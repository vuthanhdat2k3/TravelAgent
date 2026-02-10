"""Schemas for Calendar Agent – booking ↔ Google Calendar."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CalendarEventCreate(BaseModel):
    booking_id: UUID
    user_id: UUID
    google_event_id: str
    calendar_id: str | None = None


class CalendarEventResponse(BaseModel):
    id: UUID
    booking_id: UUID
    user_id: UUID
    google_event_id: str
    calendar_id: str | None = None
    synced_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
