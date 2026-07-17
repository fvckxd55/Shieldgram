"""Тесты для SpamDetector."""

from __future__ import annotations

from aiogram.types import Chat, Message, User

from shieldgram.config import SpamDetectorConfig
from shieldgram.detectors.spam_detector import SpamDetector
from shieldgram.storage.redis import RedisStorage
from shieldgram.types import DetectionVerdict


def _make_message(user_id: int, text: str) -> Message:
    return Message(
        message_id=1,
        date=0,
        chat=Chat(id=user_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        text=text,
    )


class TestSpamDetector:
    async def test_allows_clean_message(
        self, redis_storage: RedisStorage
    ) -> None:
        config = SpamDetectorConfig(max_links_per_message=3, ad_pattern_threshold=2)
        detector = SpamDetector(redis_storage, config)

        result = await detector.analyze(_make_message(1, "Hello, how are you?"), {})
        assert result.verdict == DetectionVerdict.ALLOW
        assert result.score == 0.0

    async def test_detects_many_links(
        self, redis_storage: RedisStorage
    ) -> None:
        config = SpamDetectorConfig(max_links_per_message=1, ad_pattern_threshold=10)
        detector = SpamDetector(redis_storage, config)

        text = "Check https://spam.com and https://scam.ru and https://evil.net"
        result = await detector.analyze(_make_message(1, text), {})
        assert result.verdict in (DetectionVerdict.WARN, DetectionVerdict.BLOCK)
        assert result.metadata["link_score"] >= 0.5

    async def test_detects_ad_patterns(
        self, redis_storage: RedisStorage
    ) -> None:
        config = SpamDetectorConfig(max_links_per_message=10, ad_pattern_threshold=1)
        detector = SpamDetector(redis_storage, config)

        text = "Buy cheap casino tokens now! Free money click here!"
        result = await detector.analyze(_make_message(1, text), {})
        assert result.verdict in (DetectionVerdict.WARN, DetectionVerdict.BLOCK)
        assert result.metadata["ad_score"] >= 0.5

    async def test_detects_telegram_links(
        self, redis_storage: RedisStorage
    ) -> None:
        config = SpamDetectorConfig(max_links_per_message=1, ad_pattern_threshold=10)
        detector = SpamDetector(redis_storage, config)

        text = "Join t.me/spam123 and t.me/scam456"
        result = await detector.analyze(_make_message(1, text), {})
        assert result.metadata["link_score"] >= 0.5

    async def test_disabled_returns_allow(
        self, redis_storage: RedisStorage
    ) -> None:
        config = SpamDetectorConfig(enabled=False)
        detector = SpamDetector(redis_storage, config)

        text = "Buy cheap casino!!! https://spam.com https://scam.ru"
        result = await detector.analyze(_make_message(1, text), {})
        assert result.verdict == DetectionVerdict.ALLOW

    async def test_empty_message(self, redis_storage: RedisStorage) -> None:
        config = SpamDetectorConfig()
        detector = SpamDetector(redis_storage, config)

        msg = Message(
            message_id=1,
            date=0,
            chat=Chat(id=1, type="private"),
            from_user=User(id=1, is_bot=False, first_name="Test"),
        )
        result = await detector.analyze(msg, {})
        assert result.verdict == DetectionVerdict.ALLOW
