import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_vehicles_list_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/vehicles")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] >= 4
        ids = [v["vehicle_id"] for v in data["vehicles"]]
        assert "TRUCK_01" in ids

@pytest.mark.asyncio
async def test_geofences_list_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/geofences")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] >= 1
        assert data["geofences"][0]["fence_id"] == "ZONE_METRO_CORE"

@pytest.mark.asyncio
async def test_telemetry_ping_safe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ping = {
            "vehicle_id": "TRUCK_01",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "speed_kmh": 65.0,
            "fuel_pct": 94.0,
            "engine_temp_c": 84.0
        }
        res = await ac.post("/api/v1/telemetry/ping", json=ping)
        assert res.status_code == 200
        data = res.json()
        assert data["is_inside_geofence"] is True
        assert data["is_overspeeding"] is False
        assert data["distance_to_hub_km"] <= 12.0

@pytest.mark.asyncio
async def test_telemetry_ping_breach_and_alert():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Send location 30km away with overspeeding 115 km/h
        ping = {
            "vehicle_id": "TRUCK_02",
            "latitude": 13.2500,
            "longitude": 77.8000,
            "speed_kmh": 115.0,
            "fuel_pct": 82.0,
            "engine_temp_c": 92.0
        }
        res = await ac.post("/api/v1/telemetry/ping", json=ping)
        assert res.status_code == 200
        data = res.json()
        assert data["is_inside_geofence"] is False
        assert data["is_overspeeding"] is True
        assert data["speed_delta_kmh"] > 0

@pytest.mark.asyncio
async def test_serve_radar_dashboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")
        assert "FleetSync Radar" in res.text
        assert "C++ SIMD HAVERSINE" in res.text

@pytest.mark.asyncio
async def test_telemetry_metrics_and_violations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_m = await ac.get("/api/v1/telemetry/metrics")
        assert res_m.status_code == 200
        assert "engine" in res_m.json()

        res_v = await ac.get("/api/v1/telemetry/violations?limit=5")
        assert res_v.status_code == 200
        assert "violations" in res_v.json()
