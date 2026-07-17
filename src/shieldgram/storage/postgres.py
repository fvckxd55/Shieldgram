"""PostgreSQL-хранилище для логов событий."""

from __future__ import annotations

import datetime
import json
from typing import Any

import structlog
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = structlog.get_logger()


class Base(DeclarativeBase):
    pass


class DetectionLog(Base):
    """Лог одного события детектора."""

    __tablename__ = "detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    detector_name: Mapped[str] = mapped_column(String(64))
    verdict: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column()
    reason: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class PostgresStorage:
    """Асинхронное хранилище логов в PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url, echo=False)

    async def connect(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
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
        async with AsyncSession(self._engine) as session:
            log_entry = DetectionLog(
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
    ) -> list[DetectionLog]:
        from sqlalchemy import select

        async with AsyncSession(self._engine) as session:
            result = await session.execute(
                select(DetectionLog)
                .where(DetectionLog.user_id == user_id)
                .order_by(DetectionLog.timestamp.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
