"""Decision Engine — принимает решение на основе результатов детекторов."""

from __future__ import annotations

import structlog

from ..config import BotShieldConfig
from ..types import AggregatedResult, DetectionResult, DetectionVerdict

logger = structlog.get_logger()


class DecisionEngine:
    """Агрегирует результаты детекторов и выносит финальный вердикт."""

    def __init__(self, config: BotShieldConfig) -> None:
        self._config = config

    def decide(self, results: list[DetectionResult]) -> AggregatedResult:
        """Принять решение на основе результатов детекторов.

        Стратегия: worst-case — если любой детектор говорит BLOCK -> BLOCK.
        Иначе: max score определяет вердикт.
        """
        if not results:
            return AggregatedResult(
                verdict=DetectionVerdict.ALLOW,
                score=0.0,
                reason="no detectors",
            )

        blocks = [r for r in results if r.verdict == DetectionVerdict.BLOCK]
        warns = [r for r in results if r.verdict == DetectionVerdict.WARN]

        if blocks:
            max_block_score = max(r.score for r in blocks)
            reasons = "; ".join(
                f"{r.detector_name}: {r.reason}" for r in blocks
            )
            logger.warning(
                "decision_block",
                score=max_block_score,
                reasons=reasons,
                detectors=[r.detector_name for r in blocks],
            )
            return AggregatedResult(
                verdict=DetectionVerdict.BLOCK,
                score=max_block_score,
                detector_results=results,
                reason=reasons,
            )

        if warns:
            max_warn_score = max(r.score for r in warns)
            reasons = "; ".join(
                f"{r.detector_name}: {r.reason}" for r in warns
            )
            logger.info(
                "decision_warn",
                score=max_warn_score,
                reasons=reasons,
            )
            return AggregatedResult(
                verdict=DetectionVerdict.WARN,
                score=max_warn_score,
                detector_results=results,
                reason=reasons,
            )

        max_score = max(r.score for r in results)
        return AggregatedResult(
            verdict=DetectionVerdict.ALLOW,
            score=max_score,
            detector_results=results,
            reason="all clear",
        )
