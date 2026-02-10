"""
Orchestrator – builds 3 LLM instances and runs the multi-agent pipeline.

This is the main entry point called by chat_service.
It replaces the old single-LLM approach with the Router → Agent flow.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel

from app.llm.provider import build_llm, _resolve_config
from app.llm.rate_limiter import llm_rate_limiter, RateLimitExceeded
from app.agents.router_agent import route_message

logger = logging.getLogger(__name__)


async def _build_agent_llms(db: AsyncSession, user_id: UUID | None) -> tuple[BaseChatModel, BaseChatModel, BaseChatModel]:
    """
    Build 3 separate LLM instances for the 3 agents.

    All use the same provider/model config from user settings,
    but each is a separate instance so they maintain independent states.

    Returns: (router_llm, flight_llm, assistant_llm)
    """
    config = await _resolve_config(db, user_id)

    # Build 3 independent instances
    router_llm = build_llm(config)
    flight_llm = build_llm(config)
    assistant_llm = build_llm(config)

    return router_llm, flight_llm, assistant_llm


async def run_agent_pipeline(
    db: AsyncSession,
    user_id: UUID | None,
    user_message: str,
    conversation_history: list[dict],
    state: dict,
) -> tuple[str, dict, str | None]:
    """
    Run the full multi-agent pipeline for a user message.

    Parameters
    ----------
    db : AsyncSession
    user_id : UUID | None
    user_message : str
    conversation_history : list[dict]
        Previous messages [{role, content}, ...]
    state : dict
        Conversation state (will be mutated and returned)

    Returns
    -------
    tuple[str, dict, str | None]
        (response_text, updated_state, detected_intent)
    """
    # Rate limit check
    try:
        await llm_rate_limiter.check_rate_limit(user_id)
    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for user {user_id}: {e.message}")
        return e.message, state, None

    # Build LLMs
    try:
        router_llm, flight_llm, assistant_llm = await _build_agent_llms(db, user_id)
    except Exception as e:
        logger.error(f"Failed to build agent LLMs: {e}")
        return (
            "⚠️ Không thể khởi tạo mô hình AI. "
            "Vui lòng kiểm tra cài đặt LLM trong Settings.\n\n"
            f"Chi tiết: {e}"
        ), state, None

    # Run the router
    try:
        response_text, updated_state, intent = await route_message(
            router_llm=router_llm,
            flight_llm=flight_llm,
            assistant_llm=assistant_llm,
            user_message=user_message,
            user_id=str(user_id) if user_id else "",
            conversation_history=conversation_history,
            state=state,
        )

        # Record successful call for rate limiting
        llm_rate_limiter.record_call(user_id)

        # Note: _attachments and _suggested_actions are LEFT in state
        # so the caller (chat_service) can extract them for metadata.
        # The caller must pop them before persisting state to DB.

        return response_text, updated_state, intent

    except Exception as e:
        logger.error(f"Agent pipeline error: {e}", exc_info=True)
        return (
            f"⚠️ Lỗi khi xử lý yêu cầu.\n\n"
            f"Chi tiết: {str(e)}\n\n"
            "Vui lòng thử lại hoặc kiểm tra cài đặt LLM."
        ), state, None


async def stream_agent_pipeline(
    db: AsyncSession,
    user_id: UUID | None,
    user_message: str,
    conversation_history: list[dict],
    state: dict,
):
    """
    Stream version – runs the pipeline and yields the response.

    Since agent tool-calling happens all at once (not token-by-token),
    we run the full pipeline first, then stream the final response
    using the LLM's streaming capability for a better UX.

    Yields: str chunks
    Also yields a special final dict with state and intent info.
    """

    # Rate limit check
    try:
        await llm_rate_limiter.check_rate_limit(user_id)
    except RateLimitExceeded as e:
        yield {"type": "error", "content": e.message}
        return

    # Build LLMs
    try:
        router_llm, flight_llm, assistant_llm = await _build_agent_llms(db, user_id)
    except Exception as e:
        yield {"type": "error", "content": f"⚠️ Không thể khởi tạo AI: {e}"}
        return

    # Run the full pipeline (non-streaming, since agents need tool results)
    try:
        response_text, updated_state, intent = await route_message(
            router_llm=router_llm,
            flight_llm=flight_llm,
            assistant_llm=assistant_llm,
            user_message=user_message,
            user_id=str(user_id) if user_id else "",
            conversation_history=conversation_history,
            state=state,
        )

        llm_rate_limiter.record_call(user_id)

        # Stream the response text character-by-character for smooth UX
        # (or in small chunks)
        chunk_size = 8  # chars per chunk for smooth streaming effect
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            yield {"type": "token", "content": chunk}

        # Emit structured attachments (flight cards, booking success, etc.)
        attachments = updated_state.pop("_attachments", None)
        if attachments:
            yield {"type": "attachments", "data": attachments}

        # Emit suggested actions (calendar, etc.)
        suggested_actions = updated_state.pop("_suggested_actions", None)
        if suggested_actions:
            yield {"type": "suggested_actions", "data": suggested_actions}

        # Yield final metadata
        yield {
            "type": "done",
            "state": updated_state,
            "intent": intent,
            "full_content": response_text,
        }

    except Exception as e:
        logger.error(f"Stream agent pipeline error: {e}", exc_info=True)
        yield {"type": "error", "content": f"⚠️ Lỗi: {str(e)}"}
