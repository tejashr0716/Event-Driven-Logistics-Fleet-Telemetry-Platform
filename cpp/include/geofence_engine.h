#ifndef GEOFENCE_ENGINE_H
#define GEOFENCE_ENGINE_H

#include <cstdint>
#include <cstddef>

#ifdef __cplusplus
extern "C" {
#endif

#pragma pack(push, 8)
typedef struct {
    int32_t  is_inside_geofence;     // 1 = inside, 0 = outside (breach)
    int32_t  is_overspeeding;        // 1 = exceeding speed limit, 0 = normal
    double   distance_to_center_km;  // Haversine distance
    double   speed_delta_kmh;        // current_speed - limit
    uint64_t latency_ns;             // Evaluation duration in nanoseconds
} GeofenceResult;

typedef struct {
    uint64_t total_pings_evaluated;
    uint64_t total_breaches_detected;
    uint64_t total_overspeeding_alerts;
    double   avg_latency_ns;
    uint64_t min_latency_ns;
    uint64_t max_latency_ns;
} SpatialMetrics;
#pragma pack(pop)

typedef void* GeofenceEngineHandle;

GeofenceEngineHandle create_geofence_engine();
void destroy_geofence_engine(GeofenceEngineHandle handle);
void reset_geofence_engine(GeofenceEngineHandle handle);

double haversine_distance_km(double lat1, double lon1, double lat2, double lon2);

int32_t is_point_in_polygon(
    double lat,
    double lon,
    const double* poly_lats,
    const double* poly_lons,
    int32_t num_vertices
);

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
);

void get_spatial_metrics(GeofenceEngineHandle handle, SpatialMetrics* out_metrics);

#ifdef __cplusplus
}
#endif

#endif // GEOFENCE_ENGINE_H
