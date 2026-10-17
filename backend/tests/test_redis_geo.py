import pytest
from backend.app.services.redis_geo import redis_geo

@pytest.mark.asyncio
async def test_redis_geo_add_and_search_nearby():
    # Add two vehicles: one at hub (0km away), one at 5km away
    await redis_geo.update_vehicle_position(
        vehicle_id="GEO_TEST_TRUCK_1",
        longitude=77.5946,
        latitude=12.9716,
        speed_kmh=60.0,
        fuel_pct=90.0
    )

    await redis_geo.update_vehicle_position(
        vehicle_id="GEO_TEST_TRUCK_2",
        longitude=77.6346,
        latitude=12.9716,
        speed_kmh=55.0,
        fuel_pct=85.0
    )

    # Query vehicles within 10km radius of hub
    nearby = await redis_geo.find_vehicles_nearby(
        longitude=77.5946,
        latitude=12.9716,
        radius_km=10.0
    )

    vehicle_ids = [v["vehicle_id"] for v in nearby]
    assert "GEO_TEST_TRUCK_1" in vehicle_ids
    assert "GEO_TEST_TRUCK_2" in vehicle_ids
