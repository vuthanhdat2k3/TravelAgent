"""Schemas for chatbot conversation and messages."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ConversationState(BaseModel):
    """Router state stored in conversation.state (JSONB)."""

    current_intent: str | None = None
    slots: dict[str, str] = Field(default_factory=dict)  # origin, destination, depart_date, etc.
    last_offer_ids: list[str] = Field(default_factory=list)
    selected_passenger_id: UUID | None = None
    step: str | None = None  # e.g. "awaiting_offer_choice", "awaiting_passenger"
    metadata_: dict | None = Field(None, alias="metadata")

    model_config = {"populate_by_name": True}


class MessageSchema(BaseModel):
    """Single message in a conversation."""

    id: UUID
    role: str  # user, assistant, system
    content: str
    intent: str | None = None
    agent_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """Incoming user message to the chatbot."""

    message: str = Field(..., min_length=1)
    conversation_id: UUID | None = None  # if null, create new conversation
    user_id: UUID | None = None  # if null, anonymous session
    channel: str = "web"


class SuggestedAction(BaseModel):
    """Quick reply or button suggestion."""

    label: str
    payload: str | None = None  # e.g. "1" for "chọn chuyến 1"
    type_: str = Field(default="quick_reply", alias="type")

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    """Assistant reply from the chatbot."""

    conversation_id: UUID
    message_id: UUID
    content: str
    intent: str | None = None
    agent_name: str | None = None
    state: ConversationState | None = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)  # e.g. offer cards, booking summary
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ConversationResponse(BaseModel):
    """Conversation session summary."""

    id: UUID
    user_id: UUID | None = None
    channel: str
    state: ConversationState | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}
