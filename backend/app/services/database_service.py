import asyncpg
import logging
from typing import Optional, Dict, Any, List
from ..config import settings

logger = logging.getLogger("FleetSync.Database")

class DatabaseService:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=2,
                    max_size=20,
                    command_timeout=30.0
                )
                logger.info("Connected to PostgreSQL FleetSync database pool.")
            except Exception as e:
                logger.error(f"FleetSync database connection error: {e}")
                raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Closed FleetSync database pool.")

    async def get_active_vehicles(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT vehicle_id, fleet_id, license_plate, model, max_speed_kmh, status FROM vehicles")
            return [dict(r) for r in rows]

    async def get_active_geofences(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT fence_id, fleet_id, name, center_lat, center_lon, radius_km, speed_limit_kmh FROM geofences")
            return [dict(r) for r in rows]

    async def record_telemetry_ping(
        self,
        vehicle_id: str,
        lat: float,
        lon: float,
        speed: float,
        fuel: float,
        temp: float
    ):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO telemetry_pings (vehicle_id, latitude, longitude, speed_kmh, fuel_pct, engine_temp_c, recorded_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                vehicle_id, lat, lon, speed, fuel, temp
            )

    async def record_geofence_violation(
        self,
        vehicle_id: str,
        fence_id: str,
        lat: float,
        lon: float,
        violation_type: str,
        speed: float,
        latency_ns: int
    ):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO geofence_violations (vehicle_id, fence_id, latitude, longitude, violation_type, speed_kmh, latency_ns, detected_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                """,
                vehicle_id, fence_id, lat, lon, violation_type, speed, latency_ns
            )

    async def get_recent_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT violation_id, vehicle_id, fence_id, latitude, longitude, violation_type, speed_kmh, latency_ns, detected_at
                FROM geofence_violations
                ORDER BY detected_at DESC
                LIMIT $1
                """,
                limit
            )
            return [dict(r) for r in rows]

db_service = DatabaseService()
