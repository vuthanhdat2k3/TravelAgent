"""Schemas for LLM configuration management."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    NVIDIA = "nvidia"


class LLMConfigCreate(BaseModel):
    """Create/update LLM configuration."""

    provider: LLMProvider = LLMProvider.GEMINI
    model_name: str = Field(default="gemini-2.0-flash", max_length=255)
    api_key: str | None = None  # Required for Gemini
    base_url: str | None = Field(default="http://localhost:11434", max_length=512)  # For Ollama
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: float | None = Field(default=2048, ge=1)


class LLMConfigUpdate(BaseModel):
    """Partial update of LLM configuration."""

    provider: LLMProvider | None = None
    model_name: str | None = Field(default=None, max_length=255)
    api_key: str | None = None
    base_url: str | None = Field(default=None, max_length=512)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: float | None = Field(default=None, ge=1)


class LLMConfigResponse(BaseModel):
    """LLM configuration response (hides API key)."""

    id: UUID
    user_id: UUID
    provider: str
    model_name: str
    api_key_set: bool = False  # True if api_key is configured
    base_url: str | None = None
    temperature: float
    max_tokens: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AvailableModel(BaseModel):
    """An available model option."""

    provider: str
    model_name: str
    display_name: str
    description: str


class AvailableModelsResponse(BaseModel):
    """List of all available models."""

    models: list[AvailableModel]
