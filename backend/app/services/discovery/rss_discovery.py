import feedparser

from app.dto.source_article import SourceArticle

from app.services.discovery.base import DiscoveryStrategy
from app.models.feed import Feed

class RSSDiscovery(DiscoveryStrategy):

    def discover(self, feed: Feed) -> list[SourceArticle]:

        parsed_feed = feedparser.parse(feed.url)

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