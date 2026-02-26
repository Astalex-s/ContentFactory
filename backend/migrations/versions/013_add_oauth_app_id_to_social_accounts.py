"""add_oauth_app_id_to_social_accounts

Revision ID: 013
Revises: 012
Create Date: 2026-02-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: Union[str, Sequence[str], None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add oauth_app_credentials_id to social_accounts."""
    op.add_column(
        "social_accounts",
        sa.Column("oauth_app_credentials_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_social_accounts_oauth_app_credentials_id",
        "social_accounts",
        ["oauth_app_credentials_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove oauth_app_credentials_id from social_accounts."""
    op.drop_index("ix_social_accounts_oauth_app_credentials_id", table_name="social_accounts")
    op.drop_column("social_accounts", "oauth_app_credentials_id")
