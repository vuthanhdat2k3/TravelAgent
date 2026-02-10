import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base


class FlightOfferCache(Base):
    """Cached Amadeus flight offers. Keyed by search params hash, TTL expiry."""

    __tablename__ = "flight_offer_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_key = Column(String(64), nullable=False, index=True)  # hash(origin, destination, date, adults, class)
    offer_id = Column(String(255), nullable=False, index=True)  # Amadeus offer id
    payload = Column(JSONB, nullable=False)  # normalized offer (price, segments, etc.)
    flight_numbers = Column(JSONB, nullable=True)  # Array of flight numbers like ["VJ145", "VN123"]
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_flight_offer_cache_search_expires", "search_key", "expires_at"),
        Index("ix_flight_offer_cache_flight_numbers", "flight_numbers", postgresql_using="gin"),
    )
