"""
Day 3 Demo Script - Robopulse Command Center

Queries the same robopulse_dev_2478 data from Day 2's seed.sql already loaded.
Nothing gets re-seeded today, this script just proves the ORM models line up with
the data that already exists.

Script to run from \backend:
    python -m scripts.day3_demo
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import Robot, RobotStatus

async def find_low_battery_robots(session, threshold: int = 20) -> list[Robot]:
    """
    Answering Business question #1: Low battery alert (3rd time answering it)
    """

    #statement object: a SQLAlchemy construct that represents a SQL SELECT statement
    statement = (
        select(Robot)
        .options(selectinload(Robot.facility))
        .where(Robot.status != RobotStatus.OFFLINE, Robot.battery_level < threshold)
        .order_by(Robot.id)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("== Full Robot Registry (via ORM)==")
        all_robots_stmt = select(Robot).options(selectinload(Robot.facility)).order_by(Robot.id)

        all_robots = await session.execute(all_robots_stmt)
        for robot in all_robots.scalars():
            print(f"{robot!r} -> facility: {robot.facility.name}")

        print("\n == Low Battery Alert (<20%) ==")
        alerts = await find_low_battery_robots(session, threshold = 20)
        if not alerts:
            print(" No Robots below threshold ")
        for robot in alerts:
            print(f" ALERT: {robot.serial_number} at {robot.battery_level}% "
                  f"(Facility : {robot.facility.name})")


if __name__ == "__main__":
    asyncio.run(main())