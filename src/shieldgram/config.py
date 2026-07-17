"""Конфигурация Shieldgram."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RateLimiterConfig:
    sliding_window_seconds: float = 60.0
    max_requests_per_window: int = 30
    token_bucket_rate: float = 5.0
    token_bucket_burst: int = 10
    enabled: bool = True


@dataclass
class FloodDetectorConfig:
    burst_window_seconds: float = 5.0
    burst_threshold: int = 10
    repeat_window_seconds: float = 30.0
    repeat_threshold: int = 5
    enabled: bool = True


@dataclass
class SpamDetectorConfig:
    max_links_per_message: int = 3
    ad_pattern_threshold: int = 2
    enabled: bool = True


@dataclass
class ReputationConfig:
    penalty: float = 0.15
    decay: float = 0.95
    enabled: bool = True


@dataclass
class ShieldConfig:
    """Главная конфигурация Shieldgram."""

    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "shieldgram"
    postgres_url: str | None = None

    rate_limiter: RateLimiterConfig = field(default_factory=RateLimiterConfig)
    flood_detector: FloodDetectorConfig = field(default_factory=FloodDetectorConfig)
    spam_detector: SpamDetectorConfig = field(default_factory=SpamDetectorConfig)
    reputation: ReputationConfig = field(default_factory=ReputationConfig)

    block_threshold: float = 0.7
    warn_threshold: float = 0.4
    warn_message: str = (
        "\u26a0\ufe0f "
        "\u041e\u0431\u043d\u0430\u0440\u0443\u0436\u0435\u043d\u0430 "
        "\u043f\u043e\u0434\u043e\u0437\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f "
        "\u0430\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442\u044c. "
        "\u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, "
        "\u0437\u0430\u043c\u0435\u0434\u043b\u0438\u0442\u0435\u0441\u044c."
    )

    ignore_users: list[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShieldConfig:
        rl = data.get("rate_limiter", {})
        fd = data.get("flood_detector", {})
        sd = data.get("spam_detector", {})
        rep = data.get("reputation", {})
        return cls(
            redis_url=str(data.get("redis_url", "redis://localhost:6379/0")),
            redis_key_prefix=str(data.get("redis_key_prefix", "shieldgram")),
            postgres_url=data.get("postgres_url"),
            rate_limiter=RateLimiterConfig(
                sliding_window_seconds=float(rl.get("sliding_window_seconds", 60.0)),
                max_requests_per_window=int(rl.get("max_requests_per_window", 30)),
                token_bucket_rate=float(rl.get("token_bucket_rate", 5.0)),
                token_bucket_burst=int(rl.get("token_bucket_burst", 10)),
                enabled=bool(rl.get("enabled", True)),
            ),
            flood_detector=FloodDetectorConfig(
                burst_window_seconds=float(fd.get("burst_window_seconds", 5.0)),
                burst_threshold=int(fd.get("burst_threshold", 10)),
                repeat_window_seconds=float(fd.get("repeat_window_seconds", 30.0)),
                repeat_threshold=int(fd.get("repeat_threshold", 5)),
                enabled=bool(fd.get("enabled", True)),
            ),
            spam_detector=SpamDetectorConfig(
                max_links_per_message=int(sd.get("max_links_per_message", 3)),
                ad_pattern_threshold=int(sd.get("ad_pattern_threshold", 2)),
                enabled=bool(sd.get("enabled", True)),
            ),
            reputation=ReputationConfig(
                penalty=float(rep.get("penalty", 0.15)),
                decay=float(rep.get("decay", 0.95)),
                enabled=bool(rep.get("enabled", True)),
            ),
            block_threshold=float(data.get("block_threshold", 0.7)),
            warn_threshold=float(data.get("warn_threshold", 0.4)),
            ignore_users=list(data.get("ignore_users", [])),
        )
