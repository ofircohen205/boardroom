# tests/conftest.py
"""Pytest fixtures for testing."""

import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.shared.db.models import Base, User

# Test database URL for integration tests (PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://boardroom_test:test_password@localhost:5433/boardroom_test",
)


@pytest_asyncio.fixture
async def test_db_session(request):
    """
    Create database session for testing.

    - Unit tests (tests/unit/): Use SQLite in-memory for speed
    - Integration tests (tests/integration/): Use PostgreSQL for production parity

    The database type is automatically determined based on the test file location.
    """
    # Check if this is an integration test by looking at the file path
    is_integration = "integration" in request.node.nodeid

    if is_integration:
        # Use PostgreSQL for integration tests (production parity)
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
        )
    else:
        # Use SQLite for unit tests (fast, isolated)
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    """Create a test user."""
    from backend.shared.core.security import get_password_hash
    from backend.shared.db.models import User

    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("password"),
        is_active=True,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def api_client(test_user):
    """AsyncClient with auth dependency overridden to test_user."""
    from backend.main import app as fastapi_app
    from backend.shared.auth.dependencies import get_current_user

    fastapi_app.dependency_overrides[get_current_user] = lambda: test_user
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client
    fastapi_app.dependency_overrides.clear()
