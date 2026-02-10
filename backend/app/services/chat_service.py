from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.schemas.chat import (
    ConversationResponse,
    ChatRequest,
    ChatResponse,
    MessageSchema
)


async def get_conversation_by_id(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID | None = None
) -> Conversation | None:
    """Get conversation by ID, optionally filtering by user_id."""
    query = select(Conversation).where(Conversation.id == conversation_id)
    
    if user_id:
        query = query.where(Conversation.user_id == user_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_conversations(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> list[Conversation]:
    """Get list of conversations for a user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def create_conversation(
    db: AsyncSession,
    user_id: UUID | None = None,
    channel: str = "web"
) -> ConversationResponse:
    """Create a new conversation."""
    db_conversation = Conversation(
        user_id=user_id,
        channel=channel,
        state={}
    )
    
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    
    return ConversationResponse.model_validate(db_conversation)


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID | None = None,
    limit: int = 50,
    before_message_id: UUID | None = None
) -> list[ConversationMessage]:
    """Get messages for a conversation with optional cursor pagination."""
    # Verify conversation exists and belongs to user (if user_id provided)
    conversation = await get_conversation_by_id(db, conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    query = select(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    )
    
    if before_message_id:
        query = query.where(ConversationMessage.id < before_message_id)
    
    query = query.order_by(ConversationMessage.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def send_message(
    db: AsyncSession,
    chat_request: ChatRequest,
    user_id: UUID | None = None
) -> ChatResponse:
    """
    Send a message and get AI response.
    Creates conversation if conversation_id not provided.
    """
    # Get or create conversation
    if chat_request.conversation_id:
        conversation = await get_conversation_by_id(
            db, chat_request.conversation_id, user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=user_id,
            channel=chat_request.channel or "web",
            state={}
        )
        db.add(conversation)
        await db.flush()
    
    # Save user message
    user_message = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.message,
        metadata={}
    )
    db.add(user_message)
    await db.flush()
    
    # TODO: Call Router/Orchestrator to process message
    # TODO: Route to appropriate agent (Flight, Booking, Calendar, Profile, etc.)
    # TODO: Generate AI response
    
    # Placeholder response
    assistant_content = "I'm a placeholder response. AI integration coming soon!"
    intent = None
    agent_name = "router"
    
    # Save assistant message
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
        intent=intent,
        agent_name=agent_name,
        metadata={}
    )
    db.add(assistant_message)
    
    # Update conversation
    conversation.updated_at = user_message.created_at
    
    await db.commit()
    await db.refresh(assistant_message)
    
    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        content=assistant_content,
        intent=intent,
        agent_name=agent_name,
        state=conversation.state,
        suggested_actions=[],
        attachments=[],
        created_at=assistant_message.created_at
    )
