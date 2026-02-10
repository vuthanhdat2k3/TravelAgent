from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.booking import Booking
from app.models.booking_flight import BookingFlight
from app.models.passenger import Passenger
from app.schemas.booking import BookingCreateRequest, BookingResponse, BookingListResponse


async def get_booking_by_id(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID
) -> Booking | None:
    """Get booking by ID, ensuring it belongs to the user."""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def get_bookings(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
    status_filter: str | None = None
) -> list[Booking]:
    """Get list of bookings for a user."""
    query = select(Booking).where(Booking.user_id == user_id)
    
    if status_filter:
        query = query.where(Booking.status == status_filter)
    
    query = query.offset(skip).limit(limit).order_by(Booking.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_booking(
    db: AsyncSession,
    user_id: UUID,
    booking_request: BookingCreateRequest
) -> BookingResponse:
    """
    Create a new booking.
    Validates passenger ownership and offer_id.
    """
    # Verify passenger belongs to user
    passenger_result = await db.execute(
        select(Passenger).where(
            Passenger.id == booking_request.passenger_id,
            Passenger.user_id == user_id
        )
    )
    passenger = passenger_result.scalar_one_or_none()
    
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found or does not belong to user"
        )
    
    # TODO: Validate offer_id with cache or Amadeus API
    # TODO: Get flight details from cache/Amadeus
    # TODO: Call Amadeus Order/Booking API
    
    # For now, create booking with PENDING status
    db_booking = Booking(
        user_id=user_id,
        passenger_id=booking_request.passenger_id,
        status="PENDING",
        provider="AMADEUS",
        amadeus_offer_id=booking_request.offer_id,
        # booking_reference will be set after Amadeus confirms
        # total_price and currency will come from Amadeus response
    )
    
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    
    # TODO: Create BookingFlight records from offer details
    
    return BookingResponse.model_validate(db_booking)


async def cancel_booking(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID,
    reason: str | None = None
) -> BookingResponse:
    """Cancel a booking."""
    db_booking = await get_booking_by_id(db, booking_id, user_id)
    
    if not db_booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    
    # Check if booking can be cancelled
    if db_booking.status in ["CANCELLED", "REFUNDED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking already {db_booking.status.lower()}"
        )
    
    # TODO: Call Amadeus cancel API if needed
    
    # Update booking status
    db_booking.status = "CANCELLED"
    
    await db.commit()
    await db.refresh(db_booking)
    
    return BookingResponse.model_validate(db_booking)
