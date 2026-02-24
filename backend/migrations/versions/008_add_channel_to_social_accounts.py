"""add channel_id and channel_title to social_accounts

Revision ID: 008
Revises: 007
Create Date: 2025-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, Sequence[str], None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add channel_id and channel_title for YouTube channel identification."""
    op.add_column(
        "social_accounts",
        sa.Column("channel_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "social_accounts",
        sa.Column("channel_title", sa.String(256), nullable=True),
    )
    op.create_index(
        "ix_social_accounts_channel_id",
        "social_accounts",
        ["channel_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove channel columns."""
    op.drop_index("ix_social_accounts_channel_id", table_name="social_accounts")
    op.drop_column("social_accounts", "channel_title")
    op.drop_column("social_accounts", "channel_id")
