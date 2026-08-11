from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article


class ArticleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, article: Article) -> Article:
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def get_by_id(self, article_id: int) -> Article | None:
        statement = select(Article).where(Article.id == article_id)
        return await self.db.scalar(statement)

    async def get_by_url(self, url: str) -> Article | None:
        statement = select(Article).where(Article.url == url)
        return await self.db.scalar(statement)

    async def list(self) -> list[Article]:
        statement = select(Article)
        result = await self.db.scalars(statement)
        return list(result.all())

    async def get_by_ids(
        self,
        article_ids: list[int],
    ) -> list[Article]:

        statement = select(Article).where(Article.id.in_(article_ids))
        result = await self.db.scalars(statement)
        return list(result.all())

    async def delete(self, article: Article) -> None:
        await self.db.delete(article)
        await self.db.commit()
