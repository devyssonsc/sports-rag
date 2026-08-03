import feedparser

from app.dto.rss_article import RSSArticle


class RSSService:

    def parse(self, url: str) -> list[RSSArticle]:

        feed = feedparser.parse(url)

        articles = []

        for entry in feed.entries:

            articles.append(
                RSSArticle(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    summary=entry.get("summary"),
                    published_at=None,
                    source=feed.feed.get("title", ""),
                )
            )

        return articles