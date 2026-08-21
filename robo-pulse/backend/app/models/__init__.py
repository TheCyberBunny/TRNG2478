"""
Package Init - lets us write:
    from app.models import Robot, Facility
Instead of:
    from app.models.robot import Robot
    from app.models.facility import Facility

"""
from .enums import RobotStatus, MissionPriority, MissionStatus
from .facility import Facility
from .robot import Robot
from .mission import Mission
from .diagnostic_log import DiagnosticLog
from .operator import Operator
from .base import Base

#this declares the list of public objects of that modules, as interpreted by import *
#similar to Java's public/private access modifiers, this is a way to control what is exposed to other packages
__all__ = [
    "Base",
    "RobotStatus", "MissionPriority", "MissionStatus",
    "Facility", "Robot", "Mission", "DiagnosticLog",
    "Operator"
]
