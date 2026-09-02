"""
RoboPulse Command Center
Day 4 Answer Key - Pydantic v2 schema for the discrepancy report.

Day 5 - Phase B Answer key added
"""

from pydantic import BaseModel, ConfigDict

from app.models import MissionPriority, MissionStatus

class MissionStatusUpdate(BaseModel):
    status: MissionStatus

class MissionRead(BaseModel):
    id: int
    title: str
    priority: MissionPriority
    status: MissionStatus
    robot_id: int
    operator_id: int

    model_config = ConfigDict(from_attributes=True)


class DiscrepancyRead(BaseModel):
    mission_id: int
    title: str
    robot_facility_id: int
    operator_facility_id: int

    model_config = ConfigDict(from_attributes=True)

class ReliabilityMetric(BaseModel):
    model: str
    total_missions: int
    completed_count: int
    failed_count: int