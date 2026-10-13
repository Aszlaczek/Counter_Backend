"""
Service layer for Person CRUD operations.

All functions require an authenticated admin user.
"""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from Models.models import Person, AdminUser, ExtraHours
from Models.schemas import PersonCreate, PersonUpdate, PersonResponse, PersonDetailResponse


def create_person(db: Session, person_data: PersonCreate, current_admin: AdminUser) -> Person:
    """
    Create a new person record.

    Args:
        db: Database session
        person_data: Person creation data
        current_admin: The authenticated admin creating this person

    Returns:
        Created Person object
    """
    person = Person(
        name=person_data.name,
        surname=person_data.surname,
        faculty=person_data.faculty or "Unknown",
        is_working=person_data.is_working if person_data.is_working is not None else True,
        created_by_id=current_admin.id,
    )

    db.add(person)
    db.commit()
    db.refresh(person)

    return person


def get_all_persons(
    db: Session,
    current_admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
    is_working: Optional[bool] = None,
) -> List[Person]:
    """
    Get all persons, with optional filtering.

    Args:
        db: Database session
        current_admin: Authenticated admin (for authorization)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        is_working: Filter by working status (None = no filter)

    Returns:
        List of Person objects
    """
    query = db.query(Person)

    if is_working is not None:
        query = query.filter(Person.is_working == is_working)

    return query.order_by(Person.id).offset(skip).limit(limit).all()


def get_person_by_id(db: Session, person_id: int, current_admin: AdminUser) -> Person:
    """
    Get a single person by ID.

    Args:
        db: Database session
        person_id: ID of the person
        current_admin: Authenticated admin

    Returns:
        Person object

    Raises:
        HTTPException 404: If person not found
    """
    person = db.query(Person).filter(Person.id == person_id).first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    return person


def update_person(
    db: Session,
    person_id: int,
    person_update: PersonUpdate,
    current_admin: AdminUser,
) -> Person:
    """
    Update a person's details.

    Args:
        db: Database session
        person_id: ID of the person to update
        person_update: Fields to update (only non-None fields are applied)
        current_admin: Authenticated admin making the update

    Returns:
        Updated Person object

    Raises:
        HTTPException 404: If person not found
    """
    person = get_person_by_id(db, person_id, current_admin)

    # Update only provided fields
    update_data = person_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)

    # Track who edited the record
    person.edited_by_id = current_admin.id

    db.commit()
    db.refresh(person)

    return person


def delete_person(
    db: Session,
    person_id: int,
    current_admin: AdminUser,
) -> bool:
    """
    Delete a person and all their associated extra hours records.

    Args:
        db: Database session
        person_id: ID of the person to delete
        current_admin: Authenticated admin

    Returns:
        True if deleted successfully

    Raises:
        HTTPException 404: If person not found
    """
    person = get_person_by_id(db, person_id, current_admin)

    # Cascade delete will remove associated extra_hours records
    db.delete(person)
    db.commit()

    return True


def get_person_with_hours_summary(
    db: Session,
    person_id: int,
    current_admin: AdminUser,
) -> PersonDetailResponse:
    """
    Get a person with a summary of their total extra hours.

    Args:
        db: Database session
        person_id: ID of the person
        current_admin: Authenticated admin

    Returns:
        PersonDetailResponse with extra hours summary
    """
    person = get_person_by_id(db, person_id, current_admin)

    total_minutes, record_count = db.query(
        func.coalesce(func.sum(ExtraHours.hours * 60 + ExtraHours.minutes), 0),
        func.count(ExtraHours.id),
    ).filter(ExtraHours.person_id == person_id).one()

    return PersonDetailResponse(
        id=person.id,
        name=person.name,
        surname=person.surname,
        faculty=person.faculty,
        is_working=person.is_working,
        created_by_id=person.created_by_id,
        created_at=person.created_at,
        updated_at=person.updated_at,
        total_extra_hours=round(total_minutes / 60.0, 2),
        extra_hours_count=record_count,
    )

