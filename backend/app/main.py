import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .services.database_service import db_service
from .services.redis_geo import redis_geo
from .services.rabbitmq_service import rabbitmq_service
from .services.cosmos_service import cosmos_service
from .services.cpp_spatial import cpp_spatial

from .routers import telemetry, vehicles, websocket

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [FleetSync] %(message)s")
logger = logging.getLogger("FleetSync")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Booting FleetSync Autonomous Fleet Telemetry Platform...")
    await db_service.connect()
    await redis_geo.connect()
    await rabbitmq_service.connect()
    await cosmos_service.connect()
    logger.info("FleetSync Spatial Engine is online and ready for high-frequency GPS stream ingestion.")
    yield
    logger.info("Shutting down FleetSync Platform...")
    await db_service.disconnect()
    await redis_geo.disconnect()
    await rabbitmq_service.disconnect()
    await cosmos_service.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-frequency geospatial telemetry, geofencing, and driver safety platform with C++ SIMD, Redis GEO, and RabbitMQ.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router, prefix=settings.API_V1_PREFIX)
app.include_router(vehicles.router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket.router)

@app.get("/", response_class=HTMLResponse)
async def serve_radar_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
