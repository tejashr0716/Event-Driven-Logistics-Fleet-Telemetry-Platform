-- FleetSync Autonomous Event-Driven Logistics & Fleet Telemetry Schema
-- PostgreSQL / Azure SQL Compatible

DROP TABLE IF EXISTS geofence_violations CASCADE;
DROP TABLE IF EXISTS telemetry_pings CASCADE;
DROP TABLE IF EXISTS geofences CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS fleets CASCADE;

CREATE TABLE fleets (
    fleet_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    operator_name VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vehicles (
    vehicle_id VARCHAR(32) PRIMARY KEY,
    fleet_id VARCHAR(32) NOT NULL REFERENCES fleets(fleet_id),
    license_plate VARCHAR(32) NOT NULL,
    model VARCHAR(64) NOT NULL,
    max_speed_kmh NUMERIC(6, 2) DEFAULT 100.0,
    status VARCHAR(16) DEFAULT 'ACTIVE'
);

CREATE TABLE geofences (
    fence_id VARCHAR(32) PRIMARY KEY,
    fleet_id VARCHAR(32) NOT NULL REFERENCES fleets(fleet_id),
    name VARCHAR(64) NOT NULL,
    center_lat NUMERIC(10, 6) NOT NULL,
    center_lon NUMERIC(10, 6) NOT NULL,
    radius_km NUMERIC(8, 2) NOT NULL,
    speed_limit_kmh NUMERIC(6, 2) DEFAULT 80.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE telemetry_pings (
    ping_id BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(32) NOT NULL REFERENCES vehicles(vehicle_id),
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    speed_kmh NUMERIC(6, 2) NOT NULL,
    fuel_pct NUMERIC(5, 2) DEFAULT 100.0,
    engine_temp_c NUMERIC(5, 2) DEFAULT 85.0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_telemetry_vehicle_time ON telemetry_pings(vehicle_id, recorded_at DESC);

CREATE TABLE geofence_violations (
    violation_id BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(32) NOT NULL REFERENCES vehicles(vehicle_id),
    fence_id VARCHAR(32) NOT NULL REFERENCES geofences(fence_id),
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    violation_type VARCHAR(32) NOT NULL, -- 'ZONE_BREACH', 'OVERSPEEDING'
    speed_kmh NUMERIC(6, 2) NOT NULL,
    latency_ns BIGINT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_violations_vehicle_time ON geofence_violations(vehicle_id, detected_at DESC);

-- Seed Sample Fleet Data
INSERT INTO fleets (fleet_id, name, operator_name)
VALUES
    ('FLEET_METRO', 'Metro Autonomous Express', 'Apex Logistics Corp')
ON CONFLICT (fleet_id) DO NOTHING;

INSERT INTO vehicles (vehicle_id, fleet_id, license_plate, model, max_speed_kmh)
VALUES
    ('TRUCK_01', 'FLEET_METRO', 'KA-01-EQ-9001', 'Volvo Autonomous FH16', 90.0),
    ('TRUCK_02', 'FLEET_METRO', 'KA-01-EQ-9002', 'Tesla Semi Autonomous', 105.0),
    ('VAN_01', 'FLEET_METRO', 'KA-01-EQ-1001', 'Rivian EDV Delivery', 80.0),
    ('ROBOT_01', 'FLEET_METRO', 'KA-01-EQ-0050', 'Nuro Urban Rover', 45.0)
ON CONFLICT (vehicle_id) DO NOTHING;

INSERT INTO geofences (fence_id, fleet_id, name, center_lat, center_lon, radius_km, speed_limit_kmh)
VALUES
    ('ZONE_METRO_CORE', 'FLEET_METRO', 'Downtown Metropolitan Zone', 12.9716, 77.5946, 12.0, 75.0),
    ('ZONE_AIRPORT_CORRIDOR', 'FLEET_METRO', 'Airport Logistics Highway', 13.1986, 77.7066, 18.0, 90.0)
ON CONFLICT (fence_id) DO NOTHING;
