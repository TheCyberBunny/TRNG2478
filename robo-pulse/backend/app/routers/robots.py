"""
RoboPulse Fleet Command Center
Day 4 - Robot endpoints.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import Robot, RobotStatus
from app.schemas.robot import RobotCreate, RobotRead

#our FastAPI router for the /robots endpoints. The prefix argument means that
#  all routes defined in this router will be prefixed with /robots, and the 
# tags argument is used for documentation purposes in the OpenAPI schema.
router = APIRouter(prefix="/robots", tags=["robots"])


#our GET /robots endpoint, which returns a list of robots, optionally filtered by battery level.
@router.get("", response_model=list[RobotRead])
async def list_robots(
    max_battery: Decimal | None = Query(
        default=None,
        ge=0,
        le=100,
        description="Only return robots strictly below this battery percentage.",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[Robot]:
    """
    Business Question #1: Low Battery Alert - a fourth time.
    GET /robots?max_battery=20 answers the exact same question
    Day 1's Python, Day 2's SQL, and Day 3's ORM query already
    answered - now reachable over HTTP, with the threshold supplied
    by whoever calls the API instead of hardcoded in a script.
    """
    statement = select(Robot).where(Robot.status != RobotStatus.OFFLINE)
    if max_battery is not None:
        statement = statement.where(Robot.battery_level < max_battery)
    statement = statement.order_by(Robot.id)

    result = await db.execute(statement)
    return list(result.scalars().all())

#our GET /robots/{robot_id} endpoint, which returns a single robot by ID.
@router.get("/{robot_id}", response_model=RobotRead)
async def get_robot(robot_id: int, db: AsyncSession = Depends(get_db)) -> Robot:
    robot = await db.get(Robot, robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Robot {robot_id} not found",
        )
    return robot

#our POST /robots endpoint, which creates a new robot.
@router.post("", response_model=RobotRead, status_code=status.HTTP_201_CREATED)
async def create_robot(payload: RobotCreate, db: AsyncSession = Depends(get_db)) -> Robot:
    robot = Robot(**payload.model_dump())
    db.add(robot)
    await db.commit()
    await db.refresh(robot)
    return robot

