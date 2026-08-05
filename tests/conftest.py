import os

os.environ.update(
    {
        "Secret_key": "test-secret-key-for-testing-only-32chars!",
        "Groq_api_key": "gsk_test_not_real_key",
        "gemini_key": "test-gemini-key-not-real",
        "database_url": "sqlite+aiosqlite://",
        "mail_password": "test-mail-password",
        "s3_bucket_name": "test-bucket",
        "s3_region": "us-east-1",
        "langfuse_secret_key": "sk-lf-test-not-real",
        "langfuse_public_key": "pk-lf-test-not-real",
        "langfuse_base_url": "http://localhost:3000",
        "OTEL_Exporter_OTLP_Endpoint": "http://localhost:4318",
        "OTEL_Exporter_OTLP_Headers": "Authorization=test-token",
    }
)

import pytest_asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from db import Base, get_db
from main import app
import redis_config


test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


def _make_mock_redis() -> AsyncMock:
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.aclose.return_value = None
    return mock


@pytest_asyncio.fixture(autouse=True)
async def _setup_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def mock_redis():
    mock = _make_mock_redis()
    redis_config.redis_client = mock
    yield mock
    redis_config.redis_client = None


@pytest_asyncio.fixture()
async def client(mock_redis):
    with patch("main.aioredis.Redis", return_value=mock_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def registered_user(client: AsyncClient) -> dict:
    creds = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!",
    }
    resp = await client.post("/users/register", json=creds)
    assert resp.status_code == 201, resp.text
    return creds


@pytest_asyncio.fixture()
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    resp = await client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def test_project(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/projects",
        json={"name": "TestProject", "description": "Integration test project"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
