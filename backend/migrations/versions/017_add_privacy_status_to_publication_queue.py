"""add privacy_status to publication_queue

Revision ID: 017
Revises: 016
Create Date: 2026-03-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: Union[str, Sequence[str], None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add privacy_status for video visibility (private/public)."""
    op.add_column(
        "publication_queue",
        sa.Column("privacy_status", sa.String(32), nullable=False, server_default="private"),
    )


def downgrade() -> None:
    """Remove privacy_status."""
    op.drop_column("publication_queue", "privacy_status")
