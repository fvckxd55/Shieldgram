"""Тесты для DecisionEngine и DetectionEngine."""

from __future__ import annotations

from botshield.config import BotShieldConfig
from botshield.engine.decision import DecisionEngine
from botshield.types import AggregatedResult, DetectionResult, DetectionVerdict


class TestDecisionEngine:
    def test_empty_results(self) -> None:
        engine = DecisionEngine(BotShieldConfig())
        result = engine.decide([])
        assert result.verdict == DetectionVerdict.ALLOW

    def test_single_warn(self) -> None:
        engine = DecisionEngine(BotShieldConfig())
        results = [
            DetectionResult(
                detector_name="test",
                verdict=DetectionVerdict.WARN,
                score=0.6,
                reason="suspicious",
            ),
        ]
        result = engine.decide(results)
        assert result.verdict == DetectionVerdict.WARN
        assert result.score == 0.6

    def test_block_overrides_warn(self) -> None:
        engine = DecisionEngine(BotShieldConfig())
        results = [
            DetectionResult(
                detector_name="rate_limiter",
                verdict=DetectionVerdict.WARN,
                score=0.6,
                reason="high rate",
            ),
            DetectionResult(
                detector_name="flood",
                verdict=DetectionVerdict.BLOCK,
                score=0.9,
                reason="burst detected",
            ),
        ]
        result = engine.decide(results)
        assert result.verdict == DetectionVerdict.BLOCK
        assert result.score == 0.9

    def test_multiple_blocks_uses_max(self) -> None:
        engine = DecisionEngine(BotShieldConfig())
        results = [
            DetectionResult(
                detector_name="a",
                verdict=DetectionVerdict.BLOCK,
                score=0.85,
                reason="a",
            ),
            DetectionResult(
                detector_name="b",
                verdict=DetectionVerdict.BLOCK,
                score=1.0,
                reason="b",
            ),
        ]
        result = engine.decide(results)
        assert result.score == 1.0

    def test_all_allowed(self) -> None:
        engine = DecisionEngine(BotShieldConfig())
        results = [
            DetectionResult(
                detector_name="a",
                verdict=DetectionVerdict.ALLOW,
                score=0.1,
                reason="ok",
            ),
            DetectionResult(
                detector_name="b",
                verdict=DetectionVerdict.ALLOW,
                score=0.3,
                reason="ok",
            ),
        ]
        result = engine.decide(results)
        assert result.verdict == DetectionVerdict.ALLOW
        assert result.score == 0.3

    def test_aggregated_result_properties(self) -> None:
        result = AggregatedResult(
            verdict=DetectionVerdict.BLOCK,
            score=0.9,
            reason="test",
        )
        assert result.blocked is True
        assert result.warned is False

        result = AggregatedResult(
            verdict=DetectionVerdict.WARN,
            score=0.6,
            reason="test",
        )
        assert result.blocked is False
        assert result.warned is True

        result = AggregatedResult(
            verdict=DetectionVerdict.ALLOW,
            score=0.1,
            reason="test",
        )
        assert result.blocked is False
        assert result.warned is False
