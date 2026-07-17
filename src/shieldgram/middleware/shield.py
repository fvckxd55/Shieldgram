"""Shieldgram Middleware — главный защитный слой для aiogram."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from ..config import ShieldConfig
from ..core.scoring import ThreatScoreEngine
from ..detectors.flood_detector import FloodDetector
from ..detectors.rate_limiter import RateLimiter
from ..detectors.spam_detector import SpamDetector
from ..engine.decision import DecisionEngine
from ..engine.detection import DetectionEngine
from ..reputation.engine import ReputationEngine
from ..storage.postgres import PostgresStorage
from ..storage.redis import RedisStorage
from ..types import DetectionVerdict

logger = structlog.get_logger()


class Shield(BaseMiddleware):
    """Главный middleware для защиты Telegram-бота.

        from shieldgram import Shield

        shield = Shield(redis="redis://localhost:6379/0")
        dp.message.middleware(shield)
    """

    def __init__(self, redis: str = "redis://localhost:6379/0", **kwargs: Any) -> None:
        config_data: dict[str, Any] = {"redis_url": redis, **kwargs}
        self._config = ShieldConfig.from_dict(config_data)

        self._redis = RedisStorage(
            redis_url=self._config.redis_url,
            key_prefix=self._config.redis_key_prefix,
        )

        self._postgres: PostgresStorage | None = None
        if self._config.postgres_url:
            self._postgres = PostgresStorage(self._config.postgres_url)

        self._detectors = [
            RateLimiter(self._redis, self._config.rate_limiter),
            FloodDetector(self._redis, self._config.flood_detector),
            SpamDetector(self._redis, self._config.spam_detector),
        ]

        self._reputation = ReputationEngine(
            self._redis,
            penalty=self._config.reputation.penalty,
            decay=self._config.reputation.decay,
        )
        self._scoring = ThreatScoreEngine()
        self._detection_engine = DetectionEngine(self._detectors)
        self._decision_engine = DecisionEngine(self._config)

        self._started = False

    async def startup(self) -> None:
        if self._started:
            return
        await self._redis.connect()
        if self._postgres:
            await self._postgres.connect()
        await self._detection_engine.startup()
        self._started = True
        logger.info("shieldgram_started")

    async def shutdown(self) -> None:
        await self._detection_engine.shutdown()
        if self._postgres:
            await self._postgres.disconnect()
        await self._redis.disconnect()
        self._started = False
        logger.info("shieldgram_stopped")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not self._started:
            await self.startup()

        user_id = self._extract_user_id(event)
        if user_id is not None and user_id in self._config.ignore_users:
            return await handler(event, data)

        results = await self._detection_engine.analyze(event, data)

        flood_score = 0.0
        spam_score = 0.0
        links_score = 0.0
        for r in results:
            if r.detector_name == "flood_detector":
                flood_score = r.score
                if r.metadata.get("repeat_score", 0) > 0.3:
                    spam_score = r.metadata["repeat_score"]
            elif r.detector_name == "spam_detector":
                links_score = r.metadata.get("link_score", 0)
                spam_score = max(spam_score, r.metadata.get("ad_score", 0))

        threat = self._scoring.compute(
            flood=flood_score, spam=spam_score, links=links_score,
        )

        decision = self._decision_engine.decide(results)

        if threat.total >= self._config.block_threshold:
            decision = self._decision_engine.override_block(results, str(threat.total))

        if user_id is not None:
            if decision.blocked:
                await self._reputation.apply_penalty(user_id, threat.total)
            else:
                await self._reputation.apply_decay(user_id)

            if self._postgres:
                for r in results:
                    await self._postgres.log_event(
                        user_id=user_id,
                        detector_name=r.detector_name,
                        verdict=r.verdict.name,
                        score=r.score,
                        reason=r.reason,
                        metadata=r.metadata,
                    )

        logger.info(
            "shieldgram_check",
            user_id=user_id,
            verdict=decision.verdict.name,
            score=round(decision.score, 3),
        )

        if decision.verdict == DetectionVerdict.BLOCK:
            return None

        if decision.verdict == DetectionVerdict.WARN and isinstance(event, Message):
            await event.answer(self._config.warn_message)

        return await handler(event, data)

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user is not None:
            return event.from_user.id
        if hasattr(event, "from_user") and event.from_user is not None:
            return event.from_user.id  # type: ignore[no-any-return]
        return None
