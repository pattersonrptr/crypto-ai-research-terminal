"""Alert model — a triggered alert for a token."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    """A triggered alert for a token (e.g. listing signal, whale accumulation)."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tokens.id"),
        nullable=True,
        index=True,
    )
    token_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    alert_metadata: Mapped[dict | None] = mapped_column(  # type: ignore[type-arg]
        "metadata",
        JSONB,
        nullable=True,
    )
    sent_telegram: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"Alert(id={self.id!r}, token_id={self.token_id!r}, type={self.alert_type!r})"
