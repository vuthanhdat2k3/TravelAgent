import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class BookingFlight(Base):
    __tablename__ = "booking_flights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    origin = Column(String(3), nullable=False)  # IATA
    destination = Column(String(3), nullable=False)  # IATA
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    airline_code = Column(String(3), nullable=False)
    flight_number = Column(String(10), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    stops = Column(Integer, default=0, nullable=False)
    cabin_class = Column(String(20), nullable=True)  # ECONOMY, BUSINESS, etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="flights")
