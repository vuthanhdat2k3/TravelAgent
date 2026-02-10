"""
Per-user sliding-window rate limiter for LLM calls.

Prevents excessive API usage that would burn through tokens/budget.
Uses in-memory storage – suitable for single-instance deployments.
For multi-instance, replace with Redis-backed implementation.
"""

from __future__ import annotations

import asyncio
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from uuid import UUID

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────

# Per-user limits
MAX_REQUESTS_PER_MINUTE = 6      # Max 6 LLM calls per minute per user
MAX_REQUESTS_PER_HOUR = 60       # Max 60 LLM calls per hour per user
MAX_REQUESTS_PER_DAY = 500       # Max 500 LLM calls per day per user

# Global limits (across all users)
GLOBAL_MAX_REQUESTS_PER_MINUTE = 30  # Protect against total API cost blow-up

# Cooldown duration in seconds when rate-limited
COOLDOWN_SECONDS = 10

# ── Rate limit buckets ──────────────────────────────────────────────────────

WINDOW_MINUTE = 60
WINDOW_HOUR = 3600
WINDOW_DAY = 86400


@dataclass
class _UserBucket:
    """Tracks timestamps of LLM calls for a single user."""
    timestamps: list[float] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def _prune(self, window: float) -> None:
        """Remove timestamps outside the window."""
        cutoff = time.monotonic() - window
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    def count_in_window(self, window: float) -> int:
        """Count requests within a time window."""
        self._prune(window)
        return len(self.timestamps)

    def record(self) -> None:
        """Record a new request timestamp."""
        self.timestamps.append(time.monotonic())


class RateLimiter:
    """
    Async-safe, in-memory, per-user + global rate limiter.

    Usage::

        limiter = RateLimiter()
        await limiter.check_rate_limit(user_id)  # raises RateLimitExceeded
        # ... call LLM ...
        limiter.record_call(user_id)
    """

    def __init__(self) -> None:
        self._user_buckets: dict[str, _UserBucket] = defaultdict(_UserBucket)
        self._global_bucket = _UserBucket()
        self._cleanup_counter = 0

    def _get_key(self, user_id: UUID | None) -> str:
        return str(user_id) if user_id else "__anonymous__"

    async def check_rate_limit(self, user_id: UUID | None) -> None:
        """
        Check if the user (or anonymous) is within rate limits.

        Raises
        ------
        RateLimitExceeded
            If any rate limit is exceeded.
        """
        key = self._get_key(user_id)
        bucket = self._user_buckets[key]

        async with bucket.lock:
            # Per-user: per-minute check
            count_min = bucket.count_in_window(WINDOW_MINUTE)
            if count_min >= MAX_REQUESTS_PER_MINUTE:
                wait_time = COOLDOWN_SECONDS
                raise RateLimitExceeded(
                    f"Bạn đã gửi quá {MAX_REQUESTS_PER_MINUTE} tin nhắn trong 1 phút. "
                    f"Vui lòng đợi {wait_time} giây rồi thử lại. ⏳",
                    retry_after=wait_time,
                )

            # Per-user: per-hour check
            count_hour = bucket.count_in_window(WINDOW_HOUR)
            if count_hour >= MAX_REQUESTS_PER_HOUR:
                raise RateLimitExceeded(
                    f"Bạn đã đạt giới hạn {MAX_REQUESTS_PER_HOUR} tin nhắn/giờ. "
                    "Vui lòng quay lại sau. ⏳",
                    retry_after=60,
                )

            # Per-user: per-day check
            count_day = bucket.count_in_window(WINDOW_DAY)
            if count_day >= MAX_REQUESTS_PER_DAY:
                raise RateLimitExceeded(
                    f"Bạn đã đạt giới hạn {MAX_REQUESTS_PER_DAY} tin nhắn/ngày. "
                    "Giới hạn sẽ được reset vào ngày mai. ⏳",
                    retry_after=300,
                )

        # Global rate limit check
        async with self._global_bucket.lock:
            global_count = self._global_bucket.count_in_window(WINDOW_MINUTE)
            if global_count >= GLOBAL_MAX_REQUESTS_PER_MINUTE:
                raise RateLimitExceeded(
                    "Hệ thống đang quá tải. Vui lòng thử lại sau vài giây. 🔄",
                    retry_after=COOLDOWN_SECONDS,
                )

    def record_call(self, user_id: UUID | None) -> None:
        """Record a successful LLM call for rate-limiting tracking."""
        key = self._get_key(user_id)
        self._user_buckets[key].record()
        self._global_bucket.record()

        # Periodic cleanup of stale user buckets (every 100 calls)
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            self._cleanup_stale_buckets()

    def get_usage_stats(self, user_id: UUID | None) -> dict:
        """Get current usage statistics for a user."""
        key = self._get_key(user_id)
        bucket = self._user_buckets[key]
        return {
            "requests_last_minute": bucket.count_in_window(WINDOW_MINUTE),
            "requests_last_hour": bucket.count_in_window(WINDOW_HOUR),
            "requests_last_day": bucket.count_in_window(WINDOW_DAY),
            "limits": {
                "per_minute": MAX_REQUESTS_PER_MINUTE,
                "per_hour": MAX_REQUESTS_PER_HOUR,
                "per_day": MAX_REQUESTS_PER_DAY,
            },
        }

    def _cleanup_stale_buckets(self) -> None:
        """Remove user buckets with no recent activity (older than 1 day)."""
        stale_keys = []
        for key, bucket in self._user_buckets.items():
            if bucket.count_in_window(WINDOW_DAY) == 0:
                stale_keys.append(key)
        for key in stale_keys:
            del self._user_buckets[key]
        if stale_keys:
            logger.debug(f"Cleaned up {len(stale_keys)} stale rate-limit buckets.")


class RateLimitExceeded(Exception):
    """Raised when a user exceeds the LLM call rate limit."""

    def __init__(self, message: str, retry_after: int = COOLDOWN_SECONDS):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


# ── Singleton instance ──────────────────────────────────────────────────────

llm_rate_limiter = RateLimiter()
