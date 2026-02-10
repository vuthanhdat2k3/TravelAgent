"""
Generate OAuth URL with user_id directly from database.
Use this for testing without needing JWT token.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User


async def main():
    """Generate OAuth URL for a specific user."""
    
    print("🔐 Google Calendar OAuth - Generate URL\n")
    
    # Get database connection
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("❌ Không tìm thấy user nào trong database")
            await engine.dispose()
            return
        
        print("📋 Danh sách users:")
        for i, user in enumerate(users, 1):
            print(f"   {i}. {user.email} (ID: {user.id})")
        
        # Select user
        try:
            choice = int(input(f"\nChọn user (1-{len(users)}): "))
            if choice < 1 or choice > len(users):
                print("❌ Lựa chọn không hợp lệ")
                await engine.dispose()
                return
            
            selected_user = users[choice - 1]
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cancelled")
            await engine.dispose()
            return
        
        print(f"\n✅ Đã chọn: {selected_user.email}")
        
        # Generate OAuth URL
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        if not client_id or not client_secret:
            print("❌ Missing Google OAuth credentials in .env")
            await engine.dispose()
            return
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uris": [redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=['https://www.googleapis.com/auth/calendar'],
                redirect_uri=redirect_uri
            )
            
            # Generate URL with user_id as state
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                prompt='consent',
                state=str(selected_user.id)  # User ID as state
            )
            
            print("\n" + "=" * 80)
            print("📋 AUTHORIZATION URL:")
            print("=" * 80)
            print(authorization_url)
            print("=" * 80)
            
            print(f"\n🔑 State (User ID): {state}")
            print("\n📝 Hướng dẫn:")
            print("   1. Copy URL trên và paste vào browser")
            print("   2. Đăng nhập Google account")
            print("   3. Click 'Allow'")
            print("   4. Sau khi authorize, tokens sẽ được lưu cho user:", selected_user.email)
            print("\n⚠️  Đảm bảo backend đang chạy tại http://localhost:8000")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
