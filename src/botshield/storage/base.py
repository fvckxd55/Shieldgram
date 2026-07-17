"""Абстрактный интерфейс хранилища."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractStorage(ABC):
    """Базовый класс для backend-хранилищ."""

    @abstractmethod
    async def connect(self) -> None:
        """Установить соединение."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Закрыть соединение."""

    @abstractmethod
    async def increment(self, key: str, window_seconds: float) -> int:
        """Атомарно увеличить счётчик и вернуть количество событий в окне."""

    @abstractmethod
    async def get_count(self, key: str, window_seconds: float) -> int:
        """Получить количество событий в окне без инкремента."""

    @abstractmethod
    async def add_to_sorted_set(
        self, key: str, score: float, member: str
    ) -> None:
        """Добавить элемент в sorted set."""

    @abstractmethod
    async def count_sorted_set(
        self, key: str, min_score: float, max_score: float
    ) -> int:
        """Подсчитать элементы в диапазоне score."""

    @abstractmethod
    async def remove_sorted_set_below(self, key: str, min_score: float) -> int:
        """Удалить элементы ниже min_score из sorted set."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Получить строковое значение."""

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Установить строковое значение."""

    @abstractmethod
    async def eval_lua(self, script: str, keys: int, *args: str) -> list[Any]:
        """Выполнить Lua-скрипт атомарно."""

    @abstractmethod
    async def check_sliding_window(
        self,
        user_id: int,
        window_seconds: float,
        max_events: int,
        event_type: str = "msg",
    ) -> tuple[int, bool]:
        """Проверить sliding window."""

    @abstractmethod
    async def check_token_bucket(
        self,
        user_id: int,
        rate: float,
        burst: int,
        tokens_requested: int = 1,
    ) -> tuple[bool, int]:
        """Проверить token bucket."""
