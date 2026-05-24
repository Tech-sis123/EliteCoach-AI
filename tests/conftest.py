import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine as global_engine, AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
import pytest_asyncio
import asyncio

# Create a test engine with NullPool to avoid loop issues
test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

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
    
    response = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    return response.json()["access_token"]
