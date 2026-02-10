import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class UserPreference(Base):
    """User travel preferences: cabin, airlines, seat, etc. Used by Profile Agent."""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    cabin_class = Column(String(20), nullable=True, default="ECONOMY")  # ECONOMY, BUSINESS, etc.
    preferred_airlines = Column(JSONB, nullable=True)  # ["VN", "VJ"] IATA codes
    seat_preference = Column(String(20), nullable=True)  # window, aisle, etc.
    default_passenger_id = Column(UUID(as_uuid=True), ForeignKey("passengers.id", ondelete="SET NULL"), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)  # extra preferences
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_preference")
