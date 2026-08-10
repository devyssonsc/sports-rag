from datetime import datetime
from dataclasses import dataclass


@dataclass
class SourceArticle:
    title: str
    url: str
    summary: str | None
    published_at: datetime | None
    source: str