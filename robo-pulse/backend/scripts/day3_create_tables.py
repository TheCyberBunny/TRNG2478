"""
Day 3 - this script creates every table and enum type defined by the SQLAlchemy
models, via Base.metadata.create_all through the async engine

run this from the \backend directory with .venv enabled using:
    python -m scripts.day3_create_tables
"""

import asyncio

from app.database import engine
from app.models import Base

async def create_tables() -> None:
    async with engine.begin() as conn:
        #create_all() is a special method provided by SQLAlchemy's MetaData object that
        #creates all tables defined in the metadata
        await conn.run_sync(Base.metadata.create_all)

#anytime we run our main script, we run this
if __name__ == "__main__":
    asyncio.run(create_tables())