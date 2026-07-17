"""Тесты для ReputationEngine."""

from __future__ import annotations

from shieldgram.reputation.engine import ReputationEngine
from shieldgram.storage.redis import RedisStorage


class TestReputationEngine:
    async def test_new_user_starts_clean(self, redis_storage: RedisStorage) -> None:
        engine = ReputationEngine(redis_storage)
        score = await engine.get_reputation(999)
        assert score == 0.0

    async def test_penalty_increases_score(self, redis_storage: RedisStorage) -> None:
        engine = ReputationEngine(redis_storage, penalty=0.2)
        new_score = await engine.apply_penalty(1, 1.0)
        assert new_score == 0.2

        new_score = await engine.apply_penalty(1, 1.0)
        assert new_score == 0.4

    async def test_score_capped_at_one(self, redis_storage: RedisStorage) -> None:
        engine = ReputationEngine(redis_storage, penalty=0.5)
        for _ in range(10):
            await engine.apply_penalty(2, 1.0)
        score = await engine.get_reputation(2)
        assert score == 1.0

    async def test_decay_reduces_score(self, redis_storage: RedisStorage) -> None:
        engine = ReputationEngine(redis_storage, penalty=0.2, decay=0.5)
        await engine.apply_penalty(3, 1.0)
        await engine.apply_penalty(3, 1.0)
        before = await engine.get_reputation(3)
        assert before > 0.0

        after = await engine.apply_decay(3)
        assert after < before

    async def test_decay_bottom_at_zero(self, redis_storage: RedisStorage) -> None:
        engine = ReputationEngine(redis_storage, decay=0.5)
        for _ in range(10):
            await engine.apply_decay(4)
        score = await engine.get_reputation(4)
        assert score == 0.0
