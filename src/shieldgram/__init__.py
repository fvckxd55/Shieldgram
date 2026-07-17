"""Shieldgram — защитный middleware для Telegram-ботов."""

from .config import (
    FloodDetectorConfig,
    RateLimiterConfig,
    ReputationConfig,
    ShieldConfig,
    SpamDetectorConfig,
)
from .middleware.shield import Shield

__all__ = [
    "FloodDetectorConfig",
    "RateLimiterConfig",
    "ReputationConfig",
    "Shield",
    "ShieldConfig",
    "SpamDetectorConfig",
]
__version__ = "0.2.0"
