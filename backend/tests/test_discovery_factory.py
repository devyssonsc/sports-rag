import pytest

from app.core.exceptions import UnsupportedNewsSourceType
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.services.discovery.factory import DiscoveryFactory
from app.services.discovery.rss_discovery import RSSDiscovery


def test_factory_returns_rss_discovery_for_rss():
    factory = DiscoveryFactory()
    news_source = NewsSource(
        name="Example",
        url="https://example.com/rss",
        type=SourceType.RSS,
    )

    strategy = factory.get(news_source)

    assert isinstance(strategy, RSSDiscovery)


def test_factory_rejects_unsupported_type():
    factory = DiscoveryFactory()
    news_source = NewsSource(
        name="Example",
        url="https://example.com",
        type=SourceType.CRAWL,
    )

    with pytest.raises(UnsupportedNewsSourceType):
        factory.get(news_source)
