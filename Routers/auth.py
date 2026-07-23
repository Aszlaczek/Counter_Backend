"""
Authentication Router - handles admin registration, login, and token management.

Endpoints:
- POST /api/auth/register - Register a new admin (not protected, first-time setup)
- POST /api/auth/login   - Login and receive JWT token
- GET  /api/auth/me      - Get current admin profile (protected)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from Models.schemas import AdminUserCreate, AdminUserLogin, TokenResponse, AdminUserResponse
from Models.models import AdminUser
from Services.auth_service import (
    register_admin,
    authenticate_admin,
    create_access_token,
    get_admin_response,
)
from dependencies import get_current_admin
from config import get_settings

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
)

settings = get_settings()


@router.post(
    "/register",
    response_model=AdminUserResponse,
    status_code=201,
    summary="Register a new admin user",
    description="Create a new administrator account. Note: In production, restrict this endpoint.",
)
def register(
    admin_data: AdminUserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new administrator.

    - **name**: First name (required)
    - **surname**: Last name (required)
    - **username**: Unique username (required)
    - **email**: Optional email address
    - **password**: Password (min 6 characters)

    Returns the created admin profile (without password).
    """
    new_admin = register_admin(db, admin_data)
    return get_admin_response(new_admin)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
    description="Authenticate with username and password to receive a JWT access token.",
)
def login(
    login_data: AdminUserLogin,
    db: Session = Depends(get_db),
):
    """
    Login with admin credentials.

    - **username**: Your admin username
    - **password**: Your password

    Returns a JWT access token that must be sent as a Bearer token in subsequent requests.
    """
    admin = authenticate_admin(db, login_data.username, login_data.password)
    token = create_access_token(admin.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        admin=get_admin_response(admin),
    )


@router.get(
    "/me",
    response_model=AdminUserResponse,
    summary="Get current admin profile",
    description="Returns the profile of the currently authenticated admin.",
)
def get_me(
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Get the profile of the currently logged-in admin.

    Requires a valid Bearer token in the Authorization header.
    """
    return get_admin_response(current_admin)

