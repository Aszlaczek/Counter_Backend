"""
Service layer for Extra Hours CRUD operations.

All functions require an authenticated admin user.
"""
import datetime as dt
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from Models.models import ExtraHours, Person, AdminUser
from Models.schemas import ExtraHoursCreate, ExtraHoursUpdate, ExtraHoursResponse


def create_extra_hours(
    db: Session,
    hours_data: ExtraHoursCreate,
    current_admin: AdminUser,
) -> ExtraHours:
    """
    Create a new extra hours record for a person.

    Args:
        db: Database session
        hours_data: Extra hours creation data
        current_admin: Authenticated admin creating this record

    Returns:
        Created ExtraHours object

    Raises:
        HTTPException 404: If person not found
    """
    # Verify the person exists
    person = db.query(Person).filter(Person.id == hours_data.person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {hours_data.person_id} not found",
        )

    # Parse date (default to today)
    if hours_data.date:
        record_date = dt.datetime.strptime(hours_data.date, "%Y-%m-%d").date()
    else:
        record_date = dt.datetime.now(dt.timezone.utc).date()

    # Create the record
    extra_hours = ExtraHours(
        person_id=hours_data.person_id,
        hours=hours_data.hours or 0,
        minutes=hours_data.minutes or 0,
        description=hours_data.description,
        date=record_date,
        created_by_id=current_admin.id,
    )

    db.add(extra_hours)
    db.commit()
    db.refresh(extra_hours)

    return extra_hours


def get_extra_hours_by_id(
    db: Session,
    hours_id: int,
    current_admin: AdminUser,
) -> ExtraHours:
    """
    Get a single extra hours record by ID.

    Args:
        db: Database session
        hours_id: ID of the extra hours record
        current_admin: Authenticated admin

    Returns:
        ExtraHours object

    Raises:
        HTTPException 404: If record not found
    """
    record = db.query(ExtraHours).filter(ExtraHours.id == hours_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extra hours record with ID {hours_id} not found",
        )

    return record


def get_all_extra_hours(
    db: Session,
    current_admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
    person_id: Optional[int] = None,
) -> List[ExtraHours]:
    """
    Get all extra hours records, with optional filtering by person.

    Args:
        db: Database session
        current_admin: Authenticated admin
        skip: Number of records to skip
        limit: Maximum records to return
        person_id: Optional filter by person ID

    Returns:
        List of ExtraHours objects
    """
    query = db.query(ExtraHours)

    if person_id is not None:
        query = query.filter(ExtraHours.person_id == person_id)

    # Order by date descending (most recent first)
    query = query.order_by(ExtraHours.date.desc(), ExtraHours.created_at.desc(), ExtraHours.id.desc())

    return query.offset(skip).limit(limit).all()


def update_extra_hours(
    db: Session,
    hours_id: int,
    hours_update: ExtraHoursUpdate,
    current_admin: AdminUser,
) -> ExtraHours:
    """
    Update an extra hours record.

    Args:
        db: Database session
        hours_id: ID of the record to update
        hours_update: Fields to update
        current_admin: Authenticated admin making the update

    Returns:
        Updated ExtraHours object
    """
    record = get_extra_hours_by_id(db, hours_id, current_admin)

    # Update only provided fields
    update_data = hours_update.model_dump(exclude_unset=True)

    # Handle date conversion if provided
    if "date" in update_data and update_data["date"] is not None:
        update_data["date"] = dt.datetime.strptime(update_data["date"], "%Y-%m-%d").date()

    for field, value in update_data.items():
        setattr(record, field, value)

    # Track who edited the record
    record.edited_by_id = current_admin.id

    db.commit()
    db.refresh(record)

    return record


def delete_extra_hours(
    db: Session,
    hours_id: int,
    current_admin: AdminUser,
) -> bool:
    """
    Delete an extra hours record.

    Args:
        db: Database session
        hours_id: ID of the record to delete
        current_admin: Authenticated admin

    Returns:
        True if deleted successfully
    """
    record = get_extra_hours_by_id(db, hours_id, current_admin)

    db.delete(record)
    db.commit()

    return True


def get_person_total_hours(
    db: Session,
    person_id: int,
    current_admin: AdminUser,
) -> dict:
    """
    Calculate total extra hours for a specific person.

    Args:
        db: Database session
        person_id: ID of the person
        current_admin: Authenticated admin

    Returns:
        Dict with total_hours (decimal), total_minutes, total_records
    """
    # Verify person exists
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    total_hours, total_minutes, total_records = db.query(
        func.coalesce(func.sum(ExtraHours.hours), 0),
        func.coalesce(func.sum(ExtraHours.minutes), 0),
        func.count(ExtraHours.id),
    ).filter(ExtraHours.person_id == person_id).one()

    # Normalize minutes into hours
    extra_hours_from_minutes = total_minutes // 60
    remaining_minutes = total_minutes % 60

    total_hours += extra_hours_from_minutes
    decimal_hours = total_hours + (remaining_minutes / 60.0)

    return {
        "person_id": person_id,
        "person_name": f"{person.name} {person.surname}",
        "total_hours": total_hours,
        "total_minutes": remaining_minutes,
        "decimal_hours": round(decimal_hours, 2),
        "total_records": total_records,
    }

