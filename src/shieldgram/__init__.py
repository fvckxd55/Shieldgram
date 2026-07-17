"""Shieldgram — защитный middleware для Telegram-ботов."""

from .config import ShieldConfig
from .middleware.shield import Shield

__all__ = ["Shield", "ShieldConfig"]
__version__ = "0.1.0"
