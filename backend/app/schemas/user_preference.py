"""Schemas for User Profile Agent – user preferences."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserPreferenceBase(BaseModel):
    cabin_class: str | None = Field("ECONOMY", description="ECONOMY, BUSINESS, etc.")
    preferred_airlines: list[str] | None = Field(None, description="IATA codes e.g. ['VN','VJ']")
    seat_preference: str | None = None  # window, aisle
    default_passenger_id: UUID | None = None


class UserPreferenceCreate(UserPreferenceBase):
    user_id: UUID


class UserPreferenceUpdate(BaseModel):
    cabin_class: str | None = None
    preferred_airlines: list[str] | None = None
    seat_preference: str | None = None
    default_passenger_id: UUID | None = None


class UserPreferenceResponse(UserPreferenceBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
