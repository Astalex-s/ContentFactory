"""create publication_queue

Revision ID: 007
Revises: 006
Create Date: 2025-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, Sequence[str], None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create publication_queue table."""
    publicationstatus_enum = postgresql.ENUM(
        "pending", "processing", "published", "failed",
        name="publicationstatus", create_type=False
    )
    publicationstatus_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "publication_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", publicationstatus_enum, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("platform_video_id", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["social_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["generated_content.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publication_queue_account_id", "publication_queue", ["account_id"], unique=False)
    op.create_index("ix_publication_queue_content_id", "publication_queue", ["content_id"], unique=False)
    op.create_index("ix_publication_queue_platform", "publication_queue", ["platform"], unique=False)
    op.create_index("ix_publication_queue_status", "publication_queue", ["status"], unique=False)


def downgrade() -> None:
    """Drop publication_queue table."""
    op.drop_index("ix_publication_queue_status", table_name="publication_queue")
    op.drop_index("ix_publication_queue_platform", table_name="publication_queue")
    op.drop_index("ix_publication_queue_content_id", table_name="publication_queue")
    op.drop_index("ix_publication_queue_account_id", table_name="publication_queue")
    op.drop_table("publication_queue")
    publicationstatus_enum = postgresql.ENUM(
        "pending", "processing", "published", "failed", name="publicationstatus"
    )
    publicationstatus_enum.drop(op.get_bind(), checkfirst=True)
