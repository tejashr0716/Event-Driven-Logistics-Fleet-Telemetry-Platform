#include "geofence_engine.h"
#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>
#include <chrono>
#include <iomanip>

int main() {
    std::cout << "=========================================================\n";
    std::cout << "  FLEETSYNC C++ HIGH-FREQUENCY SPATIAL GEOFENCING BENCHMARK \n";
    std::cout << "=========================================================\n";

    GeofenceEngineHandle engine = create_geofence_engine();

    // Define a 5-point metropolitan delivery zone polygon (e.g. San Francisco / Bangalore)
    double poly_lats[] = { 12.9200, 12.9800, 13.0400, 12.9900, 12.9100 };
    double poly_lons[] = { 77.5600, 77.5200, 77.5900, 77.6800, 77.6300 };
    int num_vertices = 5;

    double center_lat = 12.9716;
    double center_lon = 77.5946;
    double radius_km = 15.0;
    double speed_limit = 80.0;

    const int TOTAL_PINGS = 1000000;
    std::cout << "[*] Evaluating " << TOTAL_PINGS << " vehicle GPS pings against spatial boundary...\n";

    std::vector<uint64_t> latencies;
    latencies.reserve(TOTAL_PINGS);

    auto start_wall = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < TOTAL_PINGS; ++i) {
        double v_lat = 12.9000 + (i % 200) * 0.001;
        double v_lon = 77.5000 + (i % 200) * 0.001;
        double speed = 40.0 + (i % 60);

        GeofenceResult res = evaluate_vehicle_telemetry(
            engine, v_lat, v_lon, speed, speed_limit,
            center_lat, center_lon, radius_km,
            poly_lats, poly_lons, num_vertices
        );
        latencies.push_back(res.latency_ns);
    }

    auto end_wall = std::chrono::high_resolution_clock::now();
    double total_sec = std::chrono::duration<double>(end_wall - start_wall).count();
    double throughput = TOTAL_PINGS / total_sec;

    std::sort(latencies.begin(), latencies.end());

    double sum = std::accumulate(latencies.begin(), latencies.end(), 0.0);
    double avg = sum / latencies.size();
    uint64_t p50 = latencies[latencies.size() * 0.50];
    uint64_t p90 = latencies[latencies.size() * 0.90];
    uint64_t p99 = latencies[latencies.size() * 0.99];
    uint64_t p999 = latencies[latencies.size() * 0.999];
    uint64_t min_lat = latencies.front();
    uint64_t max_lat = latencies.back();

    SpatialMetrics metrics;
    get_spatial_metrics(engine, &metrics);

    std::cout << "\n================= BENCHMARK RESULTS =================\n";
    std::cout << std::fixed << std::setprecision(2);
    std::cout << " Total GPS Pings Evaluated : " << metrics.total_pings_evaluated << "\n";
    std::cout << " Geofence Breaches Alerted : " << metrics.total_breaches_detected << "\n";
    std::cout << " Overspeeding Incidents    : " << metrics.total_overspeeding_alerts << "\n";
    std::cout << " Total Time                : " << total_sec << " seconds\n";
    std::cout << " Spatial Throughput        : " << throughput << " pings/sec (" << (throughput / 1e6) << " M ops/s)\n";
    std::cout << "-----------------------------------------------------\n";
    std::cout << " Min Latency               : " << min_lat << " ns (" << (min_lat / 1000.0) << " µs)\n";
    std::cout << " Mean Latency              : " << avg << " ns (" << (avg / 1000.0) << " µs)\n";
    std::cout << " p50 Latency               : " << p50 << " ns (" << (p50 / 1000.0) << " µs)\n";
    std::cout << " p90 Latency               : " << p90 << " ns (" << (p90 / 1000.0) << " µs)\n";
    std::cout << " p99 Latency               : " << p99 << " ns (" << (p99 / 1000.0) << " µs)\n";
    std::cout << " p99.9 Latency             : " << p999 << " ns (" << (p999 / 1000.0) << " µs)\n";
    std::cout << " Max Latency               : " << max_lat << " ns (" << (max_lat / 1000.0) << " µs)\n";
    std::cout << "=====================================================\n";

    destroy_geofence_engine(engine);
    return 0;
}
