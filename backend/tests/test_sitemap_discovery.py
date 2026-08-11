from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.exceptions import DiscoveryError
from app.dto.source_article import SourceArticle
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.services.discovery.sitemap_discovery import SitemapDiscovery


SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  <url>
    <loc>https://site.com/football/news/1/article-a</loc>
    <news:news>
      <news:publication>
        <news:name>SkySports</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-08-11T12:22:00+01:00</news:publication_date>
      <news:title>Article A</news:title>
    </news:news>
  </url>
  <url>
    <loc>https://site.com/other/2/article-b</loc>
    <lastmod>2026-08-10</lastmod>
  </url>
</urlset>
""".encode("utf-8")


def make_source(pattern: str | None = None):
    return NewsSource(
        name="My Sitemap Source",
        url="https://site.com/sitemap_news.xml",
        type=SourceType.SITEMAP,
        article_url_pattern=pattern,
    )


async def test_sitemap_extracts_news_metadata():
    discovery = SitemapDiscovery()
    discovery._fetch = AsyncMock(return_value=SAMPLE)

    articles = await discovery.discover(make_source())

    assert len(articles) == 2
    assert all(isinstance(a, SourceArticle) for a in articles)

    a = next(x for x in articles if x.url.endswith("article-a"))
    assert a.title == "Article A"
    assert a.source == "SkySports"
    assert a.published_at is not None
    assert a.published_at.tzinfo is not None
    assert (a.published_at.year, a.published_at.month, a.published_at.day) == (
        2026,
        8,
        11,
    )


async def test_sitemap_falls_back_to_source_name_and_lastmod():
    discovery = SitemapDiscovery()
    discovery._fetch = AsyncMock(return_value=SAMPLE)

    articles = await discovery.discover(make_source())

    b = next(x for x in articles if x.url.endswith("article-b"))
    # no news:title -> empty; no news:name -> falls back to the source name
    assert b.title == ""
    assert b.source == "My Sitemap Source"
    # date comes from <lastmod>
    assert b.published_at is not None
    assert (b.published_at.year, b.published_at.month, b.published_at.day) == (
        2026,
        8,
        10,
    )


async def test_sitemap_exclude_pattern_drops_matches():
    discovery = SitemapDiscovery()
    discovery._fetch = AsyncMock(return_value=SAMPLE)

    # "!/other/" keeps everything except URLs containing /other/
    articles = await discovery.discover(make_source(pattern=r"!/other/"))

    assert len(articles) == 1
    assert articles[0].url.endswith("article-a")


async def test_sitemap_raises_discovery_error_on_fetch_failure():
    discovery = SitemapDiscovery()
    discovery._fetch = AsyncMock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(DiscoveryError):
        await discovery.discover(make_source())


async def test_sitemap_raises_discovery_error_on_invalid_xml():
    discovery = SitemapDiscovery()
    discovery._fetch = AsyncMock(return_value=b"<<< not valid xml >>>")

    with pytest.raises(DiscoveryError):
        await discovery.discover(make_source())


async def test_sitemap_optional_pattern_filters():
    discovery = SitemapDiscovery()
    discovery._fetch = AsyncMock(return_value=SAMPLE)

    articles = await discovery.discover(
        make_source(pattern=r"^https://site\.com/football/news/")
    )

    assert len(articles) == 1
    assert articles[0].url.endswith("article-a")
