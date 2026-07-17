"""Redis-реализация хранилища."""

from __future__ import annotations

import time
from typing import Any, cast

import redis.asyncio as redis
import structlog

from .base import AbstractStorage

logger = structlog.get_logger()

SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local member = ARGV[3]
local max_events = tonumber(ARGV[4])

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
redis.call('ZADD', key, now, member)

local count = redis.call('ZCOUNT', key, now - window, now)

redis.call('EXPIRE', key, math.ceil(window * 2))

if count > max_events then
    redis.call('ZREM', key, member)
    return {-count}
end
return {count}
"""

TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local burst = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

if tokens == nil then
    tokens = burst
    last_refill = now
end

local elapsed = math.max(now - last_refill, 0)
local refill = elapsed * rate
tokens = math.min(tokens + refill, burst)
last_refill = now

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, math.ceil(burst / rate) + 10)
    return {1, math.floor(tokens)}
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    return {0, math.floor(tokens)}
end
"""


class RedisStorage(AbstractStorage):
    """Redis-бекенд для BotShield."""

    def __init__(self, redis_url: str, key_prefix: str = "botshield") -> None:
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._client: redis.Redis | None = None
        self._sliding_window_sha: str | None = None
        self._token_bucket_sha: str | None = None
        self._sliding_counter: int = 0

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError(
                "Storage not connected. Call await storage.connect() first."
            )
        return self._client

    def _key(self, *parts: str) -> str:
        return f"{self._key_prefix}:{':'.join(parts)}"

    def _require_sha(self, sha: str | None, name: str) -> str:
        if sha is None:
            raise RuntimeError("Storage not connected")
        return sha

    async def connect(self) -> None:
        self._client = redis.from_url(self._redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        await self._client.ping()
        self._sliding_window_sha = cast(
            str, await self._client.script_load(SLIDING_WINDOW_SCRIPT)
        )
        self._token_bucket_sha = cast(
            str, await self._client.script_load(TOKEN_BUCKET_SCRIPT)
        )
        logger.info("redis_connected", url=self._redis_url)

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("redis_disconnected")

    async def increment(self, key: str, window_seconds: float) -> int:
        now = time.time()
        await self.client.zremrangebyscore(key, "-inf", now - window_seconds)
        await self.client.zadd(key, {str(now): now})
        return cast(int, await self.client.zcount(key, now - window_seconds, now))

    async def get_count(self, key: str, window_seconds: float) -> int:
        now = time.time()
        return cast(int, await self.client.zcount(key, now - window_seconds, now))

    async def add_to_sorted_set(self, key: str, score: float, member: str) -> None:
        await self.client.zadd(key, {member: score})

    async def count_sorted_set(
        self, key: str, min_score: float, max_score: float
    ) -> int:
        return cast(int, await self.client.zcount(key, min_score, max_score))

    async def remove_sorted_set_below(self, key: str, min_score: float) -> int:
        return cast(int, await self.client.zremrangebyscore(key, "-inf", min_score))

    async def get(self, key: str) -> str | None:
        return cast(str | None, await self.client.get(key))

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if ttl is not None:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)

    async def eval_lua(self, script: str, keys: int, *args: str) -> list[Any]:
        raw = await self.client.eval(script, keys, *args)  # type: ignore[misc]
        return cast(list[Any], raw)

    async def check_sliding_window(
        self,
        user_id: int,
        window_seconds: float,
        max_events: int,
        event_type: str = "msg",
    ) -> tuple[int, bool]:
        now = time.time()
        self._sliding_counter += 1
        key = self._key("sw", str(user_id), event_type)
        member = f"{now}:{self._sliding_counter}"

        sha = self._require_sha(self._sliding_window_sha, "sliding_window")
        raw = await self.client.evalsha(  # type: ignore[misc]
            sha, 1, key,
            str(now), str(window_seconds), member, str(max_events),
        )
        result = cast(list[Any], raw)
        count = abs(int(result[0]))
        blocked = int(result[0]) < 0
        return count, blocked

    async def check_token_bucket(
        self,
        user_id: int,
        rate: float,
        burst: int,
        tokens_requested: int = 1,
    ) -> tuple[bool, int]:
        now = time.time()
        key = self._key("tb", str(user_id))

        sha = self._require_sha(self._token_bucket_sha, "token_bucket")
        raw = await self.client.evalsha(  # type: ignore[misc]
            sha, 1, key,
            str(now), str(rate), str(burst), str(tokens_requested),
        )
        result = cast(list[Any], raw)
        allowed = bool(int(result[0]))
        tokens_left = int(result[1])
        return allowed, tokens_left
