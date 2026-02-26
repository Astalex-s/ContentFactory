"""create_oauth_app_credentials

Revision ID: 012
Revises: 011
Create Date: 2026-02-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, Sequence[str], None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_app_credentials table. Uses existing socialplatform enum."""
    socialplatform_enum = postgresql.ENUM(
        "youtube", "vk", "tiktok", name="socialplatform", create_type=False
    )
    
    op.create_table(
        "oauth_app_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "platform",
            socialplatform_enum,
            nullable=False,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("client_id", sa.String(512), nullable=False),
        sa.Column("client_secret", sa.Text(), nullable=False),
        sa.Column("redirect_uri", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_app_credentials_user_id",
        "oauth_app_credentials",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_app_credentials_platform",
        "oauth_app_credentials",
        ["platform"],
        unique=False,
    )


def downgrade() -> None:
    """Drop oauth_app_credentials table."""
    op.drop_index("ix_oauth_app_credentials_platform", table_name="oauth_app_credentials")
    op.drop_index("ix_oauth_app_credentials_user_id", table_name="oauth_app_credentials")
    op.drop_table("oauth_app_credentials")
