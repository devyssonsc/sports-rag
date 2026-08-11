from datetime import datetime
from dataclasses import dataclass


@dataclass
class SourceArticle:
    """Article discovered by a DiscoveryStrategy.

    ``published_at`` is either ``None`` or a timezone-aware datetime in UTC.
    Every strategy is responsible for normalizing its source's date format
    (via ``app.core.dates``) before setting it.
    """

    title: str
    url: str
    summary: str | None
    published_at: datetime | None
    source: str