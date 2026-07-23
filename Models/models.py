"""
SQLAlchemy ORM models for the Extra Hours Management API.

Tables:
- AdminUser: Administrators who can login and manage the system
- Person: Individuals whose extra hours are tracked
- ExtraHours: Records of extra hours worked by persons
"""
import datetime as dt
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from database import Base


class AdminUser(Base):
    """
    Administrator user model.
    Only admins can authenticate and perform actions in the system.
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc))
    updated_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc), onupdate=dt.datetime.now(dt.timezone.utc))

    # Relationships
    created_persons = relationship("Person", back_populates="creator", foreign_keys="Person.created_by_id")
    extra_hours_created = relationship("ExtraHours", back_populates="created_by_admin", foreign_keys="ExtraHours.created_by_id")

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}')>"


class Person(Base):
    """
    Person model representing individuals whose extra hours are tracked.
    """
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    faculty = Column(String(200), default="Unknown")
    is_working = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc))
    updated_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc), onupdate=dt.datetime.now(dt.timezone.utc))
    edited_by_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    # Relationships
    creator = relationship("AdminUser", back_populates="created_persons", foreign_keys=[created_by_id])
    editor = relationship("AdminUser", foreign_keys=[edited_by_id])
    extra_hours = relationship("ExtraHours", back_populates="person", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name} {self.surname}')>"


class ExtraHours(Base):
    """
    Extra hours model storing additional hours worked by a person.
    Each record is linked to a person and the admin who created it.
    """
    __tablename__ = "extra_hours"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    minutes = Column(Integer, default=0)  # Extra minutes (0-59)
    hours = Column(Integer, default=0)    # Extra hours
    description = Column(Text, nullable=True)  # Optional reason for extra hours
    date = Column(DateTime, default=dt.datetime.now(dt.timezone.utc).date())  # Date when hours were worked
    created_by_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc))
    updated_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc), onupdate=dt.datetime.now(dt.timezone.utc))
    edited_by_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    # Relationships
    person = relationship("Person", back_populates="extra_hours")
    created_by_admin = relationship("AdminUser", back_populates="extra_hours_created", foreign_keys=[created_by_id])
    edited_by_admin = relationship("AdminUser", foreign_keys=[edited_by_id])

    @property
    def total_hours_decimal(self) -> float:
        """Returns total hours as a decimal (e.g., 2 hours 30 min = 2.5)"""
        return self.hours + (self.minutes / 60.0)

    def __repr__(self):
        return f"<ExtraHours(id={self.id}, person_id={self.person_id}, hours={self.hours}, minutes={self.minutes})>"

