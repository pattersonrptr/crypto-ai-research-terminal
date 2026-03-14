"""add historical_candles table

Revision ID: a1b2c3d4e5f6
Revises: e10c91a4be38
Create Date: 2026-03-14 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e10c91a4be38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create historical_candles table."""
    op.create_table(
        "historical_candles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Double(), nullable=False),
        sa.Column("high", sa.Double(), nullable=False),
        sa.Column("low", sa.Double(), nullable=False),
        sa.Column("close", sa.Double(), nullable=False),
        sa.Column("volume_usd", sa.Double(), nullable=False),
        sa.Column("market_cap_usd", sa.Double(), nullable=True),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "timestamp", name="uq_historical_candle_symbol_ts"),
    )
    op.create_index(
        op.f("ix_historical_candles_symbol"),
        "historical_candles",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_historical_candles_timestamp"),
        "historical_candles",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Drop historical_candles table."""
    op.drop_index(op.f("ix_historical_candles_timestamp"), table_name="historical_candles")
    op.drop_index(op.f("ix_historical_candles_symbol"), table_name="historical_candles")
    op.drop_table("historical_candles")
