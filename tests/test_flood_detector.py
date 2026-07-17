"""Тесты для FloodDetector."""

from __future__ import annotations

import asyncio

from aiogram.types import Chat, Message, User

from botshield.config import FloodDetectorConfig
from botshield.detectors.flood_detector import FloodDetector
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


class TestFloodDetector:
    async def test_allows_normal_traffic(
        self, redis_storage: RedisStorage, flood_config: FloodDetectorConfig
    ) -> None:
        detector = FloodDetector(redis_storage, flood_config)

        for _ in range(2):
            result = await detector.analyze(_make_message(1), {})
            assert result.verdict == DetectionVerdict.ALLOW

    async def test_detects_repeated_content(
        self, redis_storage: RedisStorage, flood_config: FloodDetectorConfig
    ) -> None:
        config = FloodDetectorConfig(
            burst_window_seconds=3.0,
            burst_threshold=100,
            repeat_window_seconds=30.0,
            repeat_threshold=3,
        )
        detector = FloodDetector(redis_storage, config)

        for _ in range(3):
            result = await detector.analyze(_make_message(1, "spam spam spam"), {})
            assert result.verdict in (DetectionVerdict.ALLOW, DetectionVerdict.WARN)

        for _ in range(3):
            result = await detector.analyze(_make_message(1, "spam spam spam"), {})

        assert result.verdict == DetectionVerdict.BLOCK

    async def test_detects_burst(
        self, redis_storage: RedisStorage
    ) -> None:
        config = FloodDetectorConfig(
            burst_window_seconds=5.0,
            burst_threshold=3,
            repeat_window_seconds=30.0,
            repeat_threshold=100,
        )
        detector = FloodDetector(redis_storage, config)

        for i in range(5):
            await detector.analyze(_make_message(1, f"burst_{i}"), {})
            await asyncio.sleep(0.01)

        result = await detector.analyze(_make_message(1, "burst_final"), {})
        assert result.verdict in (DetectionVerdict.WARN, DetectionVerdict.BLOCK)

    async def test_disabled_returns_allow(
        self, redis_storage: RedisStorage
    ) -> None:
        config = FloodDetectorConfig(enabled=False)
        detector = FloodDetector(redis_storage, config)

        for _ in range(100):
            result = await detector.analyze(_make_message(1, "spam"), {})
            assert result.verdict == DetectionVerdict.ALLOW

    async def test_different_content_no_repeat(
        self, redis_storage: RedisStorage, flood_config: FloodDetectorConfig
    ) -> None:
        detector = FloodDetector(redis_storage, flood_config)

        for i in range(3):
            result = await detector.analyze(_make_message(1, f"unique_{i}"), {})
            assert result.verdict == DetectionVerdict.ALLOW
            assert result.score < 0.5
