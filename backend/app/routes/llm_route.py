"""API routes for LLM model configuration."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    AvailableModelsResponse,
)
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/llm", tags=["llm-config"])


@router.get("/models", response_model=AvailableModelsResponse)
async def list_available_models():
    """List all supported LLM providers and models."""
    from app.services.llm_config_service import get_available_models

    return get_available_models()


@router.get("/config", response_model=LLMConfigResponse | None)
async def get_my_llm_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's LLM configuration."""
    from app.services.llm_config_service import get_llm_config_response

    return await get_llm_config_response(db, current_user.id)


@router.put("/config", response_model=LLMConfigResponse, status_code=status.HTTP_200_OK)
async def set_llm_config(
    data: LLMConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update LLM configuration for current user."""
    from app.services.llm_config_service import create_or_update_llm_config

    return await create_or_update_llm_config(db, current_user.id, data)


@router.patch("/config", response_model=LLMConfigResponse)
async def update_my_llm_config(
    data: LLMConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Partially update LLM configuration."""
    from app.services.llm_config_service import update_llm_config

    return await update_llm_config(db, current_user.id, data)


@router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_llm_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete LLM configuration (revert to system default)."""
    from app.services.llm_config_service import delete_llm_config

    await delete_llm_config(db, current_user.id)


@router.get("/usage")
async def get_llm_usage_stats(
    current_user: User = Depends(get_current_active_user),
):
    """Get current LLM rate-limit usage stats for the user."""
    from app.llm.rate_limiter import llm_rate_limiter

    return llm_rate_limiter.get_usage_stats(current_user.id)
