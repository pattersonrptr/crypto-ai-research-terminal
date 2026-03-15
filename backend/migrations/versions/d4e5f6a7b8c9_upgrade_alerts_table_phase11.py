"""upgrade alerts table phase11

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-10 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 11 columns to alerts table and make token_id nullable."""
    # Make token_id nullable (for system-wide alerts like DAILY_REPORT)
    op.alter_column(
        "alerts",
        "token_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # Add new columns
    op.add_column("alerts", sa.Column("token_symbol", sa.String(20), nullable=True))
    op.add_column("alerts", sa.Column("metadata", JSONB, nullable=True))
    op.add_column(
        "alerts",
        sa.Column("sent_telegram", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "alerts",
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "alerts",
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add index on alert_type for filtering queries
    op.create_index(op.f("ix_alerts_alert_type"), "alerts", ["alert_type"], unique=False)


def downgrade() -> None:
    """Remove Phase 11 columns from alerts table."""
    op.drop_index(op.f("ix_alerts_alert_type"), table_name="alerts")
    op.drop_column("alerts", "acknowledged_at")
    op.drop_column("alerts", "acknowledged")
    op.drop_column("alerts", "sent_telegram")
    op.drop_column("alerts", "metadata")
    op.drop_column("alerts", "token_symbol")

    op.alter_column(
        "alerts",
        "token_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
