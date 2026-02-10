"""Schemas for Router/Orchestrator intent and agent context."""

from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class ChatIntent(str, Enum):
    """Supported user intents for the router."""

    FLIGHT_SEARCH = "flight_search"
    BOOK_FLIGHT = "book_flight"
    VIEW_BOOKING = "view_booking"
    CANCEL_BOOKING = "cancel_booking"
    ADD_TO_CALENDAR = "add_to_calendar"
    ASK_ITINERARY = "ask_itinerary"
    PROFILE_UPDATE = "profile_update"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    """Output of intent classification."""

    intent: ChatIntent
    confidence: float = Field(..., ge=0, le=1)
    slots: dict[str, str] = Field(default_factory=dict)  # extracted entities
    raw_intent: str | None = None  # original LLM label if different from enum


class AgentContext(BaseModel):
    """Context passed between Router and sub-agents."""

    conversation_id: UUID
    user_id: UUID | None = None
    intent: ChatIntent
    slots: dict[str, str] = Field(default_factory=dict)
    last_offer_ids: list[str] = Field(default_factory=list)
    selected_offer_id: str | None = None
    selected_passenger_id: UUID | None = None
    step: str | None = None
    metadata_: dict | None = Field(None, alias="metadata")


class AgentResponse(BaseModel):
    """Generic response from a sub-agent."""

    success: bool
    message: str = ""
    data: dict | None = None  # agent-specific payload
    next_step: str | None = None  # suggested step for router
    suggested_actions: list[dict] = Field(default_factory=list)
