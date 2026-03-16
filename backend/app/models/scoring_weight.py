"""ScoringWeight model — persisted calibrated pillar weights.

Stores weight sets discovered by the backtesting calibrator.
Only one row should have ``is_active=True`` at a time — the active
set is used by :class:`OpportunityEngine` when computing composite scores.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScoringWeight(Base):
    """Persisted pillar weight configuration.

    Attributes:
        fundamental: Weight for the fundamental sub-score.
        growth: Weight for the growth sub-score.
        narrative: Weight for the narrative sub-score.
        listing: Weight for the listing sub-score.
        risk: Weight for the risk sub-score.
        source_cycle: Cycle name that produced these weights (e.g. ``"cycle_2_2019_2021"``).
        precision_at_k: Best Precision@K achieved with these weights.
        k: The K value used during calibration.
        is_active: Whether this weight set is currently active.
    """

    __tablename__ = "scoring_weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    fundamental: Mapped[float] = mapped_column(Float, nullable=False)
    growth: Mapped[float] = mapped_column(Float, nullable=False)
    narrative: Mapped[float] = mapped_column(Float, nullable=False)
    listing: Mapped[float] = mapped_column(Float, nullable=False)
    risk: Mapped[float] = mapped_column(Float, nullable=False)

    source_cycle: Mapped[str | None] = mapped_column(String(60), nullable=True)
    precision_at_k: Mapped[float | None] = mapped_column(Float, nullable=True)
    k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def total(self) -> float:
        """Sum of all pillar weights."""
        return self.fundamental + self.growth + self.narrative + self.listing + self.risk

    def to_weight_set(self) -> "WeightSet":
        """Convert to a :class:`WeightSet` for use by the scorer."""
        from app.backtesting.weight_calibrator import WeightSet

        return WeightSet(
            fundamental=self.fundamental,
            growth=self.growth,
            narrative=self.narrative,
            listing=self.listing,
            risk=self.risk,
        )

    def __repr__(self) -> str:
        return (
            f"ScoringWeight(id={self.id}, "
            f"f={self.fundamental}, g={self.growth}, n={self.narrative}, "
            f"l={self.listing}, r={self.risk}, "
            f"active={self.is_active})"
        )
