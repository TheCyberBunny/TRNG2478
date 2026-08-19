"""
Mission Model - Day 1 plain python version
"""

from typing import ClassVar

from .enums import MissionPriority, MissionStatus


class Mission:
    #class variable 
    registry: ClassVar[list["Mission"]] = []

    def __init__(self, mission_id: int, title: str, priority: MissionPriority, robot_id: int,
                 operator_id: int, status: MissionStatus = MissionStatus.PENDING):
        self.id = mission_id
        self.title = title
        self.priority = priority
        self.status = status
        self.robot_id = robot_id
        self.operator_id = operator_id
        Mission.registry.append(self)

    #update the mission status to completed
    def mark_completed(self) -> None:
        self.status = MissionStatus.COMPLETED

    #update the mission status to Failed
    def mark_failed(self) -> None:
        self.status = MissionStatus.FAILED

    @classmethod
    def find_by_id(cls, mission_id: int) -> "Mission | None":
        for mission in cls.registry:
            if mission.id == mission_id:
                return mission
        return None

    def __repr__(self) -> str:
        return (f"Mission(id={self.id}, title={self.title!r}, "
                f"priority={self.priority.value}, status={self.status.value})")