"""
Robot Model - Day 1 plain-python version

"""

from typing import ClassVar

from .enums import RobotStatus


class Robot:
    registry: ClassVar[list["Robot"]] = []

    #a class attribute that represents when a robot's battery level is considered 'low'
    LOW_BATTERY_THRESHOLD: ClassVar[int] = 20

    #constructor
    def __init__(self, robot_id: int, serial_number: str, model: str,
                 battery_level: float, facility_id: int,
                 status: RobotStatus = RobotStatus.IDLE):
        self.id = robot_id
        self.serial_number = serial_number
        self.model = model
        self.status = status
        self.facility_id = facility_id
        self.battery_level = self._validate_battery(battery_level)
        Robot.registry.append(self)

    """
    a static method that validates the battery level of a robot
    the @staticmethod annotation just indicates that it is a static method,
    meaning it can be called on the class itself, rather than just the instance of a class
    """
    @staticmethod
    def _validate_battery(level: float) -> float:
        if level < 0:
            print(f"Warning: battery_level {level} below 0, clamping to 0")
            return 0.0
        if level > 100:
            print(f"Warning: battery_level {level} above 100, clamping to 100")
            return 100.0

        return float(level)

    #A method to check if the robot's battery level is below a certain threshold
    #if no threshold is provided, it uses the class attribute LOW_BATTERY_THRESHOLD value
    def is_low_battery(self, threshold: int | None = None ) -> bool:
        limit = threshold if threshold is not None else Robot.LOW_BATTERY_THRESHOLD
        return self.battery_level < limit

    #a method to check if a robot's status is set to maintenance
    def needs_maintenance(self) -> bool:
        return self.status == RobotStatus.MAINTENANCE

    #A class method to return robot by id
    @classmethod
    def find_by_id(cls, robot_id: int) -> "Robot | None ":
        for robot in cls.registry:
            if robot.id == robot_id:
                return robot
        return None

    #tostring
    def __repr__(self) -> str:
        return (f"Robot(serial={self.serial_number!r}, model={self.model!r}, "
                f"Battery={self.battery_level}%, status={self.status.value})")