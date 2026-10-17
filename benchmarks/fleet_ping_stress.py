import asyncio
import time
import statistics
import random
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.database_service import db_service
from backend.app.services.redis_geo import redis_geo
from backend.app.services.rabbitmq_service import rabbitmq_service

TOTAL_PINGS = 2500
CONCURRENT_VEHICLES = 50

async def vehicle_worker(worker_id: int, pings_per_vehicle: int, latencies: list, breaches: list):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        valid_vehicles = ["TRUCK_01", "TRUCK_02", "VAN_01", "ROBOT_01"]
        vehicle_id = valid_vehicles[worker_id % len(valid_vehicles)]
        hub_lat = 12.9716
        hub_lon = 77.5946

        for i in range(pings_per_vehicle):
            angle = (i * 0.1) + worker_id
            dist_deg = (0.01 + (i % 15) * 0.01) # Radius in degrees
            lat = hub_lat + (dist_deg * 0.8)
            lon = hub_lon + (dist_deg * 0.8)
            speed = 45.0 + (i % 55)

            payload = {
                "vehicle_id": vehicle_id,
                "latitude": lat,
                "longitude": lon,
                "speed_kmh": speed,
                "fuel_pct": 90.0,
                "engine_temp_c": 85.0
            }

            t0 = time.perf_counter()
            try:
                res = await client.post("/api/v1/telemetry/ping", json=payload)
                t1 = time.perf_counter()
                dur_ms = (t1 - t0) * 1000.0
                latencies.append(dur_ms)
                if res.status_code == 200:
                    data = res.json()
                    if not data["is_inside_geofence"] or data["is_overspeeding"]:
                        breaches.append(1)
            except Exception:
                pass

async def run_benchmark():
    print("=====================================================================")
    print("  FLEETSYNC DISTRIBUTED GPS TELEMETRY STREAM CONCURRENT STRESS TEST   ")
    print("=====================================================================")
    print(f"[*] Target Pings       : {TOTAL_PINGS}")
    print(f"[*] Concurrent Fleets  : {CONCURRENT_VEHICLES}")
    print("[*] Connecting services (Postgres, Redis GEO, RabbitMQ, C++ Core)...")

    await db_service.connect()
    await redis_geo.connect()
    await rabbitmq_service.connect()

    latencies = []
    breaches = []
    pings_per_worker = TOTAL_PINGS // CONCURRENT_VEHICLES

    start_wall = time.perf_counter()
    tasks = [
        asyncio.create_task(vehicle_worker(w_id, pings_per_worker, latencies, breaches))
        for w_id in range(CONCURRENT_VEHICLES)
    ]
    await asyncio.gather(*tasks)
    end_wall = time.perf_counter()

    total_sec = end_wall - start_wall
    throughput = len(latencies) / total_sec

    latencies.sort()
    p50 = statistics.median(latencies)
    p90 = latencies[int(len(latencies) * 0.90)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    mean_lat = statistics.mean(latencies)

    print("\n======================= BENCHMARK RESULTS =======================")
    print(f" Total GPS Pings Ingested : {len(latencies):,}")
    print(f" Violations & Breaches    : {len(breaches):,}")
    print(f" Total Elapsed Time       : {total_sec:.3f} seconds")
    print(f" Ingestion Throughput     : {throughput:,.2f} pings/sec")
    print("-----------------------------------------------------------------")
    print(f" Mean Latency             : {mean_lat:.2f} ms")
    print(f" p50 Latency              : {p50:.2f} ms")
    print(f" p90 Latency              : {p90:.2f} ms")
    print(f" p95 Latency              : {p95:.2f} ms")
    print(f" p99 Latency              : {p99:.2f} ms")
    print("=================================================================\n")

    await db_service.disconnect()
    await redis_geo.disconnect()
    await rabbitmq_service.disconnect()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
