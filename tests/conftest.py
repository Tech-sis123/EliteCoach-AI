import pytest
from httpx import AsyncClient, ASGITransport

# MONKEYPATCH JSONB/ARRAY BEFORE ANYTHING ELSE
from sqlalchemy import JSON, TypeDecorator, String
import sqlalchemy.dialects.postgresql as postgresql
from sqlalchemy import UUID as BaseUUID

class SQLiteJSONB(TypeDecorator):
    impl = JSON
    cache_ok = True
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSON) if dialect.name == "sqlite" else dialect.type_descriptor(postgresql.JSONB)

class SQLiteARRAY(TypeDecorator):
    impl = JSON
    cache_ok = True
    def __init__(self, item_type, **kwargs):
        super().__init__(**kwargs)
        self.item_type = item_type
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSON) if dialect.name == "sqlite" else dialect.type_descriptor(postgresql.ARRAY(self.item_type))

# Patch UUID for SQLite to handle string inputs better
class SafeSQLiteUUID(TypeDecorator):
    impl = BaseUUID
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        return dialect.type_descriptor(BaseUUID())
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        import uuid
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                return value
        return value

# Apply patches immediately
postgresql.JSONB = SQLiteJSONB
postgresql.ARRAY = SQLiteARRAY
# postgresql.UUID = SafeSQLiteUUID  # Might be too aggressive

from unittest.mock import patch
# Mock analytics track to avoid Celery/Redis overhead in tests
patch("app.services.analytics.analytics_service.track", return_value=None).start()

from app.main import app
from app.core.database import Base, engine as global_engine, AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings
from app.worker.celery_app import celery_app
import pytest_asyncio
import asyncio

# Configure Celery for testing
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
    broker_url="memory://",
    result_backend="rpc://",
    broker_connection_retry_on_startup=True
)

# Use SQLite for faster and isolated tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    # Override the get_db dependency to use TestSessionLocal
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    from app.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def token(client: AsyncClient):
    # Register and login a user to get a token
    email = "tester@example.com"
    password = "testpassword123"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User",
        "phone": "+2347012345678"
    })

    # MANUALLY VERIFY USER for tests
    from sqlalchemy import update
    from app.models.users import User
    from datetime import datetime
    async with TestSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.email == email)
            .values(email_verified_at=datetime.utcnow())
        )
        await session.commit()

    response = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    return response.json()["access_token"]
