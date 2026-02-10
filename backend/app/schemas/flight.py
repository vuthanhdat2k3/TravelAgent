from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3, description="IATA code, e.g. HAN")
    destination: str = Field(..., min_length=3, max_length=3, description="IATA code, e.g. SGN")
    depart_date: date
    return_date: Optional[date] = None
    adults: int = Field(1, ge=1, le=9)
    travel_class: str = Field("ECONOMY", description="ECONOMY or BUSINESS")
    currency: str = Field("VND", max_length=3)
    
    @field_validator('return_date', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for optional date field."""
        if v == '' or v is None:
            return None
        return v
    
    @field_validator('origin', 'destination')
    @classmethod
    def uppercase_iata_codes(cls, v):
        """Convert IATA codes to uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v


class FlightSegment(BaseModel):
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    airline_code: str
    flight_number: str


class FlightOffer(BaseModel):
    offer_id: str  # Amadeus flightOfferId
    total_price: float
    currency: str
    duration_minutes: int
    stops: int
    segments: list[FlightSegment]
