"""Schemas for Notification Agent – sent notification log."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class NotificationLogCreate(BaseModel):
    user_id: UUID
    type_: str  # booking_confirmed, checkin_reminder, etc.
    channel: str  # email, telegram
    subject: str | None = None
    ref_id: UUID | None = None
    status: str = "sent"
    metadata_: str | None = None


class NotificationLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    type_: str = Field(alias="type")
    channel: str
    subject: str | None = None
    ref_id: UUID | None = None
    status: str
    sent_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
