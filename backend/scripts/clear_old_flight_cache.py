"""
Script để xóa cache cũ không có flight_numbers.
Chạy script này sau khi migration để đảm bảo chỉ có cache mới.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.models.flight_offer_cache import FlightOfferCache
from sqlalchemy import delete


async def clear_old_cache():
    """Delete cache entries without flight_numbers."""
    async with AsyncSessionLocal() as db:
        # Delete entries where flight_numbers is NULL
        result = await db.execute(
            delete(FlightOfferCache).where(FlightOfferCache.flight_numbers == None)
        )
        await db.commit()
        
        deleted_count = result.rowcount
        print(f"✅ Đã xóa {deleted_count} cache entries cũ (không có flight_numbers)")
        
        if deleted_count > 0:
            print("ℹ️  Vui lòng search lại để tạo cache mới với flight_numbers")


if __name__ == "__main__":
    print("🧹 Đang xóa cache cũ...")
    asyncio.run(clear_old_cache())
    print("✅ Hoàn tất!")
