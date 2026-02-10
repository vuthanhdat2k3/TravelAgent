"""
Check all database tables and their usage.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.passenger import Passenger
from app.models.flight_search import FlightSearch
from app.models.flight_offer_cache import FlightOfferCache
from app.models.booking import Booking
from app.models.booking_flight import BookingFlight
from app.models.payment import Payment
from app.models.calendar_event import CalendarEvent
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.models.notification_log import NotificationLog
from app.models.llm_config import LLMConfig


async def main():
    """Check database tables."""
    
    print("🔍 Kiểm tra Database Tables\n")
    print("="*80)
    
    # Get database connection
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    tables = [
        ("users", User, "Core - User accounts"),
        ("user_preferences", UserPreference, "User flight preferences (seat, meal, class)"),
        ("passengers", Passenger, "Passenger profiles for bookings"),
        ("flight_searches", FlightSearch, "Search history (for analytics)"),
        ("flight_offer_cache", FlightOfferCache, "Cached flight offers (TTL 30min)"),
        ("bookings", Booking, "Flight bookings"),
        ("booking_flights", BookingFlight, "Flight details per booking"),
        ("payments", Payment, "Payment records"),
        ("calendar_events", CalendarEvent, "Google Calendar sync records"),
        ("conversations", Conversation, "Chat conversations"),
        ("conversation_messages", ConversationMessage, "Chat messages"),
        ("notification_logs", NotificationLog, "Email/SMS notification logs"),
        ("llm_configs", LLMConfig, "LLM configuration (admin)"),
    ]
    
    async with async_session() as db:
        for table_name, model, description in tables:
            try:
                result = await db.execute(
                    select(func.count()).select_from(model)
                )
                count = result.scalar()
                
                # Check recent activity (last 7 days)
                if hasattr(model, 'created_at'):
                    recent_result = await db.execute(
                        select(func.count()).select_from(model)
                        .where(model.created_at >= func.now() - text("interval '7 days'"))
                    )
                    recent_count = recent_result.scalar()
                    activity = f"({recent_count} trong 7 ngày gần đây)" if recent_count > 0 else "(không có hoạt động gần đây)"
                else:
                    activity = ""
                
                status = "✅" if count > 0 else "⚪"
                print(f"{status} {table_name:25} | {count:6} rows {activity}")
                print(f"   📝 {description}")
                print()
                
            except Exception as e:
                print(f"❌ {table_name:25} | ERROR: {e}")
                print()
    
    print("="*80)
    print("\n📊 Tóm tắt:")
    print("   ✅ = Table có dữ liệu")
    print("   ⚪ = Table trống (có thể chưa dùng hoặc mới tạo)")
    print("\n💡 Gợi ý:")
    print("   • flight_offer_cache: Nên clean up định kỳ (đã có TTL 30min)")
    print("   • flight_searches: Có thể archive sau 30 ngày nếu quá nhiều")
    print("   • conversation_messages: Có thể archive chat cũ sau 90 ngày")
    print("   • notification_logs: Có thể clean up sau 30 ngày")
    print("\n🔍 Tất cả tables đều cần thiết cho hệ thống!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
