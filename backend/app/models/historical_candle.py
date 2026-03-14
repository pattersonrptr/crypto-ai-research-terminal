"""HistoricalCandle model — stores OHLCV candles for backtesting.

Each row represents a single daily (or weekly) OHLCV candle for a given
token symbol.  The composite unique constraint on (symbol, timestamp) makes
all inserts idempotent: duplicate rows are silently ignored via
``ON CONFLICT DO NOTHING``.

This model is part of the Backtesting Engine (Phase 7).
"""

from datetime import datetime

from sqlalchemy import DateTime, Double, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HistoricalCandle(Base):
    """A single OHLCV candle for a cryptocurrency over a given time period."""

    __tablename__ = "historical_candles"

    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", name="uq_historical_candle_symbol_ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    open: Mapped[float] = mapped_column(Double, nullable=False)
    high: Mapped[float] = mapped_column(Double, nullable=False)
    low: Mapped[float] = mapped_column(Double, nullable=False)
    close: Mapped[float] = mapped_column(Double, nullable=False)
    volume_usd: Mapped[float] = mapped_column(Double, nullable=False)
    market_cap_usd: Mapped[float | None] = mapped_column(Double, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"HistoricalCandle("
            f"symbol={self.symbol!r}, "
            f"timestamp={self.timestamp!r}, "
            f"close={self.close!r})"
        )
