"""SocialData model — social-media metrics for a token."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialData(Base):
    """Social-media metrics collected for a token at a point in time."""

    __tablename__ = "social_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id"), nullable=False, index=True)
    reddit_subscribers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reddit_posts_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    twitter_mentions_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    twitter_engagement: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"SocialData(id={self.id!r}, token_id={self.token_id!r})"
