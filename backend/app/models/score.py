"""TokenScore model — composite opportunity score for a token."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TokenScore(Base):
    """Composite opportunity score computed for a token at a point in time."""

    __tablename__ = "token_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id"), nullable=False, index=True)
    fundamental_score: Mapped[float] = mapped_column(Float, nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"TokenScore(id={self.id!r}, token_id={self.token_id!r}, "
            f"opportunity={self.opportunity_score!r})"
        )
