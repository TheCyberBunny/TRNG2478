"""
Day 1 Demo script - Robopulse Command Center
Run from backend/ with the venv active:
    python -m scripts.day1_demo
"""

from app.models import Facility, Robot, Mission, DiagnosticLog, RobotStatus, MissionPriority

def find_low_battery_robots(robots: list[Robot], threshold: int = 20) -> list[Robot]:
    """
    Business question #1: Low battery alert
    Which ACTIVE Robots are operating below the low battery threshold?
    """
    return [
        robot for robot in robots
        if robot.status != RobotStatus.OFFLINE and robot.is_low_battery(threshold)
    ]
"""
for robot in robots:
    if robot....
    return robot
"""

#create some dummy seed data for the demo, including facilities, robots, missions, and diagnostic logs
def seed_demo_data() -> None:

    Facility(1, "Houston Fabrication Plant", "US-South", capacity=40, supervisor_id=101)
    Facility(2, "Rotterdam Logistics Hub", "EU-East", capacity=25, supervisor_id=102)

    Robot(1, "RX-1001", "Sentinel-V2", battery_level=18.5, facility_id=1, status=RobotStatus.IN_MISSION)
    Robot(2, "RX-1002", "Sentinel-V2", battery_level=76.0, facility_id=1, status=RobotStatus.IDLE)
    Robot(3, "AD-2050", "SkyHawk-Drone", battery_level=9.0, facility_id=2, status=RobotStatus.IN_MISSION)
    Robot(4, "RX-1003", "Sentinel-V2", battery_level=42.0, facility_id=2, status=RobotStatus.MAINTENANCE)

    Mission(1, "Pipeline Corrosion Sweep", MissionPriority.CRITICAL, robot_id=1, operator_id=201)
    Mission(2, "Warehouse Perimeter Patrol", MissionPriority.LOW, robot_id=3, operator_id=202)

    DiagnosticLog(1, mission_id=1, file_url="s3://robopulse-diagnostics/rx1001-001.pdf", 
                  notes="Vibration sensor reading normal")

#main function to actually run our seed demo function to create the data and run our low battery check
def main() -> None:
    seed_demo_data()

    print("==Full Robot Registry==")
    for robot in Robot.registry:
        print(robot)

    print("\n== Low Battery Alert (< 20%)==")
    alerts = find_low_battery_robots(Robot.registry, threshold=20)
    if not alerts:
        print("No robots below threshold")
    for robot in alerts:
        print(f" ALERT: {robot.serial_number} at {robot.battery_level}% "
              f"(facility{robot.facility_id})")


##entry point for the script
if __name__ == "__main__":
    main()


