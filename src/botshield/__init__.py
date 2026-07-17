"""BotShield — защитный слой для Telegram-ботов."""

from .config import BotShieldConfig
from .middleware.shield import BotShield

__all__ = ["BotShield", "BotShieldConfig"]
__version__ = "0.1.0"
