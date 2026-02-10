"""Schemas for Flight Search Agent – offer cache (internal use)."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class FlightOfferCacheCreate(BaseModel):
    search_key: str
    offer_id: str
    payload: dict  # normalized offer JSON
    expires_at: datetime


class FlightOfferCacheResponse(BaseModel):
    id: UUID
    search_key: str
    offer_id: str
    payload: dict
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
