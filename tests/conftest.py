# tests/conftest.py
"""Pytest fixtures for testing."""
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.db.models import Base

# Test database URL for integration tests (PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://boardroom_test:test_password@localhost:5433/boardroom_test"
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
