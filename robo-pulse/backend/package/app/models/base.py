"""
Robopulse Command Center - Day 3
Shared declarative base for every ORM model to inherit from

"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
