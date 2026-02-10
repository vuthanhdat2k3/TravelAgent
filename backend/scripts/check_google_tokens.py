"""
Check if users have Google Calendar tokens in database.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.core.config import settings


async def main():
    """Check users' Google Calendar credentials."""
    
    # Create database connection
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"📊 Tìm thấy {len(users)} users trong database\n")
        
        for user in users:
            print(f"👤 {user.email} (ID: {user.id})")
            
            if user.metadata_:
                if 'google_calendar' in user.metadata_:
                    tokens = user.metadata_['google_calendar']
                    has_access = bool(tokens.get('access_token'))
                    has_refresh = bool(tokens.get('refresh_token'))
                    
                    if has_access and has_refresh:
                        print(f"   ✅ Google Calendar: CONNECTED")
                        print(f"   🔑 Access token: {tokens['access_token'][:30]}...")
                        print(f"   🔑 Refresh token: {tokens['refresh_token'][:30]}...")
                    else:
                        print(f"   ⚠️  Google Calendar: INCOMPLETE (missing tokens)")
                else:
                    print(f"   ❌ Google Calendar: NOT CONNECTED")
            else:
                print(f"   ❌ metadata_: NULL")
            
            print()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
