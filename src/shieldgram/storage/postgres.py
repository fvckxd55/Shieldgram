"""PostgreSQL-хранилище для логов событий.

SQLAlchemy — опциональная зависимость. Установи:
    pip install shieldgram[dashboard]
"""

from __future__ import annotations

import datetime
import json
from typing import Any

import structlog

logger = structlog.get_logger()


class PostgresStorage:
    """Асинхронное хранилище логов в PostgreSQL.

    Все импорты sqlalchemy — ленивые, внутри методов.
    Без PostgreSQL модуль импортируется без ошибок.
    """

    def __init__(self, database_url: str) -> None:
        from sqlalchemy.ext.asyncio import create_async_engine

        self._engine = create_async_engine(database_url, echo=False)
        self._model: Any = None
        self._base: Any = None

    async def connect(self) -> None:
        from sqlalchemy import DateTime, Integer, String, Text, func
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

        class _Base(DeclarativeBase):
            pass

        class _DetectionLog(_Base):
            __tablename__ = "detection_logs"

            id: Mapped[int] = mapped_column(
                Integer, primary_key=True, autoincrement=True
            )
            timestamp: Mapped[datetime.datetime] = mapped_column(
                DateTime(timezone=True), server_default=func.now()
            )
            user_id: Mapped[int] = mapped_column(Integer, index=True)
            detector_name: Mapped[str] = mapped_column(String(64))
            verdict: Mapped[str] = mapped_column(String(16))
            score: Mapped[float] = mapped_column()
            reason: Mapped[str] = mapped_column(Text, default="")
            metadata_json: Mapped[str | None] = mapped_column(
                Text, nullable=True
            )

        self._model = _DetectionLog
        self._base = _Base

        async with self._engine.begin() as conn:
            await conn.run_sync(_Base.metadata.create_all)
        logger.info("postgres_connected")

    async def disconnect(self) -> None:
        await self._engine.dispose()
        logger.info("postgres_disconnected")

    async def log_event(
        self,
        user_id: int,
        detector_name: str,
        verdict: str,
        score: float,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        from sqlalchemy.ext.asyncio import AsyncSession

        if self._model is None:
            logger.warning("postgres_not_connected")
            return

        async with AsyncSession(self._engine) as session:
            log_entry = self._model(
                user_id=user_id,
                detector_name=detector_name,
                verdict=verdict,
                score=score,
                reason=reason,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            session.add(log_entry)
            await session.commit()

    async def get_user_history(
        self, user_id: int, limit: int = 50
    ) -> list[Any]:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        if self._model is None:
            return []

        async with AsyncSession(self._engine) as session:
            stmt = (
                select(self._model)
                .where(self._model.user_id == user_id)
                .order_by(self._model.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
