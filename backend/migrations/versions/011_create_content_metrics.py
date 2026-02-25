"""create_content_metrics

Revision ID: 011
Revises: 010
Create Date: 2026-02-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, Sequence[str], None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create content_metrics table."""
    op.create_table(
        "content_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "content_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generated_content.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ctr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "marketplace_clicks", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_metrics_content_id",
        "content_metrics",
        ["content_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_metrics_platform",
        "content_metrics",
        ["platform"],
        unique=False,
    )
    op.create_index(
        "ix_content_metrics_recorded_at",
        "content_metrics",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop content_metrics table."""
    op.drop_index("ix_content_metrics_recorded_at", table_name="content_metrics")
    op.drop_index("ix_content_metrics_platform", table_name="content_metrics")
    op.drop_index("ix_content_metrics_content_id", table_name="content_metrics")
    op.drop_table("content_metrics")
