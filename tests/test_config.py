"""Тесты для конфигурации."""

from __future__ import annotations

from shieldgram.config import FloodDetectorConfig, RateLimiterConfig, ShieldConfig


class TestConfig:
    def test_default_config(self) -> None:
        config = ShieldConfig()
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.rate_limiter.enabled is True
        assert config.flood_detector.enabled is True
        assert config.block_threshold == 0.7
        assert config.warn_threshold == 0.4

    def test_from_dict(self) -> None:
        data = {
            "redis_url": "redis://custom:6379/1",
            "redis_key_prefix": "sg",
            "rate_limiter": {
                "sliding_window_seconds": 30,
                "max_requests_per_window": 10,
                "enabled": False,
            },
            "flood_detector": {
                "burst_threshold": 20,
            },
            "block_threshold": 0.9,
            "ignore_users": [123, 456],
        }
        config = ShieldConfig.from_dict(data)
        assert config.redis_url == "redis://custom:6379/1"
        assert config.redis_key_prefix == "sg"
        assert config.rate_limiter.sliding_window_seconds == 30
        assert config.rate_limiter.max_requests_per_window == 10
        assert config.rate_limiter.enabled is False
        assert config.flood_detector.burst_threshold == 20
        assert config.block_threshold == 0.9
        assert config.ignore_users == [123, 456]

    def test_rate_limiter_config_defaults(self) -> None:
        config = RateLimiterConfig()
        assert config.sliding_window_seconds == 60.0
        assert config.max_requests_per_window == 30
        assert config.token_bucket_rate == 5.0
        assert config.token_bucket_burst == 10

    def test_flood_config_defaults(self) -> None:
        config = FloodDetectorConfig()
        assert config.burst_window_seconds == 5.0
        assert config.burst_threshold == 10
        assert config.repeat_window_seconds == 30.0
        assert config.repeat_threshold == 5
