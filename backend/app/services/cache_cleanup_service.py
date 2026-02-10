"""
Periodic cleanup service for expired flight offer cache entries.

Runs a background asyncio task every N minutes (configurable, default 7 min)
to delete expired rows from `flight_offer_cache`, preventing DB bloat.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select

from app.db.database import AsyncSessionLocal
from app.models.flight_offer_cache import FlightOfferCache
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (from env / settings, fallback to sensible defaults)
# ---------------------------------------------------------------------------

CLEANUP_INTERVAL_MINUTES: int = settings.CACHE_CLEANUP_INTERVAL_MINUTES   # default 7 min
STALE_THRESHOLD_MINUTES: int = settings.CACHE_STALE_THRESHOLD_MINUTES     # default 30 min
BATCH_SIZE: int = 500                     # Max rows per DELETE to avoid long locks

# ---------------------------------------------------------------------------
# Core cleanup logic
# ---------------------------------------------------------------------------


async def cleanup_expired_offers() -> dict:
    """
    Delete all expired flight offer cache entries.

    Two-phase approach:
      1. Delete rows where ``expires_at < now()`` (normal expiry).
      2. Delete rows where ``created_at < now() - STALE_THRESHOLD`` as a safety
         net for any rows that somehow bypassed the TTL check.

    Returns a summary dict with counts.
    """
    total_deleted = 0
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        try:
            # --- Phase 1: delete expired entries ---
            count_before = await _count_total(db)

            result_expired = await db.execute(
                delete(FlightOfferCache).where(
                    FlightOfferCache.expires_at < now
                )
            )
            expired_count = result_expired.rowcount
            total_deleted += expired_count

            # --- Phase 2: safety cleanup for very old entries ---
            stale_cutoff = now - timedelta(minutes=STALE_THRESHOLD_MINUTES)
            result_stale = await db.execute(
                delete(FlightOfferCache).where(
                    FlightOfferCache.created_at < stale_cutoff
                )
            )
            stale_count = result_stale.rowcount
            total_deleted += stale_count

            await db.commit()

            count_after = await _count_total(db)

            summary = {
                "expired_deleted": expired_count,
                "stale_deleted": stale_count,
                "total_deleted": total_deleted,
                "remaining": count_after,
                "timestamp": now.isoformat(),
            }

            if total_deleted > 0:
                logger.info(
                    f"[CacheCleanup] Removed {total_deleted} entries "
                    f"(expired={expired_count}, stale={stale_count}). "
                    f"Remaining: {count_after}"
                )
            else:
                logger.debug("[CacheCleanup] No expired entries to clean.")

            return summary

        except Exception as exc:
            await db.rollback()
            logger.error(f"[CacheCleanup] Error during cleanup: {exc}", exc_info=True)
            return {"error": str(exc), "total_deleted": 0}


async def get_cache_stats() -> dict:
    """Return current cache statistics (for admin/monitoring)."""
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        total = await _count_total(db)

        # Count expired (still in DB)
        result = await db.execute(
            select(func.count()).select_from(FlightOfferCache).where(
                FlightOfferCache.expires_at < now
            )
        )
        expired = result.scalar() or 0

        # Count active
        active = total - expired

        # Oldest entry
        result = await db.execute(
            select(func.min(FlightOfferCache.created_at))
        )
        oldest = result.scalar()

        return {
            "total_entries": total,
            "active_entries": active,
            "expired_entries": expired,
            "oldest_entry": oldest.isoformat() if oldest else None,
            "cleanup_interval_minutes": CLEANUP_INTERVAL_MINUTES,
            "stale_threshold_minutes": STALE_THRESHOLD_MINUTES,
        }


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

_cleanup_task: asyncio.Task | None = None


async def _cleanup_loop() -> None:
    """Infinite loop that runs cleanup on a fixed interval."""
    logger.info(
        f"[CacheCleanup] Background task started — "
        f"interval={CLEANUP_INTERVAL_MINUTES}min, "
        f"stale_threshold={STALE_THRESHOLD_MINUTES}min"
    )

    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_MINUTES * 60)
            await cleanup_expired_offers()
        except asyncio.CancelledError:
            logger.info("[CacheCleanup] Background task cancelled — shutting down.")
            break
        except Exception as exc:
            logger.error(
                f"[CacheCleanup] Unexpected error in loop: {exc}",
                exc_info=True,
            )
            # Sleep a bit before retrying to avoid tight error loops
            await asyncio.sleep(30)


def start_cleanup_task() -> None:
    """Start the background cleanup task (call once at app startup)."""
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_loop())
        logger.info("[CacheCleanup] Scheduled periodic cache cleanup.")


async def stop_cleanup_task() -> None:
    """Gracefully stop the background cleanup task (call at app shutdown)."""
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("[CacheCleanup] Background task stopped.")
    _cleanup_task = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _count_total(db) -> int:
    result = await db.execute(
        select(func.count()).select_from(FlightOfferCache)
    )
    return result.scalar() or 0
