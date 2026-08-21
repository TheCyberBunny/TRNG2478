"""
Facility Model - Day 3, SQLAlchemy 2.0 ORM version
same fields, same __repr__ shape and the class now also IS the db table
"""

#tells python to treat every type annotation as a string literal, allowing forward references
#to classes that are defined later in the file or in other modules
from __future__ import annotations

#Loading the TYPE_CHECKING constant from the typing modules which is used to indicate that certain
#imports are only needed for type checking and not at runtime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
#ORM = Object Relational Mapper
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .operator import Operator
    from .robot import Robot

class Facility(Base):
    #setting the table name for the facility model in the database
    __tablename__ = "facilities"

    #define our columns
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(100))
    location_region: Mapped[str] = mapped_column(String(50))
    capacity: Mapped[int] = mapped_column(Integer)
    supervisor_id: Mapped[int] = mapped_column(Integer)

    #creating our relationships with other tables
    robots: Mapped[list["Robot"]] = relationship(back_populates="facilities")
    operators: Mapped[list["Operator"]] = relationship(back_populates="facilities")

    def __repr__(self) -> str:
        return (f"Facility(id={self.id}, name={self.name!r}, "
                f"region={self.location_region!r})")












"""
Facility Model - Day 1 Plain Python version.
No database yet: state lives only in the 'registry' class attribute

Here, we are demonstrating simple classes, class attributes, and class methods.
In the future, we will be using SQLAlchemy to manage our database modles.



from typing import ClassVar

class Facility:
    
    this is a class attribute that will hold all instances of Facility
    A class attribute is shared across all instances of the class, and
    can be accessed using the class name (Facility.registry) or using 
    an instance of the class (facility_instance.registry).
    While an instance attribute belongs to a specific instance of the class,
    a class attribute belongs to the class itself.
    
    registry: ClassVar[list["Facility"]] = []

    #the constructor for the Facility class
    def __init__(self, facility_id: int, name: str, location_region: str, 
                 capacity: int, supervisor_id: int):
        self.id = facility_id
        self.name = name
        self.location_region = location_region
        self.capacity = capacity
        self.supervisor_id = supervisor_id
        Facility.registry.append(self)

    #the __repr__ method provides a string representation of the Facility instance
    #equivalent to the Java tostring method, but mostly used for debugging and logging
    def __repr__(self) -> str:
        return (f"Facility(id={self.id}, name={self.name!r}, "
                 f"region={self.location_region!r})")


    
    a class method that finds the facility instance by its ID
    @classmethod annotation - indicates that this method is a class method
    which means it can be called on the class itself, not just an instance of the class
    
    @classmethod
    def find_by_id(cls, facility_id: int) -> "Facility | None ":
        for facility in cls.registry:
            if facility.id == facility_id:
                return facility
        return None

"""