"""
Facility Model - Day 1 Plain Python version.
No database yet: state lives only in the 'registry' class attribute

Here, we are demonstrating simple classes, class attributes, and class methods.
In the future, we will be using SQLAlchemy to manage our database modles.

"""

from typing import ClassVar

class Facility:
    """
    this is a class attribute that will hold all instances of Facility
    A class attribute is shared across all instances of the class, and
    can be accessed using the class name (Facility.registry) or using 
    an instance of the class (facility_instance.registry).
    While an instance attribute belongs to a specific instance of the class,
    a class attribute belongs to the class itself.
    """
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


    """
    a class method that finds the facility instance by its ID
    @classmethod annotation - indicates that this method is a class method
    which means it can be called on the class itself, not just an instance of the class
    """
    @classmethod
    def find_by_id(cls, facility_id: int) -> "Facility | None ":
        for facility in cls.registry:
            if facility.id == facility_id:
                return facility
        return None

