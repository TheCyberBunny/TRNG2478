"""
RoboPulse Command Center
Reference implementation - Pydantic schemas for Facility-level
analytics (Business Questions #4 and #5). No Facility CRUD schemas
exist yet - this file only covers the analytical read models these
two endpoints need.
"""

from pydantic import BaseModel


class MaintenanceFlag(BaseModel):
    facility_id: int
    facility_name: str
    total_robots: int
    maintenance_count: int
    maintenance_percentage: float


class OperatorActiveMissions(BaseModel):
    operator_id: int
    operator_name: str
    active_mission_count: int


class ReportingLineResult(BaseModel):
    supervisor_id: int
    operator_count: int
    operators: list[OperatorActiveMissions]