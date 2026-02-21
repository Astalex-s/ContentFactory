"""create_products_table

Revision ID: 001
Revises:
Create Date: 2025-02-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("popularity_score", sa.Float(), nullable=True),
        sa.Column("marketplace_url", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_category", "products", ["category"], unique=False)
    op.create_index("ix_products_price", "products", ["price"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_products_price", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")
