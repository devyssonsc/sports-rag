import pytest

from app.core.exceptions import UnsupportedNewsSourceType
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.services.discovery.factory import DiscoveryFactory
from app.services.discovery.html_discovery import HtmlDiscovery
from app.services.discovery.rss_discovery import RSSDiscovery
from app.services.discovery.sitemap_discovery import SitemapDiscovery


def test_factory_returns_rss_discovery_for_rss():
    factory = DiscoveryFactory()
    news_source = NewsSource(
        name="Example",
        url="https://example.com/rss",
        type=SourceType.RSS,
    )

    strategy = factory.get(news_source)

    assert isinstance(strategy, RSSDiscovery)


def test_factory_returns_html_discovery_for_crawl():
    factory = DiscoveryFactory()
    news_source = NewsSource(
        name="Example",
        url="https://example.com/futebol",
        type=SourceType.CRAWL,
        article_url_pattern=r"^https://example\.com/futebol/\d+$",
    )

    strategy = factory.get(news_source)

    assert isinstance(strategy, HtmlDiscovery)


def test_factory_returns_sitemap_discovery_for_sitemap():
    factory = DiscoveryFactory()
    news_source = NewsSource(
        name="Example",
        url="https://example.com/sitemap_news.xml",
        type=SourceType.SITEMAP,
    )

    strategy = factory.get(news_source)

    assert isinstance(strategy, SitemapDiscovery)


def test_factory_rejects_unsupported_type():
    factory = DiscoveryFactory()
    news_source = NewsSource(
        name="Example",
        url="https://example.com",
        type=SourceType.RSS,
    )
    # Simulate a source type with no registered strategy.
    news_source.type = "UNKNOWN"

    with pytest.raises(UnsupportedNewsSourceType):
        factory.get(news_source)
