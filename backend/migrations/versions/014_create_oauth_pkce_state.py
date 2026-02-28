"""create_oauth_pkce_state

Revision ID: 014
Revises: 013
Create Date: 2026-02-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: Union[str, Sequence[str], None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_pkce_state table for PKCE code_verifier storage."""
    op.create_table(
        "oauth_pkce_state",
        sa.Column("state", sa.String(512), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("state"),
    )


def downgrade() -> None:
    """Drop oauth_pkce_state table."""
    op.drop_table("oauth_pkce_state")
