"""Тесты для RateLimiter."""

from __future__ import annotations

import asyncio

from aiogram.types import Chat, Message, User

from botshield.config import RateLimiterConfig
from botshield.detectors.rate_limiter import RateLimiter
from botshield.storage.redis import RedisStorage
from botshield.types import DetectionVerdict


def _make_message(user_id: int, text: str = "test") -> Message:
    return Message(
        message_id=1,
        date=0,
        chat=Chat(id=user_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        text=text,
    )


class TestRateLimiter:
    async def test_allows_low_traffic(
        self, redis_storage: RedisStorage, rate_limiter_config: RateLimiterConfig
    ) -> None:
        config = RateLimiterConfig(
            sliding_window_seconds=60.0,
            max_requests_per_window=5,
            token_bucket_rate=100.0,
            token_bucket_burst=100,
        )
        detector = RateLimiter(redis_storage, config)

        for _ in range(2):
            result = await detector.analyze(_make_message(1), {})
            assert result.verdict == DetectionVerdict.ALLOW
            assert result.score < 0.5

    async def test_warns_then_blocks(
        self, redis_storage: RedisStorage, rate_limiter_config: RateLimiterConfig
    ) -> None:
        config = RateLimiterConfig(
            sliding_window_seconds=60.0,
            max_requests_per_window=5,
            token_bucket_rate=100.0,
            token_bucket_burst=100,
        )
        detector = RateLimiter(redis_storage, config)

        results: list[str] = []
        for i in range(6):
            result = await detector.analyze(_make_message(1, f"msg_{i}"), {})
            results.append(result.verdict.name)
            await asyncio.sleep(0.01)

        assert "WARN" in results
        assert "BLOCK" in results

    async def test_different_users_independent(
        self, redis_storage: RedisStorage, rate_limiter_config: RateLimiterConfig
    ) -> None:
        config = RateLimiterConfig(
            sliding_window_seconds=60.0,
            max_requests_per_window=3,
            token_bucket_rate=100.0,
            token_bucket_burst=100,
        )
        detector = RateLimiter(redis_storage, config)

        for _ in range(3):
            await detector.analyze(_make_message(1), {})

        result = await detector.analyze(_make_message(2), {})
        assert result.verdict == DetectionVerdict.ALLOW

    async def test_disabled_returns_allow(
        self, redis_storage: RedisStorage
    ) -> None:
        config = RateLimiterConfig(enabled=False)
        detector = RateLimiter(redis_storage, config)

        for _ in range(100):
            result = await detector.analyze(_make_message(1), {})
            assert result.verdict == DetectionVerdict.ALLOW

    async def test_token_bucket_limits(
        self, redis_storage: RedisStorage, rate_limiter_config: RateLimiterConfig
    ) -> None:
        config = RateLimiterConfig(
            sliding_window_seconds=60.0,
            max_requests_per_window=100,
            token_bucket_rate=1.0,
            token_bucket_burst=3,
        )
        detector = RateLimiter(redis_storage, config)

        for _ in range(3):
            result = await detector.analyze(_make_message(1), {})
            assert result.verdict == DetectionVerdict.ALLOW

        result = await detector.analyze(_make_message(1), {})
        assert result.score > 0.0
