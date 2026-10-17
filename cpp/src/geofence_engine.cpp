#include "geofence_engine.h"
#include <cmath>
#include <chrono>
#include <atomic>
#include <cstring>
#include <algorithm>

namespace {

constexpr double EARTH_RADIUS_KM = 6371.0;
constexpr double PI = 3.14159265358979323846;

inline double deg2rad(double deg) {
    return deg * (PI / 180.0);
}

inline uint64_t get_now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()
    ).count();
}

class GeofenceEngineImpl {
private:
    std::atomic<uint64_t> total_pings_{0};
    std::atomic<uint64_t> total_breaches_{0};
    std::atomic<uint64_t> total_overspeed_{0};
    std::atomic<uint64_t> latency_sum_ns_{0};
    std::atomic<uint64_t> min_latency_ns_{UINT64_MAX};
    std::atomic<uint64_t> max_latency_ns_{0};

public:
    GeofenceEngineImpl() = default;

    void reset() {
        total_pings_ = 0;
        total_breaches_ = 0;
        total_overspeed_ = 0;
        latency_sum_ns_ = 0;
        min_latency_ns_ = UINT64_MAX;
        max_latency_ns_ = 0;
    }

    GeofenceResult evaluate(
        double vehicle_lat,
        double vehicle_lon,
        double speed_kmh,
        double speed_limit_kmh,
        double center_lat,
        double center_lon,
        double radius_km,
        const double* poly_lats,
        const double* poly_lons,
        int32_t num_vertices
    ) {
        uint64_t t0 = get_now_ns();
        total_pings_.fetch_add(1, std::memory_order_relaxed);

        GeofenceResult res;
        std::memset(&res, 0, sizeof(GeofenceResult));

        // 1. Distance & Circular geofence check
        res.distance_to_center_km = haversine_distance_km(vehicle_lat, vehicle_lon, center_lat, center_lon);
        int inside = (radius_km > 0.0) ? (res.distance_to_center_km <= radius_km ? 1 : 0) : 1;

        // 2. Polygonal geofence check (if vertices provided)
        if (num_vertices >= 3 && poly_lats && poly_lons) {
            inside = is_point_in_polygon(vehicle_lat, vehicle_lon, poly_lats, poly_lons, num_vertices);
        }

        res.is_inside_geofence = inside;
        if (!inside) {
            total_breaches_.fetch_add(1, std::memory_order_relaxed);
        }

        // 3. Speed limit violation check
        res.speed_delta_kmh = speed_kmh - speed_limit_kmh;
        if (res.speed_delta_kmh > 0.0) {
            res.is_overspeeding = 1;
            total_overspeed_.fetch_add(1, std::memory_order_relaxed);
        } else {
            res.is_overspeeding = 0;
        }

        uint64_t t1 = get_now_ns();
        res.latency_ns = t1 - t0;

        latency_sum_ns_.fetch_add(res.latency_ns, std::memory_order_relaxed);

        uint64_t cur_min = min_latency_ns_.load(std::memory_order_relaxed);
        while (res.latency_ns < cur_min &&
               !min_latency_ns_.compare_exchange_weak(cur_min, res.latency_ns, std::memory_order_relaxed)) {}

        uint64_t cur_max = max_latency_ns_.load(std::memory_order_relaxed);
        while (res.latency_ns > cur_max &&
               !max_latency_ns_.compare_exchange_weak(cur_max, res.latency_ns, std::memory_order_relaxed)) {}

        return res;
    }

    void get_metrics(SpatialMetrics* out) {
        if (!out) return;
        uint64_t tot = total_pings_.load(std::memory_order_relaxed);
        out->total_pings_evaluated = tot;
        out->total_breaches_detected = total_breaches_.load(std::memory_order_relaxed);
        out->total_overspeeding_alerts = total_overspeed_.load(std::memory_order_relaxed);
        out->avg_latency_ns = (tot > 0) ? (static_cast<double>(latency_sum_ns_.load(std::memory_order_relaxed)) / tot) : 0.0;
        uint64_t min_lat = min_latency_ns_.load(std::memory_order_relaxed);
        out->min_latency_ns = (min_lat == UINT64_MAX) ? 0 : min_lat;
        out->max_latency_ns = max_latency_ns_.load(std::memory_order_relaxed);
    }
};

} // namespace

extern "C" {

GeofenceEngineHandle create_geofence_engine() {
    return reinterpret_cast<GeofenceEngineHandle>(new GeofenceEngineImpl());
}

void destroy_geofence_engine(GeofenceEngineHandle handle) {
    if (handle) {
        delete reinterpret_cast<GeofenceEngineImpl*>(handle);
    }
}

void reset_geofence_engine(GeofenceEngineHandle handle) {
    if (handle) {
        reinterpret_cast<GeofenceEngineImpl*>(handle)->reset();
    }
}

double haversine_distance_km(double lat1, double lon1, double lat2, double lon2) {
    double dlat = deg2rad(lat2 - lat1);
    double dlon = deg2rad(lon2 - lon1);
    double rlat1 = deg2rad(lat1);
    double rlat2 = deg2rad(lat2);

    double a = std::sin(dlat / 2.0) * std::sin(dlat / 2.0) +
               std::cos(rlat1) * std::cos(rlat2) *
               std::sin(dlon / 2.0) * std::sin(dlon / 2.0);
    double c = 2.0 * std::atan2(std::sqrt(a), std::sqrt(1.0 - a));
    return EARTH_RADIUS_KM * c;
}

int32_t is_point_in_polygon(
    double lat,
    double lon,
    const double* poly_lats,
    const double* poly_lons,
    int32_t num_vertices
) {
    if (num_vertices < 3 || !poly_lats || !poly_lons) return 0;

    int inside = 0;
    for (int i = 0, j = num_vertices - 1; i < num_vertices; j = i++) {
        double yi = poly_lats[i], xi = poly_lons[i];
        double yj = poly_lats[j], xj = poly_lons[j];

        bool intersect = ((yi > lat) != (yj > lat)) &&
                         (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
    }
    return inside ? 1 : 0;
}

GeofenceResult evaluate_vehicle_telemetry(
    GeofenceEngineHandle handle,
    double vehicle_lat,
    double vehicle_lon,
    double speed_kmh,
    double speed_limit_kmh,
    double center_lat,
    double center_lon,
    double radius_km,
    const double* poly_lats,
    const double* poly_lons,
    int32_t num_vertices
) {
    if (!handle) {
        GeofenceResult err;
        std::memset(&err, 0, sizeof(GeofenceResult));
        return err;
    }
    return reinterpret_cast<GeofenceEngineImpl*>(handle)->evaluate(
        vehicle_lat, vehicle_lon, speed_kmh, speed_limit_kmh,
        center_lat, center_lon, radius_km, poly_lats, poly_lons, num_vertices
    );
}

void get_spatial_metrics(GeofenceEngineHandle handle, SpatialMetrics* out_metrics) {
    if (handle && out_metrics) {
        reinterpret_cast<GeofenceEngineImpl*>(handle)->get_metrics(out_metrics);
    }
}

}
