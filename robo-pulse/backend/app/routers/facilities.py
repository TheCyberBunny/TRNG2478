"""
RoboPulse Command Center
Reference implementation - Business Questions #4 and #5. No router
for the Facility resource existed before this; both questions are
Facility-level aggregations, so they share one new router.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models import Facility, Mission, MissionStatus, Operator, Robot, RobotStatus, User
from app.schemas.facility import MaintenanceFlag, OperatorActiveMissions, ReportingLineResult

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("/maintenance-flags", response_model=list[MaintenanceFlag])
async def maintenance_flags(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Business Question #4: Maintenance Flags.

    WHERE filters rows BEFORE they're grouped/aggregated; this
    question needs to filter on a value that only exists AFTER
    aggregation (a computed percentage per facility) - that's exactly
    what HAVING is for, and it's the first HAVING clause anywhere in
    this project.
    """
    maintenance_count = func.sum(case((Robot.status == RobotStatus.MAINTENANCE, 1), else_=0))
    total_robots = func.count(Robot.id)
    maintenance_pct = maintenance_count * 100.0 / total_robots

    statement = (
        select(
            Facility.id.label("facility_id"),
            Facility.name.label("facility_name"),
            total_robots.label("total_robots"),
            maintenance_count.label("maintenance_count"),
            maintenance_pct.label("maintenance_percentage"),
        )
        .join(Robot, Robot.facility_id == Facility.id)
        .group_by(Facility.id, Facility.name)
        .having(maintenance_pct > 30)
        .order_by(Facility.id)
    )
    result = await db.execute(statement)
    return [dict(row) for row in result.mappings().all()]


@router.get("/reporting-lines", response_model=ReportingLineResult)
async def reporting_lines(
    supervisor_id: int = Query(..., description="Regional Supervisor's ID (Facility.supervisor_id)."),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Business Question #5: Reporting Lines.

    "Active" mirrors the same definition used everywhere else in this
    project: not yet Completed or Failed - i.e. Pending or
    In-Progress. supervisor_id is deliberately a query parameter, not
    a path parameter tied to a real resource - Day 2's schema.sql
    never modeled supervisors/employees as their own table, so
    supervisor_id is just a plain integer on Facility with nothing to
    look up by ID.
    """
    statement = (
        select(
            Operator.id.label("operator_id"),
            Operator.name.label("operator_name"),
            func.count(Mission.id).label("active_mission_count"),
        )
        .join(Facility, Facility.id == Operator.facility_id)
        .join(Mission, Mission.operator_id == Operator.id)
        .where(
            Facility.supervisor_id == supervisor_id,
            Mission.status.in_([MissionStatus.PENDING, MissionStatus.IN_PROGRESS]),
        )
        .group_by(Operator.id, Operator.name)
        .order_by(Operator.id)
    )
    result = await db.execute(statement)
    operators = [OperatorActiveMissions(**row) for row in result.mappings().all()]

    return ReportingLineResult(
        supervisor_id=supervisor_id,
        operator_count=len(operators),
        operators=operators,
    )