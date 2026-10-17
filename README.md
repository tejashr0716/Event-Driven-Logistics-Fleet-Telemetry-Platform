# FleetSync: Autonomous Event-Driven Logistics & Fleet Telemetry Tracking Platform

[![CI/CD Pipeline](https://github.com/tejashr0716/Event-Driven-Logistics-Fleet-Telemetry-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/tejashr0716/Event-Driven-Logistics-Fleet-Telemetry-Platform/actions)
[![Language: C++17](https://img.shields.io/badge/Language-C%2B%2B17-blue.svg)](https://en.cppreference.com/w/cpp/17)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5%2F4.2-E25A1C.svg)](https://spark.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D.svg)](https://redis.io/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.13-FF6600.svg)](https://www.rabbitmq.com/)

**FleetSync** is an institutional-scale, event-driven geospatial telemetry and logistics tracking engine built to monitor fleets of 10,000+ autonomous trucks, vans, and urban rovers. It pairs a **sub-microsecond C++ SIMD spatial engine** (Haversine & Jordan Curve Ray-Casting) with **Redis Geospatial indexing**, **RabbitMQ** event routing, **FastAPI WebSockets**, and **Apache Spark** driver safety anomaly profiling.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Fleets["Connected Fleet IoT Telemetry"]
        V1["Volvo Autonomous FH16 Trucks"]
        V2["Tesla Semi Express Fleet"]
        V3["Rivian EDV Urban Delivery"]
    end

    subgraph Ingestion["Ingestion & WebSocket Stream (FastAPI)"]
        API["FastAPI Telemetry Ingestion Router"]
        WS["WebSocket Radar Broadcast Hub"]
        FFI["Ctypes FFI Zero-Copy Bridge"]
    end

    subgraph SpatialCore["C++ Sub-Microsecond Geofence Engine"]
        HAV["Vectorized Haversine Distance Calculator"]
        RAY["Jordan Curve Ray-Casting Point-in-Polygon"]
        OFS["Real-Time Overspeeding Delta Evaluator"]
    end

    subgraph DistributedState["Geospatial Cache & Event Bus"]
        REDIS["Redis 7 (GEOADD, GEORADIUS & Pub/Sub)"]
        RMQ["RabbitMQ (logistics.events & geofence.alerts)"]
        COSMOS["Azure Cosmos DB / NoSQL (GPS Breadcrumbs)"]
    end

    subgraph Persistence["Storage & Analytics Grid"]
        PG["PostgreSQL / Azure SQL (Vehicles, Zones, Violations)"]
        SPARK["Apache Spark 4.2 (Fuel & Driver Safety Anomaly Job)"]
    end

    V1 & V2 & V3 -->|GPS Telemetry Pings| API
    API --> FFI
    FFI <--> SpatialCore
    API --> REDIS
    API --> WS
    API -->|If Zone Breach or Overspeed| RMQ
    RMQ --> PG
    API --> COSMOS
    PG --> SPARK
```

---

## Hardware Benchmark Results

### 1. C++ Spatial Geofencing Core (Apple Silicon / Clang -O3)
| Metric | Benchmark Result | Unit |
| :--- | :--- | :--- |
| **Spatial Throughput** | **12,075,921.41** | **Pings / Second (12.08M ops/s)** |
| **Min Latency** | **0** | **Nanoseconds** |
| **Mean Latency** | **49.60** | **Nanoseconds (0.05 µs)** |
| **p50 Median Latency** | **42** | **Nanoseconds (0.04 µs)** |
| **p90 Latency** | **83** | **Nanoseconds (0.08 µs)** |
| **p99 Tail Latency** | **84** | **Nanoseconds (0.08 µs)** |
| **p99.9 Tail Latency** | **125** | **Nanoseconds (0.12 µs)** |

### 2. End-to-End Concurrent Ingestion Load Test
- **Concurrent Vehicle Workers**: 50 parallel fleet sessions
- **Total GPS Pings Ingested**: 2,500 pings
- **Ingestion Throughput**: **833.10 pings/sec**
- **p50 Latency**: **63.00 ms** (including DB write, Redis GEOADD, and RabbitMQ dispatch)

---

## Quickstart & Local Execution

### 1. Build C++ Engine & Run Micro-Benchmark
```bash
cd cpp
make clean && make
./benchmark_runner
```

### 2. Initialize Database & Run Backend
```bash
psql -U postgres -d postgres -c "CREATE DATABASE fleetsync_db;"
psql -U postgres -d fleetsync_db -f schema.sql

pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Run Pytest Suite
```bash
python3 -m pytest backend/tests/ -v
```

### 4. Run Spark Fleet Anomaly Job
```bash
python3 spark/fleet_streaming_anomaly_job.py
```

### 5. Launch with Docker Compose
```bash
docker-compose up --build
```
