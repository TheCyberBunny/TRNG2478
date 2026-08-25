"""
Robopulse Command Center
Day 5 - seeds one demo user per RBAC role, bypassing POST /auth/register entirely
(which requires the fleet_admin role to call it)

Run from the /backend directory with .venv active:
    python -m scripts.day5_seed_users
"""

import asyncio

from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.security import hash_password

async def seed_users() -> None:
    async with AsyncSessionLocal() as session:
        session.add_all([
            User(username="admin", hashed_password=hash_password("AdminPass123!"), role=UserRole.FLEET_ADMIN),
            User(username="operator", hashed_password=hash_password("OperatorPass123!"), role=UserRole.FIELD_OPERATOR),
            User(username="auditor", hashed_password=hash_password("AuditorPass123!"), role=UserRole.AUDITOR),
        ])
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_users())
