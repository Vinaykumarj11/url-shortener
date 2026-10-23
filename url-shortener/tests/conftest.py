import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.cache import get_redis
from app.config import get_settings
from app.db import Base, engine
from app.main import app


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def client(redis_client):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_redis] = lambda: redis_client
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    get_settings.cache_clear()
