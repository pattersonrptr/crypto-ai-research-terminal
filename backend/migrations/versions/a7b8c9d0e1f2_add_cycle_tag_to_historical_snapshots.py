"""add cycle_tag to historical_snapshots

Revision ID: a7b8c9d0e1f2
Revises: f5a6b7c8d9e0
Create Date: 2026-03-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cycle_tag column to historical_snapshots table."""
    op.add_column(
        "historical_snapshots",
        sa.Column("cycle_tag", sa.String(length=40), nullable=True),
    )
    op.create_index(
        "ix_historical_snapshots_cycle_tag",
        "historical_snapshots",
        ["cycle_tag"],
    )


def downgrade() -> None:
    """Remove cycle_tag column from historical_snapshots table."""
    op.drop_index("ix_historical_snapshots_cycle_tag", table_name="historical_snapshots")
    op.drop_column("historical_snapshots", "cycle_tag")
