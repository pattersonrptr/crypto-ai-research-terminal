"""NarrativeCluster model — detected market narrative stored per snapshot date."""

from datetime import date, datetime

from sqlalchemy import ARRAY, Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NarrativeCluster(Base):
    """A detected market narrative cluster persisted at a point in time.

    Each row represents one narrative detected by :class:`NarrativeDetector`
    during a snapshot run.  The ``snapshot_date`` groups rows from the same
    run, enabling trend comparison between dates.
    """

    __tablename__ = "narratives"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    momentum_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trend: Mapped[str] = mapped_column(String(20), nullable=False, default="stable")
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    token_symbols: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"NarrativeCluster(id={self.id!r}, name={self.name!r})"
