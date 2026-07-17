"""Базовый класс детектора."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aiogram.types import TelegramObject

from ..storage.base import AbstractStorage
from ..types import DetectionResult


class AbstractDetector(ABC):
    """Базовый класс для всех детекторов."""

    name: str = "base"

    def __init__(self, storage: AbstractStorage) -> None:
        self._storage = storage

    @abstractmethod
    async def analyze(
        self, event: TelegramObject, data: dict[str, Any]
    ) -> DetectionResult:
        """Проанализировать событие и вернуть вердикт."""

    async def startup(self) -> None:
        """Вызывается при инициализации детектора."""

    async def shutdown(self) -> None:
        """Вызывается при остановке детектора."""
