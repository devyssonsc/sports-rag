from urllib.parse import urljoin

import httpx

from lxml import etree
from lxml import html as lxml_html

from app.core.exceptions import DiscoveryError
from app.core.url_filter import compile_url_filter
from app.dto.source_article import SourceArticle
from app.models.news_source import NewsSource
from app.services.discovery.base import DiscoveryStrategy


class HtmlDiscovery(DiscoveryStrategy):
    """Lightweight discovery for server-rendered (plain HTML) listing pages.

    Fetches the source URL with a simple HTTP GET (no browser), extracts the
    anchor links and keeps only those matching the source's
    ``article_url_pattern`` regex. Sites that render links via JavaScript are
    out of scope here and will be handled by a future browser-based strategy.
    """

    TIMEOUT = 15.0

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; sports-rag/1.0)"}

    async def discover(
        self,
        news_source: NewsSource,
    ) -> list[SourceArticle]:

        keep = compile_url_filter(news_source.article_url_pattern)

        try:
            base_url, html_text = await self._fetch_html(news_source.url)
            document = lxml_html.fromstring(html_text)
        except httpx.HTTPError as exc:
            raise DiscoveryError(
                f"Failed to fetch '{news_source.url}': {exc}"
            ) from exc
        except etree.LxmlError as exc:
            raise DiscoveryError(
                f"Failed to parse HTML from '{news_source.url}': {exc}"
            ) from exc

        articles = []
        seen = set()

        for anchor in document.xpath("//a[@href]"):

            href = anchor.get("href")

            absolute_url = urljoin(base_url, href)

            if not keep(absolute_url):
                continue

            if absolute_url in seen:
                continue

            seen.add(absolute_url)

            title = (anchor.text_content() or "").strip()

            articles.append(
                SourceArticle(
                    title=title,
                    url=absolute_url,
                    summary=None,
                    published_at=None,
                    source=news_source.name,
                )
            )

        return articles

    async def _fetch_html(self, url: str) -> tuple[str, str]:

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.TIMEOUT,
            headers=self.HEADERS,
        ) as client:

            response = await client.get(url)
            response.raise_for_status()

            return str(response.url), response.text
