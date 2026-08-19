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

        """
        In-class question answered:
        The above methods follow the Domain-Driven Design(DDD) architecture.
        In a future iteration, we may have wanted to have additional functionality happen when the status
        is updated to certain values. For example, checking that a mission status != Failed and then updating to
        completed may not be a valid change.
        Below is a generic parameterized approach:
        
        def update_status(self, new_status: MissionStatus) -> None:
            #need to check that the provided value is a valid status against the enum
            if not isinstance(new_status, MissionStatus):
                raise TypeError(f"Expected MissionStatus enum, got {type(new_status).__name__}")

            #if the current and new status is the same, do nothing    
            if self.status == new_status:
                return
            
            self.status == new_status
        """




    @classmethod
    def find_by_id(cls, mission_id: int) -> "Mission | None":
        for mission in cls.registry:
            if mission.id == mission_id:
                return mission
        return None

    def __repr__(self) -> str:
        return (f"Mission(id={self.id}, title={self.title!r}, "
                f"priority={self.priority.value}, status={self.status.value})")