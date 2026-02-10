"""Service for LLM configuration CRUD operations."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.llm_config import LLMConfig
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    AvailableModel,
    AvailableModelsResponse,
)

# ── Available models registry ──────────────────────────────────────────────

AVAILABLE_MODELS: list[AvailableModel] = [
    # Gemini models
    AvailableModel(
        provider="gemini",
        model_name="gemini-2.0-flash-lite",
        display_name="Gemini 2.0 Flash Lite",
        description="Mô hình nhanh và hiệu quả, phù hợp cho hầu hết các tác vụ.",
    ),
    AvailableModel(
        provider="gemini",
        model_name="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        description="Mô hình nhanh và hiệu quả, phù hợp cho hầu hết các tác vụ.",
    ),
    AvailableModel(
        provider="gemini",
        model_name="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash Lite",
        description="Phiên bản mới nhất với khả năng suy luận tốt hơn.",
    ),
    AvailableModel(
        provider="gemini",
        model_name="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        description="Mô hình mạnh nhất của Google, xuất sắc trong suy luận phức tạp.",
    ),
    AvailableModel(
        provider="gemini",
        model_name="gemini-2.5-flash-pro",
        display_name="Gemini 2.5 Flash Pro",
        description="Mô hình mạnh nhất của Google, xuất sắc trong suy luận phức tạp.",
    ),
    AvailableModel(
        provider="gemini",
        model_name="gemini-2.5-flash-pro-preview",
        display_name="Gemini 2.5 Flash Pro Preview",
        description="Mô hình mạnh nhất của Google, xuất sắc trong suy luận phức tạp.",
    ),
    # Ollama local models
    AvailableModel(
        provider="ollama",
        model_name="llama3.1:8b",
        display_name="Llama 3.1 8B",
        description="Mô hình mã nguồn mở 8B tham số, chạy cục bộ qua Ollama.",
    ),
    AvailableModel(
        provider="ollama",
        model_name="llama3.2:3b",
        display_name="Llama 3.2 3B",
        description="Mô hình nhẹ 3B, phản hồi nhanh cho máy cấu hình thấp.",
    ),
    AvailableModel(
        provider="ollama",
        model_name="qwen2.5:7b",
        display_name="Qwen 2.5 7B",
        description="Mô hình mã nguồn mở 7B từ Alibaba, hỗ trợ tiếng Việt tốt.",
    ),
    AvailableModel(
        provider="ollama",
        model_name="mistral:7b",
        display_name="Mistral 7B",
        description="Mô hình mã nguồn mở 7B hiệu quả từ Mistral AI.",
    ),
    AvailableModel(
        provider="ollama",
        model_name="gemma2:9b",
        display_name="Gemma 2 9B",
        description="Mô hình mã nguồn mở 9B từ Google DeepMind.",
    ),
    AvailableModel(
        provider="ollama",
        model_name="phi3:mini",
        display_name="Phi 3 Mini",
        description="Mô hình mã nguồn mở nhỏ gọn từ Google DeepMind.",
    ),
    # NVIDIA NIM models
    AvailableModel(
        provider="nvidia",
        model_name="meta/llama-4-maverick-17b-128e-instruct",
        display_name="Llama 4 Maverick 17B",
        description="Meta Llama 4 Maverick 17B-128E qua NVIDIA NIM API, suy luận mạnh mẽ.",
    ),
]


def get_available_models() -> AvailableModelsResponse:
    """Return list of all available LLM models."""
    return AvailableModelsResponse(models=AVAILABLE_MODELS)


# ── CRUD ────────────────────────────────────────────────────────────────────


async def get_llm_config(db: AsyncSession, user_id: UUID) -> LLMConfig | None:
    """Get the LLM config for a user."""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_llm_config_response(db: AsyncSession, user_id: UUID) -> LLMConfigResponse | None:
    """Get the LLM config response (with api_key_set flag)."""
    config = await get_llm_config(db, user_id)
    if not config:
        return None
    return _to_response(config)


async def create_or_update_llm_config(
    db: AsyncSession,
    user_id: UUID,
    data: LLMConfigCreate,
) -> LLMConfigResponse:
    """Create or update LLM config for a user (upsert)."""
    existing = await get_llm_config(db, user_id)

    if existing:
        existing.provider = data.provider.value
        existing.model_name = data.model_name
        if data.api_key is not None:
            existing.api_key = data.api_key
        existing.base_url = data.base_url
        existing.temperature = data.temperature
        existing.max_tokens = data.max_tokens
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return _to_response(existing)
    else:
        new_config = LLMConfig(
            user_id=user_id,
            provider=data.provider.value,
            model_name=data.model_name,
            api_key=data.api_key,
            base_url=data.base_url,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            is_active=True,
        )
        db.add(new_config)
        await db.commit()
        await db.refresh(new_config)
        return _to_response(new_config)


async def update_llm_config(
    db: AsyncSession,
    user_id: UUID,
    data: LLMConfigUpdate,
) -> LLMConfigResponse:
    """Partially update LLM config."""
    config = await get_llm_config(db, user_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found. Create one first.",
        )

    update_data = data.model_dump(exclude_unset=True)
    if "provider" in update_data and update_data["provider"] is not None:
        update_data["provider"] = update_data["provider"].value

    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return _to_response(config)


async def delete_llm_config(db: AsyncSession, user_id: UUID) -> None:
    """Delete LLM config for a user."""
    config = await get_llm_config(db, user_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found.",
        )
    await db.delete(config)
    await db.commit()


# ── Helpers ─────────────────────────────────────────────────────────────────


def _to_response(config: LLMConfig) -> LLMConfigResponse:
    """Convert model to response schema, masking the API key."""
    return LLMConfigResponse(
        id=config.id,
        user_id=config.user_id,
        provider=config.provider,
        model_name=config.model_name,
        api_key_set=bool(config.api_key),
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )
