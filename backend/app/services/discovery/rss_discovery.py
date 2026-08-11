import asyncio

import feedparser

from app.core.dates import from_struct_time
from app.dto.source_article import SourceArticle

from app.services.discovery.base import DiscoveryStrategy
from app.models.news_source import NewsSource

class RSSDiscovery(DiscoveryStrategy):

    async def discover(self, news_source: NewsSource) -> list[SourceArticle]:

        parsed_feed = await asyncio.to_thread(
            feedparser.parse,
            news_source.url,
        )

        articles = []

        for entry in parsed_feed.entries:

            published_at = from_struct_time(
                entry.get("published_parsed")
                or entry.get("updated_parsed")
            )

            articles.append(
                SourceArticle(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    summary=entry.get("summary"),
                    published_at=published_at,
                    source=parsed_feed.feed.get("title", ""),
                )
            )

        return articles
