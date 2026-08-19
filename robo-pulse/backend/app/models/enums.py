"""
RoboPulse Command Center
Day 1 - Enumerated types shared across all domain models.

The benefit of creating these as enums is that typos (such as idlee instead of idle)
will be caught at compile time, rather than at runtime. Very important for fields that
are used as foreign keys in the database, since that can cause integrity issues.

"""

from enum import Enum

class RobotStatus(str, Enum):
    IDLE = "Idle"
    IN_MISSION = "In-Mission"
    MAINTENANCE = "Maintenance"
    OFFLINE = "Offline"

class MissionPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    CRITICAL = "Critical"

class MissionStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In-Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"

