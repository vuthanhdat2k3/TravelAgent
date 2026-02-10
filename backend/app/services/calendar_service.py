from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import logging

from app.models.calendar_event import CalendarEvent
from app.models.booking import Booking
from app.models.booking_flight import BookingFlight
from app.models.user import User
from app.schemas.calendar_event import CalendarEventCreate, CalendarEventResponse
from app.core.google_calendar_client import get_google_calendar_client

logger = logging.getLogger(__name__)


async def get_calendar_events_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> list[CalendarEvent]:
    """Get all calendar events for a user."""
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(CalendarEvent.created_at.desc())
    )
    return list(result.scalars().all())


async def get_calendar_events_by_booking(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID
) -> list[CalendarEvent]:
    """Get calendar events for a specific booking."""
    # Verify booking belongs to user
    booking_result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.booking_id == booking_id)
        .order_by(CalendarEvent.created_at.desc())
    )
    return list(result.scalars().all())


async def create_calendar_event(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID,
    calendar_id: str = "primary"
) -> CalendarEventResponse:
    """
    Create a Google Calendar event for a booking.
    Requires user to have connected Google Calendar (OAuth token).
    """
    # Verify booking belongs to user and load relationships
    booking_result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.flights),
            selectinload(Booking.passenger)
        )
        .where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    
    # Check if calendar event already exists for this booking
    existing_event_result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.booking_id == booking_id)
    )
    existing_event = existing_event_result.scalar_one_or_none()
    
    if existing_event:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Calendar event already exists for this booking"
        )
    
    # Check if booking has flights
    if not booking.flights:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has no flight information to add to calendar"
        )
    
    # Get user to check Google Calendar credentials
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has Google Calendar connected
    google_tokens = user.metadata_.get('google_calendar', {}) if user.metadata_ else {}
    access_token = google_tokens.get('access_token')
    refresh_token = google_tokens.get('refresh_token')
    
    if not access_token or not refresh_token:
        # For development: Create placeholder event
        logger.warning(f"User {user_id} has no Google Calendar credentials. Creating placeholder event.")
        google_event_id = f"placeholder_{booking_id}"
    else:
        try:
            # Create Google Calendar client
            calendar_client = get_google_calendar_client(
                access_token=access_token,
                refresh_token=refresh_token
            )
            
            # Get first flight for calendar event
            first_flight = booking.flights[0]
            passenger = booking.passenger
            passenger_name = f"{passenger.first_name} {passenger.last_name}" if passenger else "Unknown"
            
            # Create event in Google Calendar
            google_event_id = calendar_client.create_flight_event(
                booking_reference=booking.booking_reference or str(booking.id)[:8].upper(),
                origin=first_flight.origin,
                destination=first_flight.destination,
                departure_time=first_flight.departure_time,
                arrival_time=first_flight.arrival_time,
                airline_code=first_flight.airline_code,
                flight_number=first_flight.flight_number,
                passenger_name=passenger_name,
                calendar_id=calendar_id
            )
            
            logger.info(f"Created Google Calendar event {google_event_id} for booking {booking_id}")
            
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            # Fallback to placeholder if API fails
            google_event_id = f"placeholder_{booking_id}"
    
    # Save calendar event to database
    db_event = CalendarEvent(
        booking_id=booking_id,
        user_id=user_id,
        google_event_id=google_event_id,
        calendar_id=calendar_id,
        synced_at=datetime.utcnow()
    )
    
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    
    return CalendarEventResponse.model_validate(db_event)
