from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification_log import NotificationLog
from app.schemas.notification import NotificationLogResponse


async def get_notifications(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
    type_filter: str | None = None
) -> list[NotificationLog]:
    """Get notification logs for a user."""
    query = select(NotificationLog).where(NotificationLog.user_id == user_id)
    
    if type_filter:
        query = query.where(NotificationLog.type_ == type_filter)
    
    query = query.offset(skip).limit(limit).order_by(NotificationLog.sent_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    notification_type: str,
    channel: str,
    subject: str,
    ref_id: UUID | None = None,
    metadata: str | None = None
) -> NotificationLog:
    """
    Create and send a notification.
    This is typically called by the Notification Agent, not directly by API.
    """
    # TODO: Actually send notification via email/SMS/push
    # For now, just log it
    
    db_notification = NotificationLog(
        user_id=user_id,
        type_=notification_type,
        channel=channel,
        subject=subject,
        ref_id=ref_id,
        status="SENT",  # or "PENDING", "FAILED"
        metadata=metadata
    )
    
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    
    return db_notification
