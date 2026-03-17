"""add twitter columns to social_data

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-03-16 23:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add twitter_mentions_24h and twitter_engagement to social_data."""
    op.add_column(
        "social_data",
        sa.Column("twitter_mentions_24h", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "social_data",
        sa.Column("twitter_engagement", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Remove twitter columns from social_data."""
    op.drop_column("social_data", "twitter_engagement")
    op.drop_column("social_data", "twitter_mentions_24h")
