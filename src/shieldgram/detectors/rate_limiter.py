"""Rate Limiter — Sliding Window + Token Bucket."""

from __future__ import annotations

from typing import Any

from aiogram.types import Message, TelegramObject

from ..config import RateLimiterConfig
from ..storage.base import AbstractStorage
from ..types import DetectionResult, DetectionVerdict
from .base import AbstractDetector


class RateLimiter(AbstractDetector):
    """Ограничение частоты запросов.

    Использует два алгоритма:
    - Sliding Window: ограничение количества событий за период
    - Token Bucket: плавное ограничение с burst-возможностью
    """

    name = "rate_limiter"

    def __init__(
        self,
        storage: AbstractStorage,
        config: RateLimiterConfig,
    ) -> None:
        super().__init__(storage)
        self._config = config

    async def analyze(
        self, event: TelegramObject, data: dict[str, Any]
    ) -> DetectionResult:
        if not self._config.enabled:
            return DetectionResult(
                detector_name=self.name,
                verdict=DetectionVerdict.ALLOW,
                score=0.0,
                reason="disabled",
            )

        user_id = self._extract_user_id(event)
        if user_id is None:
            return DetectionResult(
                detector_name=self.name,
                verdict=DetectionVerdict.ALLOW,
                score=0.0,
                reason="no user_id",
            )

        count, sw_blocked = await self._storage.check_sliding_window(
            user_id,
            self._config.sliding_window_seconds,
            self._config.max_requests_per_window,
        )

        tb_allowed, tb_tokens = await self._storage.check_token_bucket(
            user_id,
            self._config.token_bucket_rate,
            self._config.token_bucket_burst,
        )

        if sw_blocked:
            return DetectionResult(
                detector_name=self.name,
                verdict=DetectionVerdict.BLOCK,
                score=1.0,
                reason=(
                    f"Sliding window exceeded: "
                    f"{count}/{self._config.max_requests_per_window}"
                ),
                metadata={
                    "count": count,
                    "max": self._config.max_requests_per_window,
                },
            )

        max_req = self._config.max_requests_per_window
        utilization = count / max_req if max_req else 0.0
        tb_penalty = 0.0 if tb_allowed else 0.3

        score = min(utilization + tb_penalty, 1.0)

        if score >= 0.8:
            verdict = DetectionVerdict.BLOCK
        elif score >= 0.5:
            verdict = DetectionVerdict.WARN
        else:
            verdict = DetectionVerdict.ALLOW

        return DetectionResult(
            detector_name=self.name,
            verdict=verdict,
            score=score,
            reason=(
                f"Window: {count}/{max_req}, "
                f"tokens_left: {tb_tokens}"
            ),
            metadata={
                "count": count,
                "max": max_req,
                "tokens_left": tb_tokens,
                "utilization": round(utilization, 3),
            },
        )

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user is not None:
            return event.from_user.id
        if hasattr(event, "from_user") and event.from_user is not None:
            return event.from_user.id  # type: ignore[no-any-return]
        return None
