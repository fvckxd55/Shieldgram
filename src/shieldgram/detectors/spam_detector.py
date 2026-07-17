"""Spam Detector — ссылки, рекламные паттерны, подозрительный контент."""

from __future__ import annotations

import re
from typing import Any

from aiogram.types import Message, TelegramObject

from ..config import SpamDetectorConfig
from ..storage.base import AbstractStorage
from ..types import DetectionResult, DetectionVerdict
from .base import AbstractDetector

_AD_PATTERNS: list[str] = [
    r"\b(?:buy|cheap|discount|free\s*money|click\s*here)\b",
    r"\b(?:casino|bet|gambling|poker|lottery)\b",
    r"\b(?:crypto.*(?:signal|pump|100x|moon))\b",
    r"\b(?:earn\s*(?:money|cash|usd|usdt|btc|eth))\b",
    r"\b(?:join\s*(?:now|today|fast).*(?:channel|group))\b",
]

_URL_RE = re.compile(r"https?://\S+|t\.me/\S+", re.IGNORECASE)


class SpamDetector(AbstractDetector):
    """Обнаружение спама.

    Анализирует:
    - Количество ссылок в сообщении
    - Рекламные паттерны (ключевые слова)
    - Комбинацию факторов
    """

    name = "spam_detector"

    def __init__(
        self,
        storage: AbstractStorage,
        config: SpamDetectorConfig,
    ) -> None:
        super().__init__(storage)
        self._config = config
        self._ad_patterns = [re.compile(p, re.IGNORECASE) for p in _AD_PATTERNS]

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

        text = self._extract_text(event)
        if not text:
            return DetectionResult(
                detector_name=self.name,
                verdict=DetectionVerdict.ALLOW,
                score=0.0,
                reason="no text",
            )

        link_score = self._check_links(text)
        ad_score = self._check_ads(text)

        score = max(link_score, ad_score)

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
            reason=f"links={link_score:.2f}, ads={ad_score:.2f}",
            metadata={
                "link_score": round(link_score, 3),
                "ad_score": round(ad_score, 3),
            },
        )

    def _check_links(self, text: str) -> float:
        urls = _URL_RE.findall(text)
        count = len(urls)
        max_links = self._config.max_links_per_message

        if max_links <= 0:
            return 0.0

        if count >= max_links * 2:
            return 1.0
        if count > max_links:
            return 0.6 + (count - max_links) / max_links * 0.4
        return count / max_links * 0.5

    def _check_ads(self, text: str) -> float:
        matches = 0
        for pattern in self._ad_patterns:
            if pattern.search(text):
                matches += 1

        threshold = self._config.ad_pattern_threshold
        if threshold <= 0:
            return 0.0

        if matches >= threshold * 2:
            return 1.0
        if matches >= threshold:
            return 0.6 + (matches - threshold) / threshold * 0.4
        return matches / threshold * 0.5

    @staticmethod
    def _extract_text(event: TelegramObject) -> str | None:
        if isinstance(event, Message):
            text = event.text or event.caption
            return text.strip() if text else None
        return None
