"""add SITEMAP to source_type enum

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the migration's transaction,
    # so it is executed in an autocommit block. IF NOT EXISTS keeps it
    # idempotent.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'SITEMAP'"
        )


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type without recreating it,
    # so this downgrade is intentionally a no-op.
    pass
