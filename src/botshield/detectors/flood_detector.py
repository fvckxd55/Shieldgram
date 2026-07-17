"""Flood Detector — обнаружение флуда и повторяющихся сообщений."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from aiogram.types import Message, TelegramObject

from ..config import FloodDetectorConfig
from ..storage.base import AbstractStorage
from ..types import DetectionResult, DetectionVerdict
from .base import AbstractDetector


class FloodDetector(AbstractDetector):
    """Обнаружение флуда.

    Анализирует:
    - Взрывную частоту (burst): N сообщений за M секунд
    - Повторы контента: одинаковые сообщения за окно
    """

    name = "flood_detector"

    def __init__(
        self,
        storage: AbstractStorage,
        config: FloodDetectorConfig,
    ) -> None:
        super().__init__(storage)
        self._config = config
        self._burst_counter: int = 0

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

        burst_score = await self._check_burst(user_id)
        repeat_score = await self._check_repeats(user_id, event)

        score = max(burst_score, repeat_score)

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
            reason=f"burst={burst_score:.2f}, repeat={repeat_score:.2f}",
            metadata={
                "burst_score": round(burst_score, 3),
                "repeat_score": round(repeat_score, 3),
            },
        )

    async def _check_burst(self, user_id: int) -> float:
        """Проверить взрывную частоту сообщений."""
        now = time.time()
        self._burst_counter += 1
        prefix = f"botshield:fd:burst:{user_id}"
        member = f"{now}:{self._burst_counter}"

        await self._storage.add_to_sorted_set(prefix, now, member)
        await self._storage.remove_sorted_set_below(
            prefix, now - self._config.burst_window_seconds
        )

        count = await self._storage.count_sorted_set(
            prefix,
            now - self._config.burst_window_seconds,
            now,
        )

        threshold = self._config.burst_threshold
        if count >= threshold * 2:
            return 1.0
        if count >= threshold:
            return 0.6 + (count - threshold) / threshold * 0.4
        return count / threshold * 0.5

    async def _check_repeats(
        self, user_id: int, event: TelegramObject
    ) -> float:
        """Проверить повторяющийся контент."""
        content_hash = self._hash_content(event)
        if content_hash is None:
            return 0.0

        key = f"botshield:fd:repeat:{user_id}:{content_hash}"

        last_count_str = await self._storage.get(key)
        last_count = int(last_count_str) if last_count_str else 0

        new_count = last_count + 1
        await self._storage.set(
            key, str(new_count), ttl=int(self._config.repeat_window_seconds)
        )

        threshold = self._config.repeat_threshold
        if new_count >= threshold * 2:
            return 1.0
        if new_count >= threshold:
            return 0.6 + (new_count - threshold) / threshold * 0.4
        return new_count / threshold * 0.5

    @staticmethod
    def _hash_content(event: TelegramObject) -> str | None:
        """Создать хеш содержимого сообщения."""
        if isinstance(event, Message) and event.text:
            text = event.text.strip().lower()
            return hashlib.md5(text.encode()).hexdigest()
        return None

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user is not None:
            return event.from_user.id
        if hasattr(event, "from_user") and event.from_user is not None:
            return event.from_user.id  # type: ignore[no-any-return]
        return None
