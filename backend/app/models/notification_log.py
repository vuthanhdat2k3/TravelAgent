import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class NotificationLog(Base):
    """Log of sent notifications (email, telegram). For Notification Agent."""

    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type_ = Column("type", String(50), nullable=False)  # booking_confirmed, checkin_reminder, etc.
    channel = Column(String(50), nullable=False)  # email, telegram
    subject = Column(String(255), nullable=True)  # email subject or title
    ref_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # booking_id or similar
    status = Column(String(20), nullable=False, default="sent")  # sent, failed
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    metadata_ = Column("metadata", Text, nullable=True)  # JSON string for payload/error

    # Relationships
    user = relationship("User", back_populates="notification_logs")
