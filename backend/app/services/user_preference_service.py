from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user_preference import UserPreference
from app.models.passenger import Passenger
from app.schemas.user_preference import (
    UserPreferenceCreate,
    UserPreferenceUpdate,
    UserPreferenceResponse
)


async def get_user_preference(
    db: AsyncSession,
    user_id: UUID
) -> UserPreference | None:
    """Get user preference by user_id."""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_preference(
    db: AsyncSession,
    user_id: UUID,
    preference_data: UserPreferenceCreate | UserPreferenceUpdate
) -> UserPreferenceResponse:
    """
    Create or update user preference (upsert).
    Validates default_passenger_id belongs to user.
    """
    # If default_passenger_id is provided, verify it belongs to user
    if hasattr(preference_data, 'default_passenger_id') and preference_data.default_passenger_id:
        passenger_result = await db.execute(
            select(Passenger).where(
                Passenger.id == preference_data.default_passenger_id,
                Passenger.user_id == user_id
            )
        )
        passenger = passenger_result.scalar_one_or_none()
        
        if not passenger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default passenger not found or does not belong to user"
            )
    
    # Check if preference already exists
    existing_pref = await get_user_preference(db, user_id)
    
    if existing_pref:
        # Update existing preference
        update_data = preference_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_pref, field, value)
        
        await db.commit()
        await db.refresh(existing_pref)
        
        return UserPreferenceResponse.model_validate(existing_pref)
    else:
        # Create new preference
        db_preference = UserPreference(
            user_id=user_id,
            **preference_data.model_dump(exclude_unset=True)
        )
        
        db.add(db_preference)
        await db.commit()
        await db.refresh(db_preference)
        
        return UserPreferenceResponse.model_validate(db_preference)
