"""add title and description to publication_queue

Revision ID: 009
Revises: 008
Create Date: 2025-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, Sequence[str], None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add title and description for video metadata."""
    op.add_column(
        "publication_queue",
        sa.Column("title", sa.String(256), nullable=True),
    )
    op.add_column(
        "publication_queue",
        sa.Column("description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove title and description."""
    op.drop_column("publication_queue", "description")
    op.drop_column("publication_queue", "title")
