"""
Authentication service for admin users.

Handles:
- User registration (password hashing)
- User login (password verification + JWT token generation)
- Token refresh (refresh token verification + new access token)
"""
import datetime as dt
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
from sqlalchemy.exc import IntegrityError
from jose import jwt

from config import get_settings
from Models.models import AdminUser
from Models.schemas import AdminUserCreate, AdminUserResponse

settings = get_settings()

def hash_password(password: str) -> str:
    """Hash a password without silently truncating UTF-8 bytes."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("ascii"))
    except (ValueError, UnicodeError):
        return False


# =============================================================================
# JWT Token Helpers
# =============================================================================

def create_access_token(admin_id: int, expires_delta: Optional[int] = None) -> str:
    """
    Create a JWT access token for the given admin user.
    """
    if expires_delta is None:
        expires_delta = settings.jwt_access_token_expire_minutes

    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=expires_delta)

    payload = {
        "sub": str(admin_id),
        "jti": str(uuid.uuid4()),  # Unique token ID to guarantee distinct tokens
        "exp": expire,
        "iat": dt.datetime.now(dt.timezone.utc),
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(admin_id: int) -> str:
    """
    Create a refresh token for the given admin user.
    """
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": str(admin_id),
        "jti": str(uuid.uuid4()),  # Unique token ID to guarantee distinct tokens
        "exp": expire,
        "iat": dt.datetime.now(dt.timezone.utc),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_refresh_token(refresh_token: str) -> int:
    """
    Verify a refresh token and return the admin ID.
    """
    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require_exp": True, "require_sub": True},
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: provided token is not a refresh token",
            )

        admin_id_str: str = payload.get("sub")
        if admin_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token: no subject found",
            )

        admin_id = int(admin_id_str)
        if admin_id <= 0:
            raise ValueError("Invalid subject")
        return admin_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please login again.",
        )
    except (jwt.JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token. Please login again.",
        )


def change_password(user_id: int, new_password: str) -> None:
    """
    Change the password for a given admin user using email verification."""
    pass


# =============================================================================
# Registration & Login
# =============================================================================

def register_admin(db: Session, admin_data: AdminUserCreate) -> AdminUser:
    """
    Register a new admin user.
    """
    if not settings.allow_registration:
        raise HTTPException(status_code=403, detail="Admin registration is disabled")

    existing_username = db.query(AdminUser).filter(
        AdminUser.username == admin_data.username
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{admin_data.username}' is already taken",
        )

    if admin_data.email:
        existing_email = db.query(AdminUser).filter(
            AdminUser.email == admin_data.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{admin_data.email}' is already registered",
            )

    new_admin = AdminUser(
        name=admin_data.name,
        surname=admin_data.surname,
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hash_password(admin_data.password),
        is_active=True,
    )

    db.add(new_admin)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Username or email is already registered"
        ) from exc
    db.refresh(new_admin)

    return new_admin


def authenticate_admin(db: Session, username: str, password: str) -> AdminUser:
    """
    Authenticate an admin user with username and password.
    """
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact support.",
        )

    if not verify_password(password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return admin


def get_admin_response(admin: AdminUser) -> AdminUserResponse:
    """Convert an AdminUser ORM object to a safe response schema."""
    return AdminUserResponse(
        id=admin.id,
        name=admin.name,
        surname=admin.surname,
        username=admin.username,
        email=admin.email,
        is_active=admin.is_active,
        created_at=admin.created_at,
    )
