"""
Robopulse Command Center
Day 5 - our User entity. NOTE that this is not a part of the original ERD
as shown in the problem statement document, but it is required to fulfill
the RBAC(Role-Based Access Control) section of the document. Every request from here forward needs to
know WHO is asking and WHAT role they have
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import UserRole

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    #for security reasons, we do not want to store the raw password in the database. Instead
    #we want to store a hashed version of the password
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r}, role={self.role.value})"