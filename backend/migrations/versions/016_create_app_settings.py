"""create_app_settings

Revision ID: 016
Revises: 015
Create Date: 2026-02-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, Sequence[str], None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create app_settings table."""
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.execute(
        sa.text("INSERT INTO app_settings (key, value) VALUES ('auto_publish', 'false')")
    )


def downgrade() -> None:
    """Drop app_settings table."""
    op.drop_table("app_settings")
