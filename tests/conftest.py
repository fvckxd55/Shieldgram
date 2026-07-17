"""Shared test fixtures for Shieldgram."""

from __future__ import annotations

import pytest
from fakeredis import aioredis

from shieldgram.config import FloodDetectorConfig, RateLimiterConfig, ShieldConfig
from shieldgram.storage.redis import SLIDING_WINDOW_SCRIPT, TOKEN_BUCKET_SCRIPT, RedisStorage


@pytest.fixture
async def redis_storage() -> RedisStorage:
    fake_redis = aioredis.FakeRedis(decode_responses=True)
    storage = RedisStorage(redis_url="redis://localhost:6379/0", key_prefix="shieldgram_test")
    storage._client = fake_redis
    storage._sliding_window_sha = await fake_redis.script_load(SLIDING_WINDOW_SCRIPT)
    storage._token_bucket_sha = await fake_redis.script_load(TOKEN_BUCKET_SCRIPT)
    return storage


@pytest.fixture
def rate_limiter_config() -> RateLimiterConfig:
    return RateLimiterConfig(
        sliding_window_seconds=10.0,
        max_requests_per_window=5,
        token_bucket_rate=2.0,
        token_bucket_burst=3,
    )


@pytest.fixture
def flood_config() -> FloodDetectorConfig:
    return FloodDetectorConfig(
        burst_window_seconds=3.0,
        burst_threshold=5,
        repeat_window_seconds=10.0,
        repeat_threshold=3,
    )


@pytest.fixture
def shield_config() -> ShieldConfig:
    return ShieldConfig(
        redis_url="redis://localhost:6379/0",
        rate_limiter=RateLimiterConfig(
            sliding_window_seconds=10.0,
            max_requests_per_window=5,
        ),
        flood_detector=FloodDetectorConfig(
            burst_window_seconds=3.0,
            burst_threshold=5,
        ),
    )
