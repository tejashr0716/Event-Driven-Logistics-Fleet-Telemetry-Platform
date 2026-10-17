from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VehiclePingRequest(BaseModel):
    vehicle_id: str = Field(..., example="TRUCK_01")
    latitude: float = Field(..., ge=-90.0, le=90.0, example=12.9716)
    longitude: float = Field(..., ge=-180.0, le=180.0, example=77.5946)
    speed_kmh: float = Field(..., ge=0.0, example=65.5)
    fuel_pct: float = Field(default=95.0, ge=0.0, le=100.0, example=95.0)
    engine_temp_c: float = Field(default=85.0, example=85.0)

class VehiclePingResponse(BaseModel):
    vehicle_id: str
    is_inside_geofence: bool
    is_overspeeding: bool
    distance_to_hub_km: float
    speed_delta_kmh: float
    latency_ns: int
    algorithm: str = "C++ SIMD Haversine & Ray Casting"
    recorded_at: datetime

class GeofenceZone(BaseModel):
    fence_id: str
    name: str
    center_lat: float
    center_lon: float
    radius_km: float
    speed_limit_kmh: float

class VehicleState(BaseModel):
    vehicle_id: str
    fleet_id: str
    license_plate: str
    model: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed_kmh: Optional[float] = None
    fuel_pct: Optional[float] = None
    status: str
