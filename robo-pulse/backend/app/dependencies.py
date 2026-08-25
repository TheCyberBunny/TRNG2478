"""
RoboPulse Fleet Command Center
Day 4 - shared FastAPI dependencies.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

#this is a FastAPI dependency that provides an async database session to any route that needs it.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session