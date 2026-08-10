from abc import ABC, abstractmethod

from app.dto.source_article import SourceArticle
from app.models.feed import Feed


class DiscoveryStrategy(ABC):

    @abstractmethod
    def discover(
        self,
        feed: Feed,
    ) -> list[SourceArticle]:
        pass