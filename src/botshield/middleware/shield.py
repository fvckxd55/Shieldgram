"""BotShield Middleware — главный защитный слой."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from ..config import BotShieldConfig
from ..detectors.flood_detector import FloodDetector
from ..detectors.rate_limiter import RateLimiter
from ..engine.decision import DecisionEngine
from ..engine.detection import DetectionEngine
from ..storage.redis import RedisStorage
from ..types import DetectionVerdict

logger = structlog.get_logger()


class BotShield(BaseMiddleware):
    """Главный middleware для защиты Telegram-бота.

    Подключается как middleware к aiogram Router или Dispatcher.

    Пример:
        from botshield import BotShield

        shield = BotShield(redis="redis://localhost:6379/0")
        dp.message.middleware(shield)
    """

    def __init__(
        self, redis: str = "redis://localhost:6379/0", **kwargs: Any
    ) -> None:
        config_data: dict[str, Any] = {"redis_url": redis, **kwargs}
        self._config = BotShieldConfig.from_dict(config_data)

        self._storage = RedisStorage(
            redis_url=self._config.redis_url,
            key_prefix=self._config.redis_key_prefix,
        )

        self._detectors = [
            RateLimiter(self._storage, self._config.rate_limiter),
            FloodDetector(self._storage, self._config.flood_detector),
        ]

        self._detection_engine = DetectionEngine(self._detectors)
        self._decision_engine = DecisionEngine(self._config)

        self._started = False

    async def startup(self) -> None:
        """Инициализировать хранилище и детекторы."""
        if self._started:
            return
        await self._storage.connect()
        await self._detection_engine.startup()
        self._started = True
        logger.info("botshield_started")

    async def shutdown(self) -> None:
        """Корректно завершить работу."""
        await self._detection_engine.shutdown()
        await self._storage.disconnect()
        self._started = False
        logger.info("botshield_stopped")

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
        decision = self._decision_engine.decide(results)

        logger.info(
            "botshield_check",
            user_id=user_id,
            verdict=decision.verdict.name,
            score=round(decision.score, 3),
            reason=decision.reason,
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
