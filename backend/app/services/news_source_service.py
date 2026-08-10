import logging

from app.core.exceptions import (
    NewsSourceAlreadyExists,
    NewsSourceNotFound,
    UnsupportedNewsSourceType,
)
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.repositories.news_source_repository import NewsSourceRepository
from app.schemas.news_source import NewsSourceCreate


logger = logging.getLogger(__name__)


class NewsSourceService:
    def __init__(self, repository: NewsSourceRepository):
        self.repository = repository

    def create_news_source(
        self,
        news_source_data: NewsSourceCreate,
    ) -> NewsSource:
        if news_source_data.type != SourceType.RSS:
            raise UnsupportedNewsSourceType(
                f"NewsSource type '{news_source_data.type}' is not supported yet."
            )

        existing_news_source = self.repository.get_by_url(
            news_source_data.url
        )

        if existing_news_source:
            raise NewsSourceAlreadyExists(
                f"NewsSource with URL '{news_source_data.url}' already exists."
            )

        news_source = NewsSource(
            name=news_source_data.name,
            url=news_source_data.url,
            type=news_source_data.type,
        )

        logger.info("Creating news source: %s", news_source.url)

        return self.repository.create(news_source)

    def list_news_sources(self) -> list[NewsSource]:
        return self.repository.list()

    def get(self, news_source_id: int) -> NewsSource:
        news_source = self.repository.get(news_source_id)

        if not news_source:
            raise NewsSourceNotFound()

        return news_source
