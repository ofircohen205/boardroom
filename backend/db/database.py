# backend/db/database.py
"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.settings import settings

# Create async engine
engine = create_async_engine(settings.database_url, echo=False)

# Create session maker
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: Database session that auto-commits on exit
    """
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Initialize database by creating all tables."""
    from backend.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
