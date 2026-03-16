"""HistoricalSnapshot model — stores full token state at a point in time.

Each row represents the state of a token on a specific date: price, market
cap, volume, supply and categories.  The composite unique constraint on
(symbol, snapshot_date) makes all inserts idempotent.

This model supports Phase 12 backtesting validation — re-running the scoring
pipeline on historical data to measure predictive accuracy.
"""

from __future__ import annotations

from datetime import date, datetime  # noqa: TCH003 — required at runtime by SQLAlchemy Mapped[]

from sqlalchemy import Date, DateTime, Double, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HistoricalSnapshot(Base):
    """Full token state on a given date for historical scoring."""

    __tablename__ = "historical_snapshots"

    __table_args__ = (
        UniqueConstraint("symbol", "snapshot_date", name="uq_hist_snapshot_symbol_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    price_usd: Mapped[float] = mapped_column(Double, nullable=False)
    market_cap_usd: Mapped[float] = mapped_column(Double, nullable=False)
    volume_usd: Mapped[float] = mapped_column(Double, nullable=False)
    circulating_supply: Mapped[float | None] = mapped_column(Double, nullable=True)
    total_supply: Mapped[float | None] = mapped_column(Double, nullable=True)
    categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    cycle_tag: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        sd = self.snapshot_date.isoformat() if self.snapshot_date else None
        return (
            f"HistoricalSnapshot("
            f"symbol={self.symbol!r}, "
            f"snapshot_date={sd!r}, "
            f"price_usd={self.price_usd!r}, "
            f"cycle_tag={self.cycle_tag!r})"
        )
