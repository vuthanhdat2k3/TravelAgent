from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import (
    ConversationResponse,
    ChatRequest,
    ChatResponse,
    MessageSchema
)
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user_optional, get_current_active_user

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    channel: str = "web",
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
):
    """Create a new conversation."""
    from app.services.chat_service import create_conversation
    
    user_id = current_user.id if current_user else None
    return await create_conversation(db, user_id, channel)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of conversations for current user."""
    from app.services.chat_service import get_conversations
    
    conversations = await get_conversations(db, current_user.id, skip, limit)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation_details(
    conversation_id: UUID,
    limit: int = 50,
    before: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
):
    """Get conversation details with messages."""
    from app.services.chat_service import get_conversation_by_id, get_conversation_messages
    
    user_id = current_user.id if current_user else None
    
    conversation = await get_conversation_by_id(db, conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = await get_conversation_messages(db, conversation_id, user_id, limit, before)
    
    return {
        "conversation": ConversationResponse.model_validate(conversation),
        "messages": [MessageSchema.model_validate(m) for m in messages]
    }


@router.post("/messages", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
):
    """Send a message and get AI response."""
    from app.services.chat_service import send_message
    
    user_id = current_user.id if current_user else None
    return await send_message(db, chat_request, user_id)


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message_to_conversation(
    conversation_id: UUID,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
):
    """Send a message to a specific conversation."""
    from app.services.chat_service import send_message
    
    # Override conversation_id from path
    chat_request.conversation_id = conversation_id
    
    user_id = current_user.id if current_user else None
    return await send_message(db, chat_request, user_id)
