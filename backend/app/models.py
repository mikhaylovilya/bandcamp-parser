"""SQLAlchemy models."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    artist: Mapped[str | None] = mapped_column(String(512))
    release_type: Mapped[str | None] = mapped_column(String(32))
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "artist": self.artist,
            "release_type": self.release_type,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def create_all(engine) -> None:
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as exc:  # pragma: no cover - race guard
        if "already exists" not in str(exc).lower():
            raise
