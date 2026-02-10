"""
Clear Google Calendar credentials from a user to test authorization flow.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.core.config import settings


async def main():
    """Clear Google Calendar credentials from user."""
    
    print("🧹 Clear Google Calendar Credentials\n")
    
    # Get database connection
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get users with Google Calendar
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        users_with_calendar = []
        for user in users:
            if user.metadata_ and 'google_calendar' in user.metadata_:
                users_with_calendar.append(user)
        
        if not users_with_calendar:
            print("❌ Không tìm thấy user nào có Google Calendar credentials")
            await engine.dispose()
            return
        
        print("📋 Users có Google Calendar:")
        for i, user in enumerate(users_with_calendar, 1):
            print(f"   {i}. {user.email} (ID: {user.id})")
        
        # Select user
        try:
            choice = int(input(f"\nChọn user để xóa credentials (1-{len(users_with_calendar)}): "))
            if choice < 1 or choice > len(users_with_calendar):
                print("❌ Lựa chọn không hợp lệ")
                await engine.dispose()
                return
            
            selected_user = users_with_calendar[choice - 1]
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cancelled")
            await engine.dispose()
            return
        
        print(f"\n⚠️  Bạn có chắc muốn xóa Google Calendar credentials của {selected_user.email}? (y/n): ", end='')
        confirm = input().strip().lower()
        
        if confirm != 'y':
            print("❌ Cancelled")
            await engine.dispose()
            return
        
        # Remove google_calendar from metadata
        metadata = selected_user.metadata_ or {}
        if 'google_calendar' in metadata:
            del metadata['google_calendar']
        
        await db.execute(
            update(User)
            .where(User.id == selected_user.id)
            .values(metadata_=metadata if metadata else None)
        )
        await db.commit()
        
        print(f"\n✅ Đã xóa Google Calendar credentials của {selected_user.email}")
        print("💡 User này sẽ được yêu cầu authorize lại khi thêm booking vào calendar")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
