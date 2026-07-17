"""Detection Engine — оркестратор детекторов."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from aiogram.types import TelegramObject

from ..detectors.base import AbstractDetector
from ..types import DetectionResult, DetectionVerdict

logger = structlog.get_logger()


class DetectionEngine:
    """Запускает все детекторы конкурентно и собирает результаты."""

    def __init__(self, detectors: list[AbstractDetector]) -> None:
        self._detectors = detectors

    async def startup(self) -> None:
        tasks = [d.startup() for d in self._detectors]
        await asyncio.gather(*tasks)
        logger.info(
            "detection_engine_started",
            detectors=[d.name for d in self._detectors],
        )

    async def shutdown(self) -> None:
        tasks = [d.shutdown() for d in self._detectors]
        await asyncio.gather(*tasks)

    async def analyze(
        self, event: TelegramObject, data: dict[str, Any]
    ) -> list[DetectionResult]:
        """Запустить все детекторы параллельно."""
        if not self._detectors:
            return []

        tasks = [detector.analyze(event, data) for detector in self._detectors]
        raw_results: list[DetectionResult | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        clean_results: list[DetectionResult] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, BaseException):
                logger.error(
                    "detector_error",
                    detector=self._detectors[i].name,
                    error=str(result),
                )
                clean_results.append(
                    DetectionResult(
                        detector_name=self._detectors[i].name,
                        verdict=DetectionVerdict.ALLOW,
                        score=0.0,
                        reason=f"detector error: {result}",
                    )
                )
            else:
                clean_results.append(result)

        return clean_results
