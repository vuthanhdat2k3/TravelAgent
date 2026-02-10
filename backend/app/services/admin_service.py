from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse


async def get_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    is_active: bool | None = None,
    search: str | None = None
) -> tuple[list[User], int]:
    """Get list of all users (admin only)."""
    query = select(User)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    if search:
        search_filter = User.email.ilike(f"%{search}%") | (
            User.full_name.ilike(f"%{search}%") if User.full_name else False
        )
        query = query.where(search_filter)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()
    
    return list(users), total


async def get_user_by_id_admin(
    db: AsyncSession,
    user_id: UUID
) -> User | None:
    """Get any user by ID (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user_admin(
    db: AsyncSession,
    user_id: UUID,
    user_update: UserUpdate
) -> UserResponse:
    """Update any user (admin only). Can update is_active."""
    db_user = await get_user_by_id_admin(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    
    return UserResponse.model_validate(db_user)
