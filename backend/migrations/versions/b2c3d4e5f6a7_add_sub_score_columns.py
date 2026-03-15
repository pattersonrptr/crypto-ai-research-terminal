"""add sub-score columns to token_scores

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-18 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLUMNS = [
    "technology_score",
    "tokenomics_score",
    "adoption_score",
    "dev_activity_score",
    "narrative_score",
    "growth_score",
    "risk_score",
    "listing_probability",
    "cycle_leader_prob",
]


def upgrade() -> None:
    """Add 9 sub-score columns to token_scores table (Phase 9)."""
    for col in _NEW_COLUMNS:
        op.add_column(
            "token_scores",
            sa.Column(col, sa.Float(), nullable=False, server_default="0"),
        )
    # Drop the server_default after backfilling existing rows
    for col in _NEW_COLUMNS:
        op.alter_column("token_scores", col, server_default=None)


def downgrade() -> None:
    """Remove 9 sub-score columns from token_scores table."""
    for col in reversed(_NEW_COLUMNS):
        op.drop_column("token_scores", col)
