"""
Day 3 phase b student challenge answer key

Answering business question # 2 with our ORM setup

Run this file from backend/ with .venv active:
    python -m scripts.day3_challenge
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Mission, Operator, Robot

async def find_colocation_discrepancies_orm(session: AsyncSession) -> list[Mission]:
    #answering business question #2: co-location discrepancy report (ORM Version)

    statement = (
        select(Mission)
        .join(Robot, Robot.id == Mission.robot_id)
        .join(Operator, Operator.id == Mission.operator_id)
        .where(Robot.facility_id != Operator.facility_id)
        .order_by(Mission.id)
    )

    result = await session.execute(statement)
    return list(result.scalars().all())


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("== Co-Location Discrepancy Report (Via ORM)==")
        discrepancies = await find_colocation_discrepancies_orm(session)

        if not discrepancies:
            print("No discrepancies found")

        for mission in discrepancies:
            """
            mission.robot/mission.operator here they are lazy-loaded
            this works because we are still inside of the 'async with AsyncSessionLocal'
            block, and each access below it is awaited implicitly by asyncpg's greenlet bridge
            the moment Python evaluates the attribute. Being explicit with selectinload
            is still a safer habit for anything beyond a quick script like this one.
            """
            robot = await session.get(Robot, mission.robot_id)
            operator = await session.get(Operator, mission.operator_id)
            print(f"Mission {mission.id} ({mission.title}): "
                  f"Robot at facility {robot.facility_id}, "
                  f"operator at facility {operator.facility_id}")


if __name__ == "__main__":
    asyncio.run(main())