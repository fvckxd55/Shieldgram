"""Threat Score Engine — вычисление итогового скора угрозы.

Веса угроз:

| Тип                  | Вес   |
|----------------------|-------|
| Flood (burst)        | +0.40 |
| Spam (repeat)        | +0.30 |
| Too many links       | +0.20 |
| Suspicious behavior  | +0.10 |

Пороги:

| Диапазон   | Вердикт |
|------------|---------|
| 0.0 – 0.4  | ALLOW   |
| 0.4 – 0.7  | WARN    |
| 0.7 – 1.0  | BLOCK   |
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThreatWeights:
    """Веса компонентов угрозы."""

    flood: float = 0.40
    spam: float = 0.30
    links: float = 0.20
    suspicious: float = 0.10


@dataclass
class ThreatScore:
    """Результат вычисления скора угрозы."""

    total: float
    flood: float = 0.0
    spam: float = 0.0
    links: float = 0.0
    suspicious: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return self.total < 0.4

    @property
    def is_warning(self) -> bool:
        return 0.4 <= self.total < 0.7

    @property
    def is_blocked(self) -> bool:
        return self.total >= 0.7


class ThreatScoreEngine:
    """Вычисляет итоговый threat score по компонентам."""

    def __init__(self, weights: ThreatWeights | None = None) -> None:
        self._weights = weights or ThreatWeights()

    def compute(
        self,
        *,
        flood: float = 0.0,
        spam: float = 0.0,
        links: float = 0.0,
        suspicious: float = 0.0,
    ) -> ThreatScore:
        """Вычислить threat score.

        Каждый компонент нормализован в [0, 1].
        Итоговый score — взвешенная сумма, зажатая в [0, 1].
        """
        w = self._weights

        flood_component = min(flood, 1.0) * w.flood
        spam_component = min(spam, 1.0) * w.spam
        links_component = min(links, 1.0) * w.links
        suspicious_component = min(suspicious, 1.0) * w.suspicious

        total = min(
            flood_component + spam_component + links_component + suspicious_component,
            1.0,
        )

        return ThreatScore(
            total=round(total, 3),
            flood=round(flood_component, 3),
            spam=round(spam_component, 3),
            links=round(links_component, 3),
            suspicious=round(suspicious_component, 3),
            breakdown={
                "flood": round(flood_component, 3),
                "spam": round(spam_component, 3),
                "links": round(links_component, 3),
                "suspicious": round(suspicious_component, 3),
            },
        )
