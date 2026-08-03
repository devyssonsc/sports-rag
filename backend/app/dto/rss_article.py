from datetime import datetime
from dataclasses import dataclass


@dataclass
class RSSArticle:
    title: str
    url: str
    summary: str | None
    published_at: datetime | None
    source: str