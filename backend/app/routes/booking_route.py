from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.booking import BookingCreateRequest, BookingResponse, BookingListResponse
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.booking_service import (
    get_bookings,
    get_booking_by_id,
    create_booking,
    cancel_booking
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_new_booking(
    booking_request: BookingCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new booking."""
    return await create_booking(db, current_user.id, booking_request)


@router.get("", response_model=list[BookingListResponse])
async def list_my_bookings(
    skip: int = 0,
    limit: int = 20,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of bookings for current user."""
    bookings = await get_bookings(db, current_user.id, skip, limit, status_filter)
    return [BookingListResponse.model_validate(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingListResponse)
async def get_booking_details(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get booking details."""
    booking = await get_booking_by_id(db, booking_id, current_user.id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    return BookingListResponse.model_validate(booking)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_existing_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking."""
    return await cancel_booking(db, booking_id, current_user.id)
