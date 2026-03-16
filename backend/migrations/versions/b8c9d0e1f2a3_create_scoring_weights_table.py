"""create scoring_weights table

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-03-16 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scoring_weights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fundamental", sa.Float(), nullable=False),
        sa.Column("growth", sa.Float(), nullable=False),
        sa.Column("narrative", sa.Float(), nullable=False),
        sa.Column("listing", sa.Float(), nullable=False),
        sa.Column("risk", sa.Float(), nullable=False),
        sa.Column("source_cycle", sa.String(60), nullable=True),
        sa.Column("precision_at_k", sa.Float(), nullable=True),
        sa.Column("k", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("scoring_weights")
