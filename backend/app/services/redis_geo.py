import json
import logging
import redis.asyncio as aioredis
from typing import Optional, Dict, Any, List
from ..config import settings

logger = logging.getLogger("FleetSync.Redis")

class RedisGeospatialService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        if not self.redis:
            try:
                self.redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    max_connections=20
                )
                await self.redis.ping()
                logger.info("Connected to Redis Geospatial index pool successfully.")
            except Exception as e:
                logger.warning(f"Redis connection warning: {e}. Running with memory fallback.")
                self.redis = None

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def update_vehicle_position(
        self,
        vehicle_id: str,
        longitude: float,
        latitude: float,
        speed_kmh: float,
        fuel_pct: float
    ):
        if not self.redis:
            return

        try:
            pipe = self.redis.pipeline()
            # Redis GEOADD takes (name, [longitude, latitude, member])
            pipe.geoadd("fleet:positions", (longitude, latitude, vehicle_id))
            pipe.hset(f"vehicle:{vehicle_id}", mapping={
                "vehicle_id": vehicle_id,
                "lon": str(longitude),
                "lat": str(latitude),
                "speed": str(speed_kmh),
                "fuel": str(fuel_pct)
            })
            
            payload = json.dumps({
                "vehicle_id": vehicle_id,
                "lon": longitude,
                "lat": latitude,
                "speed": speed_kmh,
                "fuel": fuel_pct
            })
            pipe.publish("fleet:locations", payload)
            await pipe.execute()
        except Exception as e:
            logger.error(f"Error updating Redis GEO position: {e}")

    async def find_vehicles_nearby(
        self,
        longitude: float,
        latitude: float,
        radius_km: float = 10.0
    ) -> List[Dict[str, Any]]:
        if not self.redis:
            return []

        try:
            # geosearch with radius
            results = await self.redis.geosearch(
                "fleet:positions",
                longitude=longitude,
                latitude=latitude,
                radius=radius_km,
                unit="km",
                withdist=True,
                withcoord=True
            )
            nearby = []
            for item in results:
                vid = item[0]
                dist = item[1]
                coord = item[2]
                nearby.append({
                    "vehicle_id": vid,
                    "distance_km": round(dist, 2),
                    "longitude": coord[0],
                    "latitude": coord[1]
                })
            return nearby
        except Exception as e:
            logger.error(f"Error querying Redis nearby vehicles: {e}")
            return []

redis_geo = RedisGeospatialService()
