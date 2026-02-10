from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_superuser
from app.services.admin_service import (
    get_all_users,
    get_user_by_id_admin,
    update_user_admin
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = 20,
    is_active: bool | None = None,
    q: str | None = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get list of all users (admin only)."""
    users, total = await get_all_users(db, skip, limit, is_active, q)
    
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get user details (admin only)."""
    user = await get_user_by_id_admin(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Update user (admin only). Can update is_active to lock/unlock users."""
    return await update_user_admin(db, user_id, user_update)
