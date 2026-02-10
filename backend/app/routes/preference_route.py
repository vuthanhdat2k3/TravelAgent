from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_preference import (
    UserPreferenceCreate,
    UserPreferenceUpdate,
    UserPreferenceResponse
)
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.user_preference_service import (
    get_user_preference,
    create_or_update_preference
)

router = APIRouter(prefix="/users/me/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferenceResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user preferences."""
    preference = await get_user_preference(db, current_user.id)
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found"
        )
    
    return UserPreferenceResponse.model_validate(preference)


@router.put("", response_model=UserPreferenceResponse)
async def upsert_preferences(
    preference_data: UserPreferenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update user preferences (upsert)."""
    return await create_or_update_preference(db, current_user.id, preference_data)


@router.patch("", response_model=UserPreferenceResponse)
async def update_preferences(
    preference_data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences (partial update)."""
    return await create_or_update_preference(db, current_user.id, preference_data)
