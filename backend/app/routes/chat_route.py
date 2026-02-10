from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single conversation and all its messages."""
    from app.services.chat_service import delete_conversation as _delete
    await _delete(db, conversation_id, current_user.id)
    return None


@router.delete("/conversations", status_code=status.HTTP_200_OK)
async def delete_all_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all conversations for the current user."""
    from app.services.chat_service import delete_all_conversations as _delete_all
    count = await _delete_all(db, current_user.id)
    return {"deleted": count}


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


@router.post("/messages/stream")
async def stream_chat_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
):
    """Send a message and stream AI response via Server-Sent Events (SSE)."""
    from app.services.chat_service import send_message_stream
    import json, logging

    user_id = current_user.id if current_user else None
    _logger = logging.getLogger(__name__)

    async def event_generator():
        try:
            async for chunk in send_message_stream(db, chat_request, user_id):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            _logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Đã xảy ra lỗi. Vui lòng thử lại.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
