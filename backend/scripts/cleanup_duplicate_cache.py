"""
Clean up duplicate flight offer cache entries.
Keeps only the newest entry for each unique offer_id.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.flight_offer_cache import FlightOfferCache
from app.core.config import settings


async def main():
    """Clean up duplicate cache entries."""
    
    print("🧹 Cleaning up duplicate flight offer cache entries\n")
    
    # Get database connection
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Find duplicate offer_ids
        result = await db.execute(
            select(
                FlightOfferCache.offer_id,
                func.count(FlightOfferCache.id).label('count')
            )
            .group_by(FlightOfferCache.offer_id)
            .having(func.count(FlightOfferCache.id) > 1)
        )
        
        duplicates = result.all()
        
        if not duplicates:
            print("✅ Không tìm thấy cache entries trùng lặp")
            await engine.dispose()
            return
        
        print(f"📊 Tìm thấy {len(duplicates)} offer_ids có nhiều cache entries:\n")
        
        total_deleted = 0
        
        for offer_id, count in duplicates:
            print(f"   • offer_id: {offer_id[:20]}... ({count} entries)")
            
            # Get all entries for this offer_id, ordered by created_at DESC
            entries_result = await db.execute(
                select(FlightOfferCache)
                .where(FlightOfferCache.offer_id == offer_id)
                .order_by(FlightOfferCache.created_at.desc())
            )
            entries = entries_result.scalars().all()
            
            # Keep the newest one, delete the rest
            if len(entries) > 1:
                ids_to_delete = [e.id for e in entries[1:]]
                
                await db.execute(
                    delete(FlightOfferCache)
                    .where(FlightOfferCache.id.in_(ids_to_delete))
                )
                
                deleted_count = len(ids_to_delete)
                total_deleted += deleted_count
                print(f"     ✓ Giữ entry mới nhất, xóa {deleted_count} entries cũ")
        
        await db.commit()
        
        print(f"\n✅ Hoàn tất! Đã xóa tổng cộng {total_deleted} cache entries trùng lặp")
        print(f"💡 Từ giờ, code sẽ tự động xóa cache cũ trước khi insert cache mới")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
