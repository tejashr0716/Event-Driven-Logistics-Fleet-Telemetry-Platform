import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FleetSync - Autonomous Event-Driven Logistics & Fleet Telemetry Platform"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('USER', 'postgres')}@localhost:5432/fleetsync_db"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/2")

    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    RABBITMQ_EXCHANGE_LOGISTICS: str = "logistics.events"
    RABBITMQ_QUEUE_GEOFENCE: str = "geofence.alerts"

    COSMOS_ENDPOINT: str = os.getenv("COSMOS_ENDPOINT", "")
    COSMOS_KEY: str = os.getenv("COSMOS_KEY", "")

    CPP_LIB_PATH: str = os.getenv(
        "CPP_LIB_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../cpp/libgeofence_engine.dylib"))
    )

    class Config:
        env_file = ".env"

settings = Settings()
