"""add_image_data

Revision ID: 005
Revises: 004
Create Date: 2025-02-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, Sequence[str], None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add image_data column (BYTEA) for storing product images in DB."""
    op.add_column(
        "products",
        sa.Column("image_data", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    """Remove image_data column."""
    op.drop_column("products", "image_data")
