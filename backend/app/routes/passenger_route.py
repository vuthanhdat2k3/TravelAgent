from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.passenger import PassengerCreate, PassengerUpdate, PassengerResponse
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.passenger_service import (
    get_passengers,
    get_passenger_by_id,
    create_passenger,
    update_passenger,
    delete_passenger
)

router = APIRouter(prefix="/users/me/passengers", tags=["passengers"])


@router.get("", response_model=list[PassengerResponse])
async def list_passengers(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of passengers for current user."""
    passengers = await get_passengers(db, current_user.id, skip, limit)
    return [PassengerResponse.model_validate(p) for p in passengers]


@router.post("", response_model=PassengerResponse, status_code=status.HTTP_201_CREATED)
async def create_new_passenger(
    passenger_create: PassengerCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new passenger for current user."""
    # Override user_id from JWT (don't trust client)
    passenger_create.user_id = current_user.id
    return await create_passenger(db, current_user.id, passenger_create)


@router.get("/{passenger_id}", response_model=PassengerResponse)
async def get_passenger(
    passenger_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get passenger details."""
    passenger = await get_passenger_by_id(db, passenger_id, current_user.id)
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found or does not belong to user"
        )
    return PassengerResponse.model_validate(passenger)


@router.patch("/{passenger_id}", response_model=PassengerResponse)
async def update_existing_passenger(
    passenger_id: UUID,
    passenger_update: PassengerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update passenger information."""
    return await update_passenger(db, passenger_id, current_user.id, passenger_update)


@router.delete("/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_passenger(
    passenger_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a passenger."""
    await delete_passenger(db, passenger_id, current_user.id)
    return None
