"""create social_accounts

Revision ID: 006
Revises: 005
Create Date: 2025-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, Sequence[str], None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create social_accounts table."""
    socialplatform_enum = postgresql.ENUM(
        "youtube", "vk", "rutube", name="socialplatform", create_type=False
    )
    socialplatform_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "social_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", socialplatform_enum, nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_social_accounts_platform", "social_accounts", ["platform"], unique=False)
    op.create_index("ix_social_accounts_user_id", "social_accounts", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop social_accounts table."""
    op.drop_index("ix_social_accounts_user_id", table_name="social_accounts")
    op.drop_index("ix_social_accounts_platform", table_name="social_accounts")
    op.drop_table("social_accounts")
    socialplatform_enum = postgresql.ENUM("youtube", "vk", "rutube", name="socialplatform")
    socialplatform_enum.drop(op.get_bind(), checkfirst=True)
