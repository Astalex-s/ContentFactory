"""add_approved_for_publication

Revision ID: 015
Revises: 014
Create Date: 2026-02-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, Sequence[str], None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add approved_for_publication to generated_content."""
    op.add_column(
        "generated_content",
        sa.Column("approved_for_publication", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Remove approved_for_publication from generated_content."""
    op.drop_column("generated_content", "approved_for_publication")
