from abc import ABC, abstractmethod

from app.dto.source_article import SourceArticle
from app.models.news_source import NewsSource


class DiscoveryStrategy(ABC):

    @abstractmethod
    async def discover(
        self,
        news_source: NewsSource,
    ) -> list[SourceArticle]:
        pass
