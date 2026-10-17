import pytest
import pytest_asyncio
from backend.app.services.cpp_spatial import cpp_spatial
from backend.app.services.database_service import db_service
from backend.app.services.redis_geo import redis_geo
from backend.app.services.rabbitmq_service import rabbitmq_service

@pytest_asyncio.fixture(autouse=True)
async def setup_services():
    await db_service.connect()
    await redis_geo.connect()
    await rabbitmq_service.connect()
    yield
    await db_service.disconnect()
    await redis_geo.disconnect()
    await rabbitmq_service.disconnect()

@pytest.fixture(autouse=True)
def reset_spatial():
    cpp_spatial.reset()
    yield
    cpp_spatial.reset()
