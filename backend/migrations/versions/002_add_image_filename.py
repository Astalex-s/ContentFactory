"""add_image_filename

Revision ID: 002
Revises: 001
Create Date: 2025-02-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add image_filename column and populate for existing products."""
    op.add_column(
        "products",
        sa.Column("image_filename", sa.String(128), nullable=True),
    )
    # Populate: assign product_00..product_18 by created_at order (wrap at 19)
    op.execute(
        sa.text("""
            WITH ordered AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) - 1 AS rn
                FROM products
            )
            UPDATE products p
            SET image_filename = 'product_' || LPAD((o.rn % 19)::text, 2, '0') || '.png'
            FROM ordered o
            WHERE p.id = o.id
        """)
    )


def downgrade() -> None:
    """Remove image_filename column."""
    op.drop_column("products", "image_filename")
