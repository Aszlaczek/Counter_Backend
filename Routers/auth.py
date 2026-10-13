"""
Authentication Router - handles admin registration, login, and token management.

Endpoints:
- POST /api/auth/register - Register a new admin (not protected, first-time setup)
- POST /api/auth/login   - Login and receive JWT access + refresh tokens
- POST /api/auth/refresh - Get a new access token using a refresh token (no auth required)
- GET  /api/auth/me      - Get current admin profile (protected)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from Models.schemas import AdminUserCreate, AdminUserLogin, TokenResponse, AdminUserResponse, TokenRefreshRequest
from Models.models import AdminUser
from Services.auth_service import (
    register_admin,
    authenticate_admin,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
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
    summary="Login and get access + refresh tokens",
    description="Authenticate with username and password to receive a JWT access token and a long-lived refresh token.",
)
def login(
    login_data: AdminUserLogin,
    db: Session = Depends(get_db),
):
    """
    Login with admin credentials.

    - **username**: Your admin username
    - **password**: Your password

    Returns:
    - **access_token**: Short-lived JWT (60 min) for API access
    - **refresh_token**: Long-lived JWT (30 days) for obtaining new access tokens
    """
    admin = authenticate_admin(db, login_data.username, login_data.password)
    access_token = create_access_token(admin.id)
    refresh_token = create_refresh_token(admin.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        refresh_token_expires_in_days=settings.jwt_refresh_token_expire_days,
        admin=get_admin_response(admin),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Obtain a new access token using a valid refresh token. No Bearer token required.",
)
def refresh(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Get a new access token using a refresh token.

    - **refresh_token**: The refresh token you received during login

    This endpoint allows you to obtain a new access token without re-entering
    your credentials. The refresh token itself is validated (signature, expiry, type).

    Returns new tokens. Previously issued refresh tokens remain valid until expiry.
    """
    # Verify the refresh token and extract admin ID
    admin_id = verify_refresh_token(refresh_data.refresh_token)

    # Fetch the admin from database
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()

    if not admin:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )

    if not admin.is_active:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Issue new tokens; stateless JWTs do not revoke previously issued tokens.
    new_access_token = create_access_token(admin.id)
    new_refresh_token = create_refresh_token(admin.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        refresh_token_expires_in_days=settings.jwt_refresh_token_expire_days,
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
