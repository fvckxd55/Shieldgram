"""Слой хранения BotShield."""

from .base import AbstractStorage
from .redis import RedisStorage

__all__ = ["AbstractStorage", "RedisStorage"]
