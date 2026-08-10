import feedparser

from app.dto.source_article import SourceArticle

from app.services.discovery.base import DiscoveryStrategy
from app.models.news_source import NewsSource

class RSSDiscovery(DiscoveryStrategy):

    def discover(self, news_source: NewsSource) -> list[SourceArticle]:

        parsed_feed = feedparser.parse(news_source.url)

        articles = []

        for entry in parsed_feed.entries:

            articles.append(
                SourceArticle(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    summary=entry.get("summary"),
                    published_at=None,
                    source=parsed_feed.feed.get("title", ""),
                )
            )

        return articles
