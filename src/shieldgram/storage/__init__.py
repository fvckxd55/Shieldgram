"""Слой хранения Shieldgram."""

from .base import AbstractStorage
from .redis import RedisStorage

__all__ = ["AbstractStorage", "RedisStorage"]
