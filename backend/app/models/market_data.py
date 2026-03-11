"""MarketData model — point-in-time market snapshot for a token."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketData(Base):
    """A single market data snapshot collected for a token."""

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id"), nullable=False, index=True)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    market_cap_usd: Mapped[float] = mapped_column(Float, nullable=True)
    volume_24h_usd: Mapped[float] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ath_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    circulating_supply: Mapped[float | None] = mapped_column(Float, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"MarketData(id={self.id!r}, token_id={self.token_id!r}, price={self.price_usd!r})"
