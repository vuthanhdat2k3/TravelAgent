from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.flight import FlightSegment


class BookingCreateRequest(BaseModel):
    passenger_id: UUID
    offer_id: str  # flightOfferId from Amadeus


class BookingFlightSchema(BaseModel):
    id: UUID
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    airline_code: str
    flight_number: str
    duration_minutes: int
    stops: int
    cabin_class: str | None = None

    model_config = {"from_attributes": True}


class BookingResponse(BaseModel):
    booking_id: UUID = Field(alias="id")
    status: str
    provider: str
    booking_reference: str | None = None
    total_price: float | None = None
    currency: str | None = None
    flights: list[FlightSegment] = []
    created_at: datetime | None = None
    confirmed_at: datetime | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class BookingListResponse(BaseModel):
    id: UUID
    user_id: UUID
    passenger_id: UUID
    status: str
    provider: str
    booking_reference: str | None = None
    total_price: float | None = None
    currency: str | None = None
    created_at: datetime
    confirmed_at: datetime | None = None
    flights: list[BookingFlightSchema] = []

    model_config = {"from_attributes": True}
