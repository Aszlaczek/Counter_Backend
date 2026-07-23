"""
Authentication service for admin users.

Handles:
- User registration (password hashing)
- User login (password verification + JWT token generation)
- Token validation
"""
import datetime as dt
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError

from config import get_settings
from Models.models import AdminUser
from Models.schemas import AdminUserCreate, AdminUserResponse

settings = get_settings()

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Password Helpers
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT Token Helpers
# =============================================================================

def create_access_token(admin_id: int, expires_delta: Optional[int] = None) -> str:
    """
    Create a JWT access token for the given admin user.

    Args:
        admin_id: The ID of the admin user
        expires_delta: Token expiry in minutes (defaults to settings value)

    Returns:
        Encoded JWT string
    """
    if expires_delta is None:
        expires_delta = settings.jwt_access_token_expire_minutes

    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=expires_delta)

    payload = {
        "sub": admin_id,
        "exp": expire,
        "iat": dt.datetime.now(dt.timezone.utc),
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# =============================================================================
# Registration & Login
# =============================================================================

def register_admin(db: Session, admin_data: AdminUserCreate) -> AdminUser:
    """
    Register a new admin user.

    Validates:
    - Username is unique
    - Email is unique (if provided)

    Args:
        db: Database session
        admin_data: Registration data

    Returns:
        Created AdminUser object

    Raises:
        HTTPException 409: If username or email already exists
    """
    # Check if username already exists
    existing_username = db.query(AdminUser).filter(
        AdminUser.username == admin_data.username
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{admin_data.username}' is already taken",
        )

    # Check if email already exists (if provided)
    if admin_data.email:
        existing_email = db.query(AdminUser).filter(
            AdminUser.email == admin_data.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{admin_data.email}' is already registered",
            )

    # Create the admin user
    new_admin = AdminUser(
        name=admin_data.name,
        surname=admin_data.surname,
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hash_password(admin_data.password),
        is_active=True,
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin


def authenticate_admin(db: Session, username: str, password: str) -> AdminUser:
    """
    Authenticate an admin user with username and password.

    Args:
        db: Database session
        username: Admin username
        password: Plain-text password

    Returns:
        Authenticated AdminUser object

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If account is deactivated
    """
    # Find the admin by username
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if account is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact support.",
        )

    # Verify password
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

