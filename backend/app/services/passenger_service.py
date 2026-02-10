from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.passenger import Passenger
from app.schemas.passenger import PassengerCreate, PassengerUpdate, PassengerResponse


async def get_passenger_by_id(
    db: AsyncSession, passenger_id: UUID, user_id: UUID
) -> Passenger | None:
    """Get passenger by ID, ensuring it belongs to the user."""
    result = await db.execute(
        select(Passenger).where(
            Passenger.id == passenger_id,
            Passenger.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def get_passengers(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50
) -> list[Passenger]:
    """Get list of passengers for a user."""
    result = await db.execute(
        select(Passenger)
        .where(Passenger.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Passenger.created_at.desc())
    )
    return list(result.scalars().all())


async def create_passenger(
    db: AsyncSession,
    user_id: UUID,
    passenger_create: PassengerCreate
) -> PassengerResponse:
    """Create a new passenger for the user."""
    # Always use user_id from JWT, not from client
    db_passenger = Passenger(
        user_id=user_id,
        first_name=passenger_create.first_name,
        last_name=passenger_create.last_name,
        gender=passenger_create.gender,
        dob=passenger_create.dob,
        passport_number=passenger_create.passport_number,
        passport_expiry=passenger_create.passport_expiry,
        nationality=passenger_create.nationality,
    )
    
    db.add(db_passenger)
    await db.commit()
    await db.refresh(db_passenger)
    
    return PassengerResponse.model_validate(db_passenger)


async def update_passenger(
    db: AsyncSession,
    passenger_id: UUID,
    user_id: UUID,
    passenger_update: PassengerUpdate
) -> PassengerResponse:
    """Update a passenger."""
    db_passenger = await get_passenger_by_id(db, passenger_id, user_id)
    if not db_passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found or does not belong to user"
        )
    
    # Update fields
    update_data = passenger_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_passenger, field, value)
    
    await db.commit()
    await db.refresh(db_passenger)
    
    return PassengerResponse.model_validate(db_passenger)


async def delete_passenger(
    db: AsyncSession,
    passenger_id: UUID,
    user_id: UUID
) -> None:
    """Delete a passenger."""
    db_passenger = await get_passenger_by_id(db, passenger_id, user_id)
    if not db_passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found or does not belong to user"
        )
    
    await db.delete(db_passenger)
    await db.commit()
