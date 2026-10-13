"""
Pydantic schemas for request validation and response serialization.
"""
import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# =============================================================================
# Admin User Schemas
# =============================================================================

class AdminUserCreate(BaseModel):
    """Schema for registering a new admin user."""
    name: str = Field(..., min_length=1, max_length=100, description="First name")
    surname: str = Field(..., min_length=1, max_length=100, description="Last name")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: Optional[EmailStr] = Field(None, description="Optional email address")
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="Password (6-72 characters — bcrypt has a 72-byte limit)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class AdminUserLogin(BaseModel):
    """Schema for admin login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class AdminUserResponse(BaseModel):
    """Schema for returning admin user data (safe, no password)."""
    id: int
    name: str
    surname: str
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for JWT token response.

    Includes both access_token (short-lived, 60 min) and
    refresh_token (long-lived, 30 days) for secure token renewal.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    refresh_token_expires_in_days: int = 30
    admin: AdminUserResponse


class TokenRefreshRequest(BaseModel):
    """Schema for refreshing a token using a refresh token."""
    refresh_token: str = Field(..., description="The refresh token received during login")


# =============================================================================
# Person Schemas
# =============================================================================

class PersonCreate(BaseModel):
    """Schema for creating a new person."""
    name: str = Field(..., min_length=1, max_length=100, description="First name")
    surname: str = Field(..., min_length=1, max_length=100, description="Last name")
    faculty: Optional[str] = Field("Unknown", max_length=200, description="Faculty/Department")
    is_working: Optional[bool] = Field(True, description="Whether the person is currently working")


class PersonUpdate(BaseModel):
    """Schema for updating an existing person. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    faculty: Optional[str] = Field(None, max_length=200)
    is_working: Optional[bool] = None

    @field_validator("name", "surname", "faculty", "is_working")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Omit this field instead of sending null")
        return value


class PersonResponse(BaseModel):
    """Schema for returning person data."""
    id: int
    name: str
    surname: str
    faculty: str
    is_working: bool
    created_by_id: int
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class PersonDetailResponse(PersonResponse):
    """Extended person response that includes extra hours summary."""
    total_extra_hours: float = 0.0  # Decimal hours (e.g., 2.5 = 2h30m)
    extra_hours_count: int = 0


# =============================================================================
# Extra Hours Schemas
# =============================================================================

class ExtraHoursCreate(BaseModel):
    """Schema for creating extra hours record."""
    person_id: int = Field(..., gt=0, description="ID of the person")
    hours: int = Field(0, ge=0, description="Number of extra hours")
    minutes: int = Field(0, ge=0, le=59, description="Extra minutes (0-59)")
    description: Optional[str] = Field(None, max_length=500, description="Reason for extra hours")
    date: Optional[str] = Field(None, description="Date (YYYY-MM-DD), defaults to today")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                dt.datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date must be in YYYY-MM-DD format")
        return v


class ExtraHoursUpdate(BaseModel):
    """Schema for updating extra hours record. All fields optional."""
    hours: Optional[int] = Field(None, ge=0)
    minutes: Optional[int] = Field(None, ge=0, le=59)
    description: Optional[str] = Field(None, max_length=500)
    date: Optional[str] = Field(None, description="Date (YYYY-MM-DD)")

    @field_validator("hours", "minutes", "date")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Omit this field instead of sending null")
        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                dt.datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date must be in YYYY-MM-DD format")
        return v


class ExtraHoursResponse(BaseModel):
    """Schema for returning extra hours data."""
    id: int
    person_id: int
    hours: int
    minutes: int
    description: Optional[str] = None
    date: dt.date
    created_by_id: int
    created_at: dt.datetime
    updated_at: dt.datetime
    edited_by_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
