import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class FlightSearch(Base):
    __tablename__ = "flight_searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # nullable for anonymous search
    origin = Column(String(3), nullable=False)  # IATA
    destination = Column(String(3), nullable=False)  # IATA
    depart_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    adults = Column(Integer, default=1, nullable=False)
    travel_class = Column(String(20), nullable=True, default="ECONOMY")  # ECONOMY, BUSINESS
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="flight_searches")
