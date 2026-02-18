import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_connection(test_db_session: AsyncSession):
    result = await test_db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
