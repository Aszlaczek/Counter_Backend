"""
Extra Hours Management API

An application for administrators to manage and track extra hours for persons.
- Admin authentication with JWT tokens
- CRUD operations for persons
- CRUD operations for extra hours records
- Every action requires authentication
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from Routers.auth import router as auth_router
from Routers.persons import router as persons_router
from Routers.extra_hours import router as extra_hours_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logging.getLogger(__name__).info("Database initialized successfully")
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description="""
    API for managing extra hours of persons.
    
    ## Authentication
    Person and extra-hours endpoints require an access token.
    Registration, login, refresh, health and API documentation are public.
    Use the **Authorize** button (top-right) to add your Bearer token after logging in.
    
    ## Flow
    1. Register an admin account via `/api/auth/register`
    2. Login via `/api/auth/login` to receive a JWT token
    3. Use the token to access all other endpoints
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Admin",
        "email": "awzorek23@gmail.com",
    },
)

# Allow configured frontend origins to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", tags=["Health"])
def root():
    """Root endpoint - API health check."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


# =============================================================================
# Include Routers
# =============================================================================

app.include_router(auth_router)
app.include_router(persons_router)
app.include_router(extra_hours_router)


# =============================================================================
# Run with: uvicorn main:app --reload
# =============================================================================

