from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import logging

from app.models.booking import Booking
from app.models.booking_flight import BookingFlight
from app.models.passenger import Passenger
from app.models.flight_offer_cache import FlightOfferCache
from app.schemas.booking import BookingCreateRequest, BookingResponse, BookingListResponse
from app.schemas.flight import FlightSegment

logger = logging.getLogger(__name__)


async def get_booking_by_id(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID
) -> Booking | None:
    """Get booking by ID, ensuring it belongs to the user."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.flights))  # Eager load flights
        .where(
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
    query = select(Booking).options(selectinload(Booking.flights)).where(Booking.user_id == user_id)
    
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
    
    # Get flight offer from cache
    # Multiple cache entries may exist for same offer_id (from multiple searches)
    # Always get the newest one
    offer_cache_result = await db.execute(
        select(FlightOfferCache).where(
            FlightOfferCache.offer_id == booking_request.offer_id,
            FlightOfferCache.expires_at > datetime.utcnow()
        )
        .order_by(FlightOfferCache.created_at.desc())
        .limit(1)
    )
    offer_cache = offer_cache_result.scalar_one_or_none()
    
    if not offer_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight offer not found or expired. Please search again."
        )
    
    offer_payload = offer_cache.payload
    
    # Extract price and currency from offer
    total_price = offer_payload.get("total_price", 0)
    currency = offer_payload.get("currency", "VND")
    
    # Create booking with PENDING status
    db_booking = Booking(
        user_id=user_id,
        passenger_id=booking_request.passenger_id,
        status="PENDING",
        provider="AMADEUS",
        amadeus_offer_id=booking_request.offer_id,
        total_price=total_price,
        currency=currency,
        # booking_reference will be set after Amadeus confirms
    )
    
    db.add(db_booking)
    await db.flush()  # Get booking ID without committing
    
    # Create BookingFlight records from offer segments
    flight_responses = []
    segments = offer_payload.get("segments", [])
    
    for segment in segments:
        # Parse datetime strings
        try:
            departure_time = datetime.fromisoformat(segment.get("departure_time", "").replace("Z", "+00:00"))
            arrival_time = datetime.fromisoformat(segment.get("arrival_time", "").replace("Z", "+00:00"))
        except ValueError as e:
            logger.warning(f"Failed to parse flight times: {e}")
            continue
        
        # Calculate duration
        duration_minutes = int((arrival_time - departure_time).total_seconds() / 60)
        
        flight_number = f"{segment.get('airline_code', '')}{segment.get('flight_number', '')}"
        
        booking_flight = BookingFlight(
            booking_id=db_booking.id,
            origin=segment.get("origin", ""),
            destination=segment.get("destination", ""),
            departure_time=departure_time,
            arrival_time=arrival_time,
            airline_code=segment.get("airline_code", ""),
            flight_number=flight_number,
            duration_minutes=duration_minutes,
            stops=offer_payload.get("stops", 0),
            cabin_class=segment.get("cabin_class", "ECONOMY")
        )
        
        db.add(booking_flight)
        
        # Build flight response
        flight_responses.append(FlightSegment(
            origin=booking_flight.origin,
            destination=booking_flight.destination,
            departure_time=booking_flight.departure_time,
            arrival_time=booking_flight.arrival_time,
            airline_code=booking_flight.airline_code,
            flight_number=booking_flight.flight_number
        ))
    
    await db.commit()
    
    # Manually create response to avoid lazy-loading issues
    return BookingResponse(
        id=db_booking.id,
        status=db_booking.status,
        provider=db_booking.provider,
        booking_reference=db_booking.booking_reference,
        total_price=float(db_booking.total_price) if db_booking.total_price else None,
        currency=db_booking.currency,
        flights=flight_responses,
        created_at=db_booking.created_at,
        confirmed_at=db_booking.confirmed_at,
    )


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
    
    # Manually create response to avoid lazy-loading issues
    return BookingResponse(
        id=db_booking.id,
        status=db_booking.status,
        provider=db_booking.provider,
        booking_reference=db_booking.booking_reference,
        total_price=float(db_booking.total_price) if db_booking.total_price else None,
        currency=db_booking.currency,
        flights=[],  # Will be populated when BookingFlight records are created
        created_at=db_booking.created_at,
        confirmed_at=db_booking.confirmed_at,
    )
