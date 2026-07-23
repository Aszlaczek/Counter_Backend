"""
Persons Router - CRUD operations for persons whose extra hours are tracked.

All endpoints require authentication (JWT Bearer token).

Endpoints:
- GET    /api/persons       - List all persons
- POST   /api/persons       - Create a new person
- GET    /api/persons/{id}  - Get person details with hours summary
- PUT    /api/persons/{id}  - Update a person
- DELETE /api/persons/{id}  - Delete a person and their hours records
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from Models.schemas import PersonCreate, PersonUpdate, PersonResponse, PersonDetailResponse
from Models.models import AdminUser
from Services.person_service import (
    create_person,
    get_all_persons,
    get_person_by_id,
    update_person,
    delete_person,
    get_person_with_hours_summary,
)
from dependencies import get_current_admin

router = APIRouter(
    prefix="/api/persons",
    tags=["Persons"],
    responses={
        401: {"description": "Not authenticated - provide Bearer token"},
        403: {"description": "Forbidden - account inactive"},
        404: {"description": "Person not found"},
    },
)


@router.get(
    "/",
    response_model=List[PersonResponse],
    summary="List all persons",
    description="Get a list of all persons. Supports pagination and filtering by working status.",
)
def list_persons(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    is_working: Optional[bool] = Query(None, description="Filter by working status"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Retrieve all persons.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Max results (default: 100, max: 500)
    - **is_working**: Optional filter (true = currently working, false = not working)

    Requires admin authentication.
    """
    persons = get_all_persons(db, current_admin, skip=skip, limit=limit, is_working=is_working)
    return persons


@router.post(
    "/",
    response_model=PersonResponse,
    status_code=201,
    summary="Create a new person",
    description="Add a new person to be tracked for extra hours.",
)
def create_new_person(
    person_data: PersonCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Create a new person record.

    - **name**: First name (required)
    - **surname**: Last name (required)
    - **faculty**: Faculty/Department (optional, defaults to "Unknown")
    - **is_working**: Working status (optional, defaults to true)

    Requires admin authentication.
    """
    person = create_person(db, person_data, current_admin)
    return person


@router.get(
    "/{person_id}",
    response_model=PersonDetailResponse,
    summary="Get person details with hours summary",
    description="Get detailed information about a specific person, including their total extra hours.",
)
def get_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Get a person by their ID, including extra hours summary.

    - **person_id**: The ID of the person to retrieve

    Returns person details plus:
    - **total_extra_hours**: Sum of all extra hours as decimal
    - **extra_hours_count**: Total number of extra hours records

    Requires admin authentication.
    """
    return get_person_with_hours_summary(db, person_id, current_admin)


@router.put(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Update a person",
    description="Update one or more fields of a person record.",
)
def update_existing_person(
    person_id: int,
    person_update: PersonUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Update an existing person.

    - **person_id**: ID of the person to update
    - Provide only the fields you want to change (all optional)

    Requires admin authentication.
    """
    person = update_person(db, person_id, person_update, current_admin)
    return person


@router.delete(
    "/{person_id}",
    status_code=204,
    summary="Delete a person",
    description="Delete a person and all their associated extra hours records.",
)
def delete_existing_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Delete a person by ID.

    - **person_id**: ID of the person to delete

    This also deletes ALL extra hours records associated with this person.
    This action cannot be undone.

    Requires admin authentication.
    """
    delete_person(db, person_id, current_admin)
    return None

