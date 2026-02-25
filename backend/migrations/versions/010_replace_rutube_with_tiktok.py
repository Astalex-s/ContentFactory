"""Replace rutube with tiktok in platform enums

Revision ID: 010
Revises: 009
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op


revision: str = "010"
down_revision: Union[str, Sequence[str], None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace 'rutube' with 'tiktok' in platform enums (safe for fresh installs)."""
    op.execute("ALTER TYPE socialplatform ADD VALUE IF NOT EXISTS 'tiktok'")
    op.execute("ALTER TYPE platform ADD VALUE IF NOT EXISTS 'tiktok'")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'socialplatform'::regtype AND enumlabel = 'rutube') THEN
                UPDATE social_accounts SET platform = 'tiktok' WHERE platform = 'rutube';
            END IF;
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'platform'::regtype AND enumlabel = 'rutube') THEN
                UPDATE generated_content SET platform = 'tiktok' WHERE platform = 'rutube';
                UPDATE publication_queue SET platform = 'tiktok' WHERE platform = 'rutube';
            END IF;
        END$$;
    """)


def downgrade() -> None:
    """Revert: this is a one-way migration (PostgreSQL cannot remove enum values)."""
    pass
