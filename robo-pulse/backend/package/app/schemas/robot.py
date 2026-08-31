"""
RoboPulse Fleet Command Center
Day 4 - Pydantic v2 schemas for the Robot resource.

Deliberately separate from app.models.Robot (the SQLAlchemy ORM
class) - because the ORM class is tied to the database, while these schemas
are tied to the API. This separation of concerns makes it easier to 
evolve the API independently of the database schema, and vice versa.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import RobotStatus


class RobotBase(BaseModel):
    serial_number: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=100)
    #the database enforces that battery_level is between 0 and 100, 
    #but we can also enforce this at the API level using Pydantic's Field() function.
    battery_level: Decimal = Field(ge=0, le=100)
    facility_id: int
    status: RobotStatus = RobotStatus.IDLE


class RobotCreate(RobotBase):
    """Shape of the request body for POST /robots."""


class RobotRead(RobotBase):
    """Shape of a Robot in any API response."""

    id: int

    #this tells pydantic that the schema should be populated 
    #from the attributes of the ORM model, rather than from a dictionary.
    model_config = ConfigDict(from_attributes=True)

