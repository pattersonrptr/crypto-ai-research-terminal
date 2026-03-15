"""add ai_analyses table

Revision ID: f5a6b7c8d9e0
Revises: 3587d61f0e41
Create Date: 2026-06-20 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "3587d61f0e41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the ai_analyses table for cached AI-generated analysis."""
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "token_id",
            sa.Integer(),
            sa.ForeignKey("tokens.id"),
            nullable=False,
        ),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_analyses_token_id", "ai_analyses", ["token_id"])
    op.create_index("ix_ai_analyses_analysis_type", "ai_analyses", ["analysis_type"])


def downgrade() -> None:
    """Drop the ai_analyses table."""
    op.drop_index("ix_ai_analyses_analysis_type", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_token_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")
