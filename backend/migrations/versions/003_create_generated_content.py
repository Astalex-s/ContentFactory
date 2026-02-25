"""create_generated_content

Revision ID: 003
Revises: 002
Create Date: 2025-02-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create generated_content table."""
    content_type_enum = postgresql.ENUM(
        "text", "image", "video", name="contenttype", create_type=False
    )
    content_status_enum = postgresql.ENUM(
        "draft", "ready", "published", name="contentstatus", create_type=False
    )
    platform_enum = postgresql.ENUM(
        "youtube", "vk", "tiktok", name="platform", create_type=False
    )
    tone_enum = postgresql.ENUM(
        "neutral", "emotional", "expert", name="tone", create_type=False
    )

    content_type_enum.create(op.get_bind(), checkfirst=True)
    content_status_enum.create(op.get_bind(), checkfirst=True)
    platform_enum.create(op.get_bind(), checkfirst=True)
    tone_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "generated_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            content_type_enum,
            nullable=False,
        ),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column(
            "status",
            content_status_enum,
            nullable=False,
        ),
        sa.Column("content_variant", sa.Integer(), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("tone", tone_enum, nullable=False),
        sa.Column("ai_model", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_content_product_id",
        "generated_content",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_generated_content_platform",
        "generated_content",
        ["platform"],
        unique=False,
    )


def downgrade() -> None:
    """Drop generated_content table."""
    op.drop_index("ix_generated_content_platform", table_name="generated_content")
    op.drop_index("ix_generated_content_product_id", table_name="generated_content")
    op.drop_table("generated_content")

    tone_enum = postgresql.ENUM("neutral", "emotional", "expert", name="tone")
    platform_enum = postgresql.ENUM("youtube", "vk", "tiktok", name="platform")
    content_status_enum = postgresql.ENUM(
        "draft", "ready", "published", name="contentstatus"
    )
    content_type_enum = postgresql.ENUM(
        "text", "image", "video", name="contenttype"
    )
    tone_enum.drop(op.get_bind(), checkfirst=True)
    platform_enum.drop(op.get_bind(), checkfirst=True)
    content_status_enum.drop(op.get_bind(), checkfirst=True)
    content_type_enum.drop(op.get_bind(), checkfirst=True)
