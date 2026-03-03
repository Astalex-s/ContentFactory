"""add vk_group_id to publication_queue for VK text posts to groups

Revision ID: 018_vk_group_id
Revises: 017_add_privacy_status_to_publication_queue
Create Date: 2025-03-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: str | None = "017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "publication_queue",
        sa.Column("vk_group_id", sa.String(32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("publication_queue", "vk_group_id")
