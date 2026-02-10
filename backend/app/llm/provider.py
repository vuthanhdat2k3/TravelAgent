"""
LLM provider abstraction – Gemini (Google AI) & Ollama (local).

Includes three layers of protection:
  1. Rate Limiting  – per-user sliding window (min/hour/day)
  2. Retry w/ Backoff – exponential backoff for transient errors
  3. Fallback – graceful error messages, never crashes
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings
from app.models.llm_config import LLMConfig
from app.services.llm_config_service import get_llm_config
from app.llm.rate_limiter import llm_rate_limiter, RateLimitExceeded

logger = logging.getLogger(__name__)

# ── Retry configuration ────────────────────────────────────────────────────

MAX_RETRIES = 2           # At most 2 retries (total 3 attempts)
INITIAL_BACKOFF_S = 1.0   # First retry after 1 s
BACKOFF_MULTIPLIER = 2.0  # Double delay each retry

# Exceptions worth retrying (transient / rate-limit from provider)
_RETRYABLE_KEYWORDS = frozenset([
    "rate limit",
    "rate_limit",
    "429",
    "quota",
    "resource exhausted",
    "resourceexhausted",
    "503",
    "service unavailable",
    "temporarily unavailable",
    "timeout",
    "timed out",
    "connection",
    "DEADLINE_EXCEEDED",
])


def _is_retryable(exc: Exception) -> bool:
    """Check if exception is transient and worth retrying."""
    msg = str(exc).lower()
    return any(kw in msg for kw in _RETRYABLE_KEYWORDS)


# ── System prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Bạn là Travel Agent AI – trợ lý du lịch thông minh.

Nhiệm vụ của bạn:
• Giúp người dùng tìm chuyến bay phù hợp
• Hỗ trợ đặt vé, quản lý bookings
• Tư vấn lịch trình, thời tiết, visa
• Trả lời các câu hỏi liên quan đến du lịch

Quy tắc:
• Trả lời bằng tiếng Việt (trừ khi được yêu cầu ngôn ngữ khác)
• Ngắn gọn, thân thiện, dễ hiểu
• Nếu thiếu thông tin, hỏi lại lịch sự
• Sử dụng emoji phù hợp để tăng trải nghiệm 🛫"""


# ── Factory ─────────────────────────────────────────────────────────────────


