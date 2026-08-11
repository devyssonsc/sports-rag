from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news_source import NewsSource


class NewsSourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, news_source: NewsSource) -> NewsSource:
        self.db.add(news_source)
        await self.db.commit()
        await self.db.refresh(news_source)
        return news_source

    async def get_by_url(self, url: str) -> NewsSource | None:
        statement = select(NewsSource).where(NewsSource.url == url)
        return await self.db.scalar(statement)

    async def list(self) -> list[NewsSource]:
        statement = select(NewsSource)
        result = await self.db.scalars(statement)
        return list(result.all())

    async def get(self, news_source_id: int) -> NewsSource | None:
        statement = select(NewsSource).where(
            NewsSource.id == news_source_id
        )
        return await self.db.scalar(statement)
