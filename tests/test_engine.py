"""Тесты для DecisionEngine и ThreatScoreEngine."""

from __future__ import annotations

from shieldgram.config import ShieldConfig
from shieldgram.core.scoring import ThreatScoreEngine, ThreatWeights
from shieldgram.engine.decision import DecisionEngine
from shieldgram.types import AggregatedResult, DetectionResult, DetectionVerdict


class TestDecisionEngine:
    def test_empty_results(self) -> None:
        engine = DecisionEngine(ShieldConfig())
        result = engine.decide([])
        assert result.verdict == DetectionVerdict.ALLOW

    def test_single_warn(self) -> None:
        engine = DecisionEngine(ShieldConfig())
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
        engine = DecisionEngine(ShieldConfig())
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

    def test_all_allowed(self) -> None:
        engine = DecisionEngine(ShieldConfig())
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

    def test_override_block(self) -> None:
        engine = DecisionEngine(ShieldConfig())
        results: list[DetectionResult] = []
        result = engine.override_block(results, "0.85")
        assert result.verdict == DetectionVerdict.BLOCK
        assert result.score == 1.0

    def test_aggregated_result_properties(self) -> None:
        result = AggregatedResult(verdict=DetectionVerdict.BLOCK, score=0.9, reason="test")
        assert result.blocked is True
        assert result.warned is False


class TestThreatScoreEngine:
    def test_clean_score(self) -> None:
        engine = ThreatScoreEngine()
        score = engine.compute(flood=0.1, spam=0.0)
        assert score.total < 0.4
        assert score.is_clean is True

    def test_warning_score(self) -> None:
        engine = ThreatScoreEngine()
        score = engine.compute(flood=1.0, spam=0.3)
        assert 0.4 <= score.total < 0.7
        assert score.is_warning is True

    def test_block_score(self) -> None:
        engine = ThreatScoreEngine()
        score = engine.compute(flood=1.0, spam=0.8, links=0.5)
        assert score.total >= 0.7
        assert score.is_blocked is True

    def test_max_clamped(self) -> None:
        engine = ThreatScoreEngine()
        score = engine.compute(flood=1.0, spam=1.0, links=1.0, suspicious=1.0)
        assert score.total == 1.0

    def test_breakdown(self) -> None:
        engine = ThreatScoreEngine()
        score = engine.compute(flood=0.5, spam=0.5)
        assert score.breakdown == {
            "flood": 0.2,
            "spam": 0.15,
            "links": 0.0,
            "suspicious": 0.0,
        }

    def test_custom_weights(self) -> None:
        weights = ThreatWeights(flood=0.5, spam=0.5, links=0.0, suspicious=0.0)
        engine = ThreatScoreEngine(weights)
        score = engine.compute(flood=1.0, spam=0.0)
        assert score.total == 0.5
