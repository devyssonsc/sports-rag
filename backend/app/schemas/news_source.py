import re

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.url_filter import validate_url_pattern
from app.models.source_type import SourceType


class NewsSourceCreate(BaseModel):
    name: str
    url: str
    type: SourceType
    article_url_pattern: str | None = None

    @field_validator("article_url_pattern")
    @classmethod
    def _validate_regex(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                validate_url_pattern(value)
            except re.error as exc:
                raise ValueError(
                    f"Invalid regex for article_url_pattern: {exc}"
                )
        return value

    @model_validator(mode="after")
    def _require_pattern_for_crawl(self) -> "NewsSourceCreate":
        if self.type == SourceType.CRAWL and not self.article_url_pattern:
            raise ValueError(
                "article_url_pattern is required for CRAWL sources."
            )
        return self


class NewsSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    type: SourceType
    article_url_pattern: str | None
    last_fetched_at: datetime | None
    created_at: datetime
