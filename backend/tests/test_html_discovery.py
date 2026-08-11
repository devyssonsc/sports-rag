from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.exceptions import DiscoveryError
from app.dto.source_article import SourceArticle
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.services.discovery.html_discovery import HtmlDiscovery


HTML = """
<html><body>
  <a href="/futebol/2026/08/benfica-vence">Benfica vence</a>
  <a href="/futebol/tag/benfica">Tag Benfica</a>
  <a href="https://site.com/futebol/2026/08/porto-empata">Porto empata</a>
  <a href="/economia/algo">Economia</a>
  <a href="/futebol/2026/08/benfica-vence">Benfica vence (dup)</a>
</body></html>
"""


def make_source():
    return NewsSource(
        name="Site",
        url="https://site.com/futebol",
        type=SourceType.CRAWL,
        article_url_pattern=r"^https://site\.com/futebol/\d{4}/\d{2}/[a-z0-9-]+$",
    )


async def test_html_discovery_filters_by_pattern():
    discovery = HtmlDiscovery()
    discovery._fetch_html = AsyncMock(
        return_value=("https://site.com/futebol", HTML)
    )

    articles = await discovery.discover(make_source())

    urls = [a.url for a in articles]

    assert "https://site.com/futebol/2026/08/benfica-vence" in urls
    assert "https://site.com/futebol/2026/08/porto-empata" in urls
    # tag / economia links must be filtered out
    assert all("/tag/" not in url for url in urls)
    assert all("/economia/" not in url for url in urls)
    # deduplicated
    assert len(urls) == len(set(urls))
    assert len(articles) == 2


async def test_html_discovery_raises_discovery_error_on_fetch_failure():
    discovery = HtmlDiscovery()
    discovery._fetch_html = AsyncMock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(DiscoveryError):
        await discovery.discover(make_source())


async def test_html_discovery_returns_source_articles():
    discovery = HtmlDiscovery()
    discovery._fetch_html = AsyncMock(
        return_value=("https://site.com/futebol", HTML)
    )

    articles = await discovery.discover(make_source())

    assert all(isinstance(a, SourceArticle) for a in articles)
    assert all(a.source == "Site" for a in articles)
    assert all(a.published_at is None for a in articles)

    benfica = next(
        a for a in articles if a.url.endswith("benfica-vence")
    )
    assert benfica.title == "Benfica vence"
