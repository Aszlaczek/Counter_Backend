"""
Extra Hours Router - CRUD operations for extra hours records.

All endpoints require authentication (JWT Bearer token).

Endpoints:
- GET  /api/extra-hours          - List all extra hours records
- POST /api/extra-hours          - Create a new extra hours record
- GET  /api/extra-hours/{id}     - Get a specific record
- PUT  /api/extra-hours/{id}     - Update a record
- DELETE /api/extra-hours/{id}   - Delete a record
- GET  /api/extra-hours/persons/{person_id}/summary - Person hours summary
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from Models.schemas import ExtraHoursCreate, ExtraHoursUpdate, ExtraHoursResponse
from Models.models import AdminUser
from Services.extra_hours_service import (
    create_extra_hours,
    get_extra_hours_by_id,
    get_all_extra_hours,
    update_extra_hours,
    delete_extra_hours,
    get_person_total_hours,
)
from dependencies import get_current_admin

router = APIRouter(
    prefix="/api/extra-hours",
    tags=["Extra Hours"],
    responses={
        401: {"description": "Not authenticated - provide Bearer token"},
        403: {"description": "Forbidden - account inactive"},
        404: {"description": "Record or person not found"},
    },
)


@router.get(
    "/",
    response_model=List[ExtraHoursResponse],
    summary="List all extra hours records",
    description="Get all extra hours records. Supports pagination and filtering by person.",
)
def list_extra_hours(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    person_id: Optional[int] = Query(None, description="Filter by person ID"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Retrieve all extra hours records.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Max results (default: 100, max: 500)
    - **person_id**: Optional filter to get records for a specific person

    Results are ordered by date (most recent first).

    Requires admin authentication.
    """
    records = get_all_extra_hours(db, current_admin, skip=skip, limit=limit, person_id=person_id)
    return records


@router.post(
    "/",
    response_model=ExtraHoursResponse,
    status_code=201,
    summary="Create extra hours record",
    description="Record extra hours worked by a person.",
)
def create_new_extra_hours(
    hours_data: ExtraHoursCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Create a new extra hours record.

    - **person_id**: ID of the person (required)
    - **hours**: Number of extra hours (default: 0)
    - **minutes**: Extra minutes 0-59 (default: 0)
    - **description**: Optional reason for the extra hours
    - **date**: Date in YYYY-MM-DD format (default: today)

    Requires admin authentication.
    """
    record = create_extra_hours(db, hours_data, current_admin)
    return record


@router.get(
    "/{hours_id}",
    response_model=ExtraHoursResponse,
    summary="Get extra hours record",
    description="Get a specific extra hours record by its ID.",
)
def get_extra_hours_record(
    hours_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Get a single extra hours record by ID.

    - **hours_id**: ID of the extra hours record

    Requires admin authentication.
    """
    record = get_extra_hours_by_id(db, hours_id, current_admin)
    return record


@router.put(
    "/{hours_id}",
    response_model=ExtraHoursResponse,
    summary="Update extra hours record",
    description="Update one or more fields of an extra hours record.",
)
def update_extra_hours_record(
    hours_id: int,
    hours_update: ExtraHoursUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Update an existing extra hours record.

    - **hours_id**: ID of the record to update
    - Provide only the fields you want to change (all optional)

    Requires admin authentication.
    """
    record = update_extra_hours(db, hours_id, hours_update, current_admin)
    return record


@router.delete(
    "/{hours_id}",
    status_code=204,
    summary="Delete extra hours record",
    description="Delete a specific extra hours record.",
)
def delete_extra_hours_record(
    hours_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Delete an extra hours record by ID.

    - **hours_id**: ID of the record to delete

    This action cannot be undone.

    Requires admin authentication.
    """
    delete_extra_hours(db, hours_id, current_admin)
    return None


@router.get(
    "/persons/{person_id}/summary",
    response_model=dict,
    summary="Get person's total hours summary",
    description="Get a summary of total extra hours for a specific person.",
    tags=["Extra Hours", "Persons"],
)
def get_person_hours_summary(
    person_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Get total extra hours summary for a person.

    - **person_id**: ID of the person

    Returns total hours, minutes, decimal hours, and record count.

    Requires admin authentication.
    """
    return get_person_total_hours(db, person_id, current_admin)
