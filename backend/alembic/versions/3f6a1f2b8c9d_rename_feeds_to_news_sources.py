"""rename feeds to news sources

Revision ID: 3f6a1f2b8c9d
Revises: 9eba7ba83165
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f6a1f2b8c9d"
down_revision: Union[str, Sequence[str], None] = "9eba7ba83165"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "articles_feed_id_fkey",
        "articles",
        type_="foreignkey",
    )

    op.rename_table("feeds", "news_sources")

    op.alter_column(
        "articles",
        "feed_id",
        new_column_name="news_source_id",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    op.create_foreign_key(
        "articles_news_source_id_fkey",
        "articles",
        "news_sources",
        ["news_source_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "articles_news_source_id_fkey",
        "articles",
        type_="foreignkey",
    )

    op.alter_column(
        "articles",
        "news_source_id",
        new_column_name="feed_id",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    op.rename_table("news_sources", "feeds")

    op.create_foreign_key(
        "articles_feed_id_fkey",
        "articles",
        "feeds",
        ["feed_id"],
        ["id"],
    )
