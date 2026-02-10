from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PassengerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    gender: str | None = None  # MALE, FEMALE, OTHER
    dob: date | None = None
    passport_number: str | None = None
    passport_expiry: date | None = None
    nationality: str | None = None  # ISO 3166-1 alpha-3


class PassengerCreate(PassengerBase):
    user_id: UUID


class PassengerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    dob: date | None = None
    passport_number: str | None = None
    passport_expiry: date | None = None
    nationality: str | None = None


class PassengerResponse(PassengerBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
