from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.notification import NotificationLogResponse
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.notification_service import get_notifications

router = APIRouter(prefix="/users/me/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationLogResponse])
async def list_my_notifications(
    skip: int = 0,
    limit: int = 20,
    type: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notification history for current user."""
    notifications = await get_notifications(db, current_user.id, skip, limit, type)
    return [NotificationLogResponse.model_validate(n) for n in notifications]
