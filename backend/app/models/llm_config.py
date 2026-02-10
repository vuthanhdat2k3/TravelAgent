"""Model for storing user LLM provider configuration."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class LLMConfig(Base):
    """Stores selected LLM provider & model configuration per user."""

    __tablename__ = "llm_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Provider: "gemini" | "ollama"
    provider = Column(String(50), nullable=False, default="gemini")

    # Model name, e.g. "gemini-2.0-flash", "llama3.1:8b"
    model_name = Column(String(255), nullable=False, default="gemini-2.0-flash")

    # API key for Gemini (stored encrypted in production)
    api_key = Column(Text, nullable=True)

    # Base URL for Ollama (default: http://localhost:11434)
    base_url = Column(String(512), nullable=True, default="http://localhost:11434")

    # Generation parameters
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Float, nullable=True, default=2048)

    # Whether this config is active
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="llm_config")