def _build_gemini_llm(config: LLMConfig) -> BaseChatModel:
    """Build a Gemini chat model from langchain-google-genai."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = config.api_key or settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError(
            "Gemini API key chưa được cấu hình. "
            "Vui lòng thêm API key trong cài đặt LLM."
        )

    return ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=api_key,
        temperature=config.temperature,
        max_output_tokens=int(config.max_tokens) if config.max_tokens else 2048,
        convert_system_message_to_human=True,
    )


def _build_ollama_llm(config: LLMConfig) -> BaseChatModel:
    """Build an Ollama chat model from langchain-ollama."""
    from langchain_ollama import ChatOllama

    base_url = config.base_url or "http://localhost:11434"

    return ChatOllama(
        model=config.model_name,
        base_url=base_url,
        temperature=config.temperature,
        num_predict=int(config.max_tokens) if config.max_tokens else 2048,
    )


def _build_nvidia_llm(config: LLMConfig) -> BaseChatModel:
    """Build an NVIDIA NIM chat model via OpenAI-compatible endpoint."""
    from langchain_openai import ChatOpenAI

    api_key = config.api_key or settings.NVIDIA_API_KEY
    if not api_key:
        raise ValueError(
            "NVIDIA API key chưa được cấu hình. "
            "Vui lòng thêm API key trong cài đặt LLM."
        )

    base_url = config.base_url or settings.NVIDIA_BASE_URL

    return ChatOpenAI(
        model=config.model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=config.temperature,
        max_tokens=int(config.max_tokens) if config.max_tokens else 512,
    )


def build_llm(config: LLMConfig) -> BaseChatModel:
    """Build the appropriate LLM based on provider."""
    if config.provider == "gemini":
        return _build_gemini_llm(config)
    elif config.provider == "ollama":
        return _build_ollama_llm(config)
    elif config.provider == "nvidia":
        return _build_nvidia_llm(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


# ── Retry helper ────────────────────────────────────────────────────────────


async def _invoke_with_retry(
    llm: BaseChatModel,
    messages: list,
    *,
    max_retries: int = MAX_RETRIES,
) -> str:
    """
    Invoke the LLM with exponential-backoff retry for transient errors.

    Only retries on network / rate-limit / timeout errors.
    Non-retryable errors (auth, bad request) are raised immediately.
    """
    last_exc: Exception | None = None
    backoff = INITIAL_BACKOFF_S

    for attempt in range(1 + max_retries):
        try:
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries and _is_retryable(exc):
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{1 + max_retries}), "
                    f"retrying in {backoff:.1f}s: {exc}"
                )
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
            else:
                # Non-retryable or final attempt
                break

    raise last_exc  # type: ignore[misc]


# ── Main entry point ───────────────────────────────────────────────────────


async def generate_chat_response(
    db: AsyncSession,
    user_id: UUID | None,
    conversation_messages: list[dict],
) -> str:
    """
    Generate an AI response with rate-limiting, retry, and fallback.

    Protection layers:
      1. Rate limit check → reject early if user is spamming
      2. Build LLM → fail-fast if config is bad
      3. Invoke with retry → exponential backoff for transient errors
      4. Fallback → friendly error if all retries fail

    Parameters
    ----------
    db : AsyncSession
    user_id : UUID | None
    conversation_messages : list[dict]
        [{"role": "user"|"assistant"|"system", "content": str}, ...]

    Returns
    -------
    str – AI response text or error message.
    """

    # ── 1. Rate limit guard ──────────────────────────────────────────────
    try:
        await llm_rate_limiter.check_rate_limit(user_id)
    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for user {user_id}: {e.message}")
        return e.message

    # ── 2. Resolve LLM config ────────────────────────────────────────────
    config = await _resolve_config(db, user_id)

    # ── 3. Build LLM instance ───────────────────────────────────────────
    try:
        llm = build_llm(config)
    except Exception as e:
        logger.error(f"Failed to build LLM: {e}")
        return (
            "⚠️ Không thể khởi tạo mô hình AI. "
            "Vui lòng kiểm tra cài đặt LLM trong phần Settings.\n\n"
            f"Chi tiết: {e}"
        )

    # ── 4. Build LangChain messages ─────────────────────────────────────
    lc_messages = _build_lc_messages(conversation_messages)

    # ── 5. Invoke with retry + fallback ──────────────────────────────────
    try:
        response_text = await _invoke_with_retry(llm, lc_messages)

        # Record successful call for rate limiting
        llm_rate_limiter.record_call(user_id)

        return response_text

    except Exception as e:
        logger.error(
            f"LLM invocation failed after retries "
            f"(provider={config.provider}, model={config.model_name}): {e}"
        )
        return _format_error(config, e)


async def stream_chat_response(
    db: AsyncSession,
    user_id: UUID | None,
    conversation_messages: list[dict],
):
    """
    Stream an AI response token-by-token via async generator.

    Yields str chunks as they arrive from the LLM.
    Same rate-limit / fallback protections as generate_chat_response.
    """

    # ── 1. Rate limit guard ──────────────────────────────────────────────
    try:
        await llm_rate_limiter.check_rate_limit(user_id)
    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for user {user_id}: {e.message}")
        yield e.message
        return

    # ── 2. Resolve config + build LLM ───────────────────────────────────
    config = await _resolve_config(db, user_id)

    try:
        llm = build_llm(config)
    except Exception as e:
        logger.error(f"Failed to build LLM: {e}")
        yield (
            "⚠️ Không thể khởi tạo mô hình AI. "
            "Vui lòng kiểm tra cài đặt LLM trong phần Settings."
        )
        return

    # ── 3. Build messages ───────────────────────────────────────────────
    lc_messages = _build_lc_messages(conversation_messages)

    # ── 4. Stream with retry ────────────────────────────────────────────
    last_exc: Exception | None = None
    backoff = INITIAL_BACKOFF_S

    for attempt in range(1 + MAX_RETRIES):
        try:
            async for chunk in llm.astream(lc_messages):
                text = chunk.content if hasattr(chunk, "content") else str(chunk)
                if text:
                    yield text

            # Record success
            llm_rate_limiter.record_call(user_id)
            return  # Success – exit the retry loop

        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                logger.warning(
                    f"LLM stream failed (attempt {attempt + 1}/{1 + MAX_RETRIES}), "
                    f"retrying in {backoff:.1f}s: {exc}"
                )
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
            else:
                break

    # All retries exhausted
    logger.error(f"LLM stream failed after retries: {last_exc}")
    yield _format_error(config, last_exc)


# ── Shared helpers ──────────────────────────────────────────────────────────


async def _resolve_config(db: AsyncSession, user_id: UUID | None) -> LLMConfig:
    """Load user config or build a default in-memory config."""
    config: LLMConfig | None = None
    if user_id:
        config = await get_llm_config(db, user_id)

    if config is None:
        config = LLMConfig(
            provider="gemini",
            model_name=settings.GEMINI_MODEL_NAME,
            api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            max_tokens=2048,
        )
    return config


def _build_lc_messages(conversation_messages: list[dict]) -> list:
    """Convert raw dict messages to LangChain message objects."""
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for msg in conversation_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))

    return lc_messages


def _format_error(config: LLMConfig, exc: Exception | None) -> str:
    """Return a user-friendly error message based on exception type."""
    error_str = str(exc).lower() if exc else ""

    if "api key" in error_str or "unauthorized" in error_str:
        return (
            "🔑 API key không hợp lệ hoặc đã hết hạn. "
            "Vui lòng cập nhật API key trong Settings → LLM."
        )
    elif "quota" in error_str or "rate" in error_str:
        return (
            "⏳ Mô hình AI đang quá tải (rate limit từ nhà cung cấp). "
            "Vui lòng thử lại sau vài phút hoặc chuyển sang mô hình khác."
        )
    elif "connection" in error_str or "timeout" in error_str:
        return (
            "🔌 Không thể kết nối tới mô hình AI. "
            "Nếu dùng Ollama, hãy đảm bảo Ollama đang chạy trên máy."
        )
    else:
        return (
            f"⚠️ Lỗi khi gọi mô hình AI ({config.provider}/{config.model_name}).\n\n"
            f"Chi tiết: {str(exc)}\n\n"
            "Hãy kiểm tra lại cài đặt LLM hoặc thử mô hình khác."
        )

