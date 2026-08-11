from app.core.exceptions import UnsupportedNewsSourceType
from app.models.news_source import NewsSource
from app.models.source_type import SourceType

from app.services.discovery.base import DiscoveryStrategy
from app.services.discovery.html_discovery import HtmlDiscovery
from app.services.discovery.rss_discovery import RSSDiscovery
from app.services.discovery.sitemap_discovery import SitemapDiscovery


class DiscoveryFactory:

    def get(
        self,
        news_source: NewsSource,
    ) -> DiscoveryStrategy:

        match news_source.type:

            case SourceType.RSS:
                return RSSDiscovery()

            case SourceType.CRAWL:
                return HtmlDiscovery()

            case SourceType.SITEMAP:
                return SitemapDiscovery()

        raise UnsupportedNewsSourceType(
            f"Unsupported source type: {news_source.type}"
        )
