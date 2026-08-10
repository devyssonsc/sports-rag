from app.models.feed import Feed
from app.models.source_type import SourceType

from app.services.discovery.base import DiscoveryStrategy
from app.services.discovery.rss_discovery import RSSDiscovery


class DiscoveryFactory:

    def get(
        self,
        feed: Feed,
    ) -> DiscoveryStrategy:

        match feed.type:

            case SourceType.RSS:
                return RSSDiscovery()

        raise ValueError(
            f"Unsupported source type: {feed.type}"
        )