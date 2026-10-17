import pytest
from backend.app.services.cpp_spatial import cpp_spatial

def test_haversine_distance_accuracy():
    # Bangalore Hub (12.9716, 77.5946) to Airport (13.1986, 77.7066)
    dist = cpp_spatial.calculate_distance_km(12.9716, 77.5946, 13.1986, 77.7066)
    assert dist == pytest.approx(28.00, 0.5)

def test_spatial_geofence_safe_evaluation():
    # Point located 5km away from hub, within 12km zone, at 60 km/h (limit 80)
    res = cpp_spatial.evaluate_telemetry(
        v_lat=12.9716,
        v_lon=77.6346,
        speed_kmh=60.0,
        speed_limit_kmh=80.0,
        center_lat=12.9716,
        center_lon=77.5946,
        radius_km=12.0
    )
    assert res["is_inside_geofence"] is True
    assert res["is_overspeeding"] is False
    assert res["distance_to_hub_km"] <= 12.0
    assert res["latency_ns"] < 10000 # Under 10 microseconds

def test_spatial_geofence_breach_detection():
    # Point located 28km away from hub (outside 12km zone)
    res = cpp_spatial.evaluate_telemetry(
        v_lat=13.1986,
        v_lon=77.7066,
        speed_kmh=70.0,
        speed_limit_kmh=80.0,
        center_lat=12.9716,
        center_lon=77.5946,
        radius_km=12.0
    )
    assert res["is_inside_geofence"] is False
    assert res["distance_to_hub_km"] > 12.0

def test_spatial_overspeeding_detection():
    # Point inside zone, but travelling at 110 km/h (limit 80)
    res = cpp_spatial.evaluate_telemetry(
        v_lat=12.9716,
        v_lon=77.5946,
        speed_kmh=110.0,
        speed_limit_kmh=80.0,
        center_lat=12.9716,
        center_lon=77.5946,
        radius_km=12.0
    )
    assert res["is_inside_geofence"] is True
    assert res["is_overspeeding"] is True
    assert res["speed_delta_kmh"] == 30.0
