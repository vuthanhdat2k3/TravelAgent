from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
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
) -> list[dict]:
    """Get list of conversations for a user with message counts."""
    # Subquery for message count
    msg_count_sq = (
        select(
            ConversationMessage.conversation_id,
            func.count().label("message_count"),
        )
        .group_by(ConversationMessage.conversation_id)
        .subquery()
    )

    result = await db.execute(
        select(Conversation, func.coalesce(msg_count_sq.c.message_count, 0).label("message_count"))
        .outerjoin(msg_count_sq, Conversation.id == msg_count_sq.c.conversation_id)
        .where(Conversation.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Conversation.updated_at.desc())
    )
    rows = result.all()
    # Attach message_count to each Conversation ORM object
    conversations = []
    for conv, count in rows:
        conv.message_count = count
        conversations.append(conv)
    return conversations


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


async def delete_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete a single conversation (and its messages via cascade)."""
    conversation = await get_conversation_by_id(db, conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    await db.delete(conversation)
    await db.commit()
    return True


async def delete_all_conversations(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Delete all conversations for a user. Returns count deleted."""
    result = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
    )
    count = result.scalar() or 0

    await db.execute(
        delete(Conversation).where(Conversation.user_id == user_id)
    )
    await db.commit()
    return count


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
    
    query = query.order_by(ConversationMessage.created_at.asc()).limit(limit)
    
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
        metadata_={}
    )
    db.add(user_message)
    await db.flush()
    
    # ── Build conversation history for LLM ──
    history_messages: list[dict] = []

    # Load prior messages from this conversation (oldest first)
    prior_query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    prior_result = await db.execute(prior_query)
    for prior_msg in prior_result.scalars().all():
        # Skip the message we just added (it's already in the list)
        if prior_msg.id == user_message.id:
            continue
        history_messages.append({
            "role": prior_msg.role,
            "content": prior_msg.content,
        })

    # Add the current user message at the end
    history_messages.append({
        "role": "user",
        "content": chat_request.message,
    })

    # ── Run multi-agent pipeline ──
    from app.agents.orchestrator import run_agent_pipeline

    # Get current conversation state
    conv_state = dict(conversation.state) if conversation.state else {}

    assistant_content, updated_state, detected_intent = await run_agent_pipeline(
        db=db,
        user_id=user_id,
        user_message=chat_request.message,
        conversation_history=history_messages,
        state=conv_state,
    )

    intent = detected_intent
    agent_name = "router_agent"
    if detected_intent in {"flight_search", "book_flight", "cancel_booking"}:
        agent_name = "flight_agent"
    elif detected_intent in {"view_booking", "view_passengers", "view_preferences", "view_calendar", "general_question"}:
        agent_name = "assistant_agent"

    # Pop transient UI keys from state (must happen before persisting state)
    captured_attachments = updated_state.pop("_attachments", None)
    captured_suggested_actions = updated_state.pop("_suggested_actions", None)

    # Build metadata with attachments for persistence
    msg_metadata: dict = {}
    if captured_attachments:
        msg_metadata["attachments"] = captured_attachments
    if captured_suggested_actions:
        msg_metadata["suggested_actions"] = captured_suggested_actions

    # Save assistant message
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
        intent=intent,
        agent_name=agent_name,
        metadata_=msg_metadata if msg_metadata else {}
    )
    db.add(assistant_message)
    
    # Update conversation state (transient keys already popped)
    conversation.state = updated_state
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
        attachments=captured_attachments or [],
        created_at=assistant_message.created_at
    )


async def send_message_stream(
    db: AsyncSession,
    chat_request: ChatRequest,
    user_id: UUID | None = None,
):
    """
    Send a message and stream the AI response token-by-token.

    Yields JSON strings for SSE events:
      - {"type": "meta", "conversation_id": ..., "user_message_id": ...}
      - {"type": "token", "content": "chunk text"}
      - {"type": "done", "message_id": ..., "full_content": ...}
      - {"type": "error", "content": "error message"}
    """
    import json

    # Get or create conversation
    if chat_request.conversation_id:
        conversation = await get_conversation_by_id(
            db, chat_request.conversation_id, user_id
        )
        if not conversation:
            yield json.dumps({"type": "error", "content": "Conversation not found"})
            return
    else:
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
        metadata_={}
    )
    db.add(user_message)
    await db.flush()

    # Send meta event with conversation_id so frontend can track
    yield json.dumps({
        "type": "meta",
        "conversation_id": str(conversation.id),
        "user_message_id": str(user_message.id),
    })

    # Build conversation history
    history_messages: list[dict] = []
    prior_query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    prior_result = await db.execute(prior_query)
    for prior_msg in prior_result.scalars().all():
        if prior_msg.id == user_message.id:
            continue
        history_messages.append({
            "role": prior_msg.role,
            "content": prior_msg.content,
        })
    history_messages.append({
        "role": "user",
        "content": chat_request.message,
    })

    # Stream AI response via multi-agent pipeline
    from app.agents.orchestrator import stream_agent_pipeline

    # Get current conversation state
    conv_state = dict(conversation.state) if conversation.state else {}

    full_content = ""
    detected_intent = None
    updated_state = conv_state
    captured_attachments = []
    captured_suggested_actions = []

    async for event in stream_agent_pipeline(
        db=db,
        user_id=user_id,
        user_message=chat_request.message,
        conversation_history=history_messages,
        state=conv_state,
    ):
        if event["type"] == "token":
            full_content += event["content"]
            yield json.dumps({"type": "token", "content": event["content"]})
        elif event["type"] == "attachments":
            captured_attachments = event["data"]
            yield json.dumps({"type": "attachments", "data": event["data"]}, default=str)
        elif event["type"] == "suggested_actions":
            captured_suggested_actions = event["data"]
            yield json.dumps({"type": "suggested_actions", "data": event["data"]}, default=str)
        elif event["type"] == "done":
            detected_intent = event.get("intent")
            updated_state = event.get("state", conv_state)
            full_content = event.get("full_content", full_content)
        elif event["type"] == "error":
            full_content = event["content"]
            yield json.dumps({"type": "error", "content": event["content"]})

    # Determine agent name
    agent_name = "router_agent"
    if detected_intent in {"flight_search", "book_flight", "cancel_booking"}:
        agent_name = "flight_agent"
    elif detected_intent in {"view_booking", "view_passengers", "view_preferences", "view_calendar", "general_question"}:
        agent_name = "assistant_agent"

    # Build metadata with attachments for persistence
    msg_metadata = {}
    if captured_attachments:
        msg_metadata["attachments"] = captured_attachments
    if captured_suggested_actions:
        msg_metadata["suggested_actions"] = captured_suggested_actions

    # Save assistant message with full content
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=full_content,
        intent=detected_intent,
        agent_name=agent_name,
        metadata_=msg_metadata if msg_metadata else {}
    )
    db.add(assistant_message)

    # Update conversation state
    conversation.state = updated_state
    conversation.updated_at = user_message.created_at
    await db.commit()
    await db.refresh(assistant_message)

    # Final done event
    yield json.dumps({
        "type": "done",
        "message_id": str(assistant_message.id),
        "full_content": full_content,
    })

