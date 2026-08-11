from datetime import datetime

import httpx

from lxml import etree

from app.core.dates import ensure_utc
from app.core.exceptions import DiscoveryError
from app.core.url_filter import compile_url_filter
from app.dto.source_article import SourceArticle
from app.models.news_source import NewsSource
from app.services.discovery.base import DiscoveryStrategy


class SitemapDiscovery(DiscoveryStrategy):
    """Discovery for XML sitemaps, including Google News sitemaps.

    Reads the ``<url>`` entries of a ``<urlset>`` and builds a SourceArticle from
    each ``<loc>``. When the news sitemap extension is present, the title and
    publication date are taken directly from ``news:title`` /
    ``news:publication_date`` (falling back to ``<lastmod>`` for the date).

    ``article_url_pattern`` is optional here: a news sitemap is already a curated
    list of article URLs. When provided, it is applied as an extra filter
    (include by default, or exclude with a leading ``!``).

    Sitemap-index files (``<sitemapindex>``) are not followed yet.
    """

    TIMEOUT = 15.0

    SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
    NEWS_NS = "http://www.google.com/schemas/sitemap-news/0.9"

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; sports-rag/1.0)"}

    async def discover(
        self,
        news_source: NewsSource,
    ) -> list[SourceArticle]:

        try:
            content = await self._fetch(news_source.url)
            root = etree.fromstring(content)
        except httpx.HTTPError as exc:
            raise DiscoveryError(
                f"Failed to fetch '{news_source.url}': {exc}"
            ) from exc
        except etree.LxmlError as exc:
            raise DiscoveryError(
                f"Failed to parse sitemap from '{news_source.url}': {exc}"
            ) from exc

        ns = {"sm": self.SITEMAP_NS, "news": self.NEWS_NS}

        keep = compile_url_filter(news_source.article_url_pattern)

        articles = []
        seen = set()

        for url_el in root.findall("sm:url", ns):

            loc = (url_el.findtext("sm:loc", namespaces=ns) or "").strip()

            if not loc or loc in seen:
                continue

            if not keep(loc):
                continue

            seen.add(loc)

            title = (
                url_el.findtext("news:news/news:title", namespaces=ns) or ""
            ).strip()

            name = (
                url_el.findtext(
                    "news:news/news:publication/news:name",
                    namespaces=ns,
                )
                or ""
            ).strip()

            published_at = self._parse_date(
                url_el.findtext(
                    "news:news/news:publication_date",
                    namespaces=ns,
                )
                or url_el.findtext("sm:lastmod", namespaces=ns)
            )

            articles.append(
                SourceArticle(
                    title=title,
                    url=loc,
                    summary=None,
                    published_at=published_at,
                    source=name or news_source.name,
                )
            )

        return articles

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None

        try:
            return ensure_utc(datetime.fromisoformat(value.strip()))
        except ValueError:
            return None

    async def _fetch(self, url: str) -> bytes:

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.TIMEOUT,
            headers=self.HEADERS,
        ) as client:

            response = await client.get(url)
            response.raise_for_status()

            return response.content
