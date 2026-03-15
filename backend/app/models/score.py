"""TokenScore model — composite opportunity score for a token.

Phase 9: stores all 11 sub-scores per SCOPE.md §7 and §9.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TokenScore(Base):
    """Composite opportunity score computed for a token at a point in time.

    Stores the full 5-pillar scoring breakdown plus ML-derived probabilities.
    """

    __tablename__ = "token_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id"), nullable=False, index=True)

    # Core scores (always populated)
    fundamental_score: Mapped[float] = mapped_column(Float, nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Fundamental sub-pillars (Phase 9)
    technology_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tokenomics_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    adoption_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dev_activity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    narrative_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Growth, risk, listing, ML (Phase 9)
    growth_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    listing_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cycle_leader_prob: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"TokenScore(id={self.id!r}, token_id={self.token_id!r}, "
            f"opportunity={self.opportunity_score!r})"
        )
