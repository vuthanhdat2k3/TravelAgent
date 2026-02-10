from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.calendar_event import CalendarEvent
from app.models.booking import Booking
from app.schemas.calendar_event import CalendarEventCreate, CalendarEventResponse


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
    
    # TODO: Check if user has Google Calendar OAuth token
    # If not, raise 400 "Google Calendar not connected"
    
    # TODO: Get flight details from BookingFlight
    # TODO: Call Google Calendar API to create event
    # For now, create a placeholder event
    
    google_event_id = f"placeholder_{booking_id}"  # Replace with actual Google event ID
    
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
