import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("passengers.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    provider = Column(String(50), nullable=False, default="AMADEUS")
    amadeus_offer_id = Column(Text, nullable=True)
    booking_reference = Column(String(50), nullable=True, index=True)
    total_price = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(3), nullable=True, default="VND")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bookings")
    passenger = relationship("Passenger", back_populates="bookings")
    flights = relationship("BookingFlight", back_populates="booking", cascade="all, delete-orphan", order_by="BookingFlight.departure_time")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="booking", cascade="all, delete-orphan")
