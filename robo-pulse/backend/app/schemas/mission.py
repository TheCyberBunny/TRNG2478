"""
RoboPulse Fleet Command Center
Day 4 Answer Key - Pydantic v2 schema for the discrepancy report.
"""

from pydantic import BaseModel, ConfigDict


class DiscrepancyRead(BaseModel):
    mission_id: int
    title: str
    robot_facility_id: int
    operator_facility_id: int

    model_config = ConfigDict(from_attributes=True)

