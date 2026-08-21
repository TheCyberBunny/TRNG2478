"""
Diagnostic Log Model - Day 3 SQLALchemy ORM version
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .mission import Mission

class DiagnosticLoc(Base):
    __tablename__ = "diagnostic_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(Integer, ForeignKey("missions.id"))
    file_url: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    #server_default=func.now() sets the default value of the created_at column
    #to the current timestamp when a new record is inserted into the database

    mission: Mapped["Mission"] = relationship(back_populates="diagnostic_logs")

    def __repr__(self) -> str:
        return (f"DiagnosticLog(id={self.id}, mission_id={self.mission_id}, "
                f"file_url={self.file_url!r})")



"""
Diagnostic log model - day 1 plain python version


from datetime import datetime
from typing import ClassVar

class DiagnosticLog:
    registry: ClassVar[list["DiagnosticLog"]] = []

    def __init__(self, log_id: int, mission_id: int, file_url: str,
                 notes: str | None = None,
                 #first None is atype hint, second is for the default value
                 created_at: datetime | None = None):
        self.id = log_id
        self.mission_id = mission_id
        self.file_url = file_url
        self.notes = notes
        #Optional[datetime]
        self.created_at = created_at or datetime.now()
        DiagnosticLog.registry.append(self)

    def __repr__(self) -> str:
        return (f"DiagnosticLog(id={self.id}, mission_id={self.mission_id}, "
                f"file_url={self.file_url!r})")
    
"""