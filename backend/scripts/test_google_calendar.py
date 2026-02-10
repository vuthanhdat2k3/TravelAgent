"""
Test script for Google Calendar integration.
Gets tokens from database and creates a test event.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.core.config import settings
from app.core.google_calendar_client import get_google_calendar_client


async def test_calendar_integration():
    """Test Google Calendar API integration."""
    
    print("🧪 Testing Google Calendar Integration\n")
    
    # Create database connection - convert to asyncpg if needed
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first user with Google Calendar credentials
        result = await db.execute(
            select(User).where(User.metadata_.isnot(None))
        )
        users = result.scalars().all()
        
        user = None
        for u in users:
            if u.metadata_ and 'google_calendar' in u.metadata_:
                google_tokens = u.metadata_['google_calendar']
                if google_tokens.get('access_token') and google_tokens.get('refresh_token'):
                    user = u
                    break
        
        if not user:
            print("❌ Không tìm thấy user nào có Google Calendar credentials")
            print("\n💡 Để test, user cần authorize Google Calendar trước:")
            print("   1. Call GET /api/google-calendar/auth/url")
            print("   2. Redirect user đến authorization_url")
            print("   3. User authorize → tokens được lưu vào user.metadata_")
            print("\n📋 Hoặc kiểm tra database:")
            print("   SELECT email, metadata_->'google_calendar' FROM users WHERE metadata_ IS NOT NULL;")
            await engine.dispose()
            return
        
        print(f"✅ Tìm thấy user: {user.email} (ID: {user.id})")
        
        google_tokens = user.metadata_['google_calendar']
        access_token = google_tokens.get('access_token')
        refresh_token = google_tokens.get('refresh_token')
        
        print(f"🔑 Access token: {access_token[:30]}..." if access_token else "❌ No access token")
        print(f"🔑 Refresh token: {refresh_token[:30]}..." if refresh_token else "❌ No refresh token")
        
        if not access_token or not refresh_token:
            print("\n❌ Tokens không hợp lệ. User cần authorize lại.")
            await engine.dispose()
            return
        
        try:
            # Create Google Calendar client
            print("\n📅 Đang tạo Google Calendar client...")
            calendar_client = get_google_calendar_client(
                access_token=access_token,
                refresh_token=refresh_token
            )
            print("✅ Client được tạo thành công")
            
            # Create test event
            print("\n📅 Đang tạo test event...")
            
            departure_time = datetime.now() + timedelta(days=7)
            arrival_time = departure_time + timedelta(hours=2)
            
            event_id = calendar_client.create_flight_event(
                booking_reference="TEST123",
                origin="HAN",
                destination="SGN",
                departure_time=departure_time,
                arrival_time=arrival_time,
                airline_code="VJ",
                flight_number="197",
                passenger_name="Test User",
                calendar_id="primary"
            )
            
            print(f"\n✅ Event được tạo thành công!")
            print(f"📌 Event ID: {event_id}")
            print(f"🔗 Xem event tại: https://calendar.google.com/calendar/")
            print(f"\n📅 Chi tiết event:")
            print(f"   - Ngày bay: {departure_time.strftime('%d/%m/%Y %H:%M')}")
            print(f"   - Chuyến bay: VJ197 (HAN → SGN)")
            print(f"   - Hành khách: Test User")
            
            # Ask if user wants to delete test event
            print("\n🧹 Để xóa test event, uncomment dòng dưới trong code")
            # calendar_client.delete_event(event_id)
            # print("✅ Test event đã được xóa")
            
            print("\n🎉 Test thành công!")
            
        except Exception as e:
            print(f"\n❌ Lỗi khi tạo event: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            
            import traceback
            print("\n📋 Full traceback:")
            traceback.print_exc()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_calendar_integration())
