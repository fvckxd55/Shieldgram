"""Общие типы данных."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class DetectionVerdict(Enum):
    """Вердикт детектора."""

    ALLOW = auto()
    WARN = auto()
    BLOCK = auto()


@dataclass
class DetectionResult:
    """Результат работы одного детектора."""

    detector_name: str
    verdict: DetectionVerdict
    score: float
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedResult:
    """Агрегированный результат всех детекторов."""

    verdict: DetectionVerdict
    score: float
    detector_results: list[DetectionResult] = field(default_factory=list)
    reason: str = ""

    @property
    def blocked(self) -> bool:
        return self.verdict == DetectionVerdict.BLOCK

    @property
    def warned(self) -> bool:
        return self.verdict == DetectionVerdict.WARN
