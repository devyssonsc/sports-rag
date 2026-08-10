from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news_source import NewsSource


class NewsSourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, news_source: NewsSource) -> NewsSource:
        self.db.add(news_source)
        self.db.commit()
        self.db.refresh(news_source)
        return news_source

    def get_by_url(self, url: str) -> NewsSource | None:
        statement = select(NewsSource).where(NewsSource.url == url)
        return self.db.scalar(statement)

    def list(self) -> list[NewsSource]:
        statement = select(NewsSource)
        return list(self.db.scalars(statement).all())

    def get(self, news_source_id: int) -> NewsSource | None:
        return (
            self.db.query(NewsSource)
            .filter(NewsSource.id == news_source_id)
            .first()
        )
