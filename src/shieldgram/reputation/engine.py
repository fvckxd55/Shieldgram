"""Reputation Engine — система доверия пользователей.

Шкала:
- 0.0 — нормальное поведение
- 0.5 — подозрительная активность
- 1.0 — злоумышленник

При атаке: reputation += penalty (быстрый рост)
При нормальном поведении: reputation *= decay (медленное затухание)
"""

from __future__ import annotations

import structlog

from ..storage.base import AbstractStorage

logger = structlog.get_logger()

_REPUTATION_KEY = "shieldgram:rep:{user_id}"
_REPUTATION_TTL = 86400 * 7  # 7 дней


class ReputationEngine:
    """Управляет репутацией пользователей в Redis."""

    def __init__(
        self,
        storage: AbstractStorage,
        penalty: float = 0.15,
        decay: float = 0.95,
    ) -> None:
        self._storage = storage
        self._penalty = penalty
        self._decay = decay

    async def get_reputation(self, user_id: int) -> float:
        raw = await self._storage.get(_REPUTATION_KEY.format(user_id=user_id))
        return float(raw) if raw else 0.0

    async def apply_penalty(self, user_id: int, score: float) -> float:
        """Применить штраф за нарушение."""
        current = await self.get_reputation(user_id)
        penalty = score * self._penalty
        new_score = min(current + penalty, 1.0)
        await self._storage.set(
            _REPUTATION_KEY.format(user_id=user_id),
            str(round(new_score, 3)),
            ttl=_REPUTATION_TTL,
        )
        logger.info(
            "reputation_penalty",
            user_id=user_id,
            old=round(current, 3),
            new=round(new_score, 3),
        )
        return new_score

    async def apply_decay(self, user_id: int) -> float:
        """Применить затухание (нормальное поведение)."""
        current = await self.get_reputation(user_id)
        if current <= 0.01:
            await self._storage.set(
                _REPUTATION_KEY.format(user_id=user_id), "0", ttl=_REPUTATION_TTL
            )
            return 0.0
        new_score = round(current * self._decay, 3)
        await self._storage.set(
            _REPUTATION_KEY.format(user_id=user_id),
            str(new_score),
            ttl=_REPUTATION_TTL,
        )
        return new_score
