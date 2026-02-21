"""add_content_text_type

Revision ID: 004
Revises: 003
Create Date: 2025-02-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add content_text_type column."""
    ct_enum = postgresql.ENUM(
        "short_post", "video_description", "cta", "all",
        name="contenttexttype",
    )
    ct_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "generated_content",
        sa.Column(
            "content_text_type",
            ct_enum,
            nullable=False,
            server_default="short_post",
        ),
    )


def downgrade() -> None:
    """Remove content_text_type column."""
    op.drop_column("generated_content", "content_text_type")
    postgresql.ENUM(
        "short_post", "video_description", "cta", "all",
        name="contenttexttype",
    ).drop(op.get_bind(), checkfirst=True)
