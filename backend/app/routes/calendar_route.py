from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.calendar_event import CalendarEventResponse
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.calendar_service import (
    get_calendar_events_by_user,
    get_calendar_events_by_booking,
    create_calendar_event
)

router = APIRouter(tags=["calendar"])


@router.post("/bookings/{booking_id}/calendar", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def add_booking_to_calendar(
    booking_id: UUID,
    calendar_id: str = "primary",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a booking to Google Calendar."""
    return await create_calendar_event(db, booking_id, current_user.id, calendar_id)


@router.get("/users/me/calendar-events", response_model=list[CalendarEventResponse])
async def list_my_calendar_events(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all calendar events for current user."""
    events = await get_calendar_events_by_user(db, current_user.id, skip, limit)
    return [CalendarEventResponse.model_validate(e) for e in events]


@router.get("/bookings/{booking_id}/calendar", response_model=list[CalendarEventResponse])
async def list_booking_calendar_events(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get calendar events for a specific booking."""
    events = await get_calendar_events_by_booking(db, booking_id, current_user.id)
    return [CalendarEventResponse.model_validate(e) for e in events]
