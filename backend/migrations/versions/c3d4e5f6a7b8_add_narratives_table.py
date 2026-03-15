"""add narratives table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-15 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the narratives table for detected market narrative clusters."""
    op.create_table(
        "narratives",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("momentum_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trend", sa.String(20), nullable=False, server_default="'stable'"),
        sa.Column("keywords", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("token_symbols", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_narratives_snapshot_date", "narratives", ["snapshot_date"])


def downgrade() -> None:
    """Drop the narratives table."""
    op.drop_index("ix_narratives_snapshot_date", table_name="narratives")
    op.drop_table("narratives")
