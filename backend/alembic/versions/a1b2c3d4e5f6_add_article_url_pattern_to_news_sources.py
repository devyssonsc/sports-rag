"""add article_url_pattern to news_sources

Revision ID: a1b2c3d4e5f6
Revises: 3f6a1f2b8c9d
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "3f6a1f2b8c9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "news_sources",
        sa.Column("article_url_pattern", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("news_sources", "article_url_pattern")
