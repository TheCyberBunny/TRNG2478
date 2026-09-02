"""
RoboPulse Command Center
Day 4 Answer Key - Mission endpoints.

Day 5 - Phase B challenge answer key
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, case, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models import Mission, MissionPriority, Operator, Robot, MissionStatus, User, UserRole
from app.schemas.mission import DiscrepancyRead, MissionRead, MissionStatusUpdate, ReliabilityMetric

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("/discrepancies", response_model=list[DiscrepancyRead])
async def list_colocation_discrepancies(
    priority: MissionPriority | None = Query(
        default=None,
        description="Only return discrepancies for missions of this priority.",
    ),
    db: AsyncSession = Depends(get_db),
    ##Day 5 code here
    _: User = Depends(require_role(UserRole.FLEET_ADMIN, UserRole.FIELD_OPERATOR)),
):
    """
    Business Question #2: Co-Location Discrepancy - a fourth time.
    Day 1: Python. Day 2: raw SQL. Day 3: async ORM script. Today:
    the same three-table JOIN, reachable at
    GET /missions/discrepancies, with an optional priority filter.

    Selects only the four columns the response actually needs,
    rather than full Mission/Robot/Operator objects, to reduce 
    the amount of data sent over the wire.
    """
    statement = (
        select(
            Mission.id.label("mission_id"),
            Mission.title,
            Robot.facility_id.label("robot_facility_id"),
            Operator.facility_id.label("operator_facility_id"),
        )
        .join(Robot, Robot.id == Mission.robot_id)
        .join(Operator, Operator.id == Mission.operator_id)
        .where(Robot.facility_id != Operator.facility_id)
    )

    #if a priority filter was provided, add it to the WHERE clause
    if priority is not None:
        statement = statement.where(Mission.priority == priority)

    statement = statement.order_by(Mission.id)

    result = await db.execute(statement)
    return [dict(row) for row in result.mappings().all()]


##Day 5 - Phase B Answer Key
@router.patch("/{mission_id}/status", response_model=MissionRead)
async def update_mission_status(
    mission_id: int,
    payload: MissionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.FLEET_ADMIN, UserRole.FIELD_OPERATOR)),
) -> Mission:
    mission = await db.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission '{mission_id}' not found",
        )
    if payload.status == MissionStatus.COMPLETED:
        mission.mark_completed()
    elif payload.status == MissionStatus.FAILED:
        mission.mark_failed()
    else:
        mission.status = payload.status

    await db.commit()
    await db.refresh(mission)
    return mission


@router.get("/reliability", response_model=list[ReliabilityMetric])
async def reliability_metrics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Business Question #3: Reliability Metrics.
    Any authenticated role can view this - it's an analytics endpoint,
    matching the problem statement's "Auditor can view analytics
    dashboards" requirement, same as /missions/discrepancies.
    """
    statement = (
        select(
            Robot.model,
            func.count(Mission.id).label("total_missions"),
            func.sum(case((Mission.status == MissionStatus.COMPLETED, 1), else_=0)).label("completed_count"),
            func.sum(case((Mission.status == MissionStatus.FAILED, 1), else_=0)).label("failed_count"),
        )
        .join(Mission, Mission.robot_id == Robot.id)
        .group_by(Robot.model)
        .order_by(Robot.model)
    )
    result = await db.execute(statement)
    return [dict(row) for row in result.mappings().all()]