"""add category column to tokens

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
Create Date: 2026-03-17 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add category column to tokens table."""
    op.add_column(
        "tokens",
        sa.Column("category", sa.String(50), nullable=True),
    )
    op.create_index("ix_tokens_category", "tokens", ["category"])


def downgrade() -> None:
    """Remove category column from tokens table."""
    op.drop_index("ix_tokens_category", table_name="tokens")
    op.drop_column("tokens", "category")
