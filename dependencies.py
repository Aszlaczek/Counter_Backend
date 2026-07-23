"""
FastAPI dependencies for authentication and database access.

Key dependencies:
- get_db(): Provides a database session
- get_current_admin(): Validates JWT token and returns the authenticated admin user
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database import get_db
from config import get_settings
from Models.models import AdminUser

# HTTP Bearer token security scheme
# This adds an "Authorize" button in Swagger UI
security_scheme = HTTPBearer(
    auto_error=False,  # We'll handle missing token manually for optional auth
)

settings = get_settings()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """
    Dependency that validates the JWT token and returns the authenticated admin user.

    This is used to protect endpoints that require authentication.
    Every protected action (create/update/delete) must use this dependency.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 403: If admin user is inactive/deactivated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        # python-jose encodes 'sub' as a string, convert to int for DB lookup
        admin_id_str: str = payload.get("sub")

        if admin_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject found",
            )

        admin_id = int(admin_id_str)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
        )

    # Fetch admin from database
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This admin account has been deactivated. Contact support.",
        )

    return admin
