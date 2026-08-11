from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    NewsSourceAlreadyExists,
    NewsSourceNotFound,
    UnsupportedNewsSourceType,
)
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.schemas.news_source import NewsSourceCreate
from app.services.news_source_service import NewsSourceService


def make_service():
    repository = AsyncMock()
    return NewsSourceService(repository), repository


async def test_create_rss_news_source():
    service, repository = make_service()
    repository.get_by_url.return_value = None
    repository.create.side_effect = lambda news_source: news_source

    data = NewsSourceCreate(
        name="Example",
        url="https://example.com/rss",
        type=SourceType.RSS,
    )

    result = await service.create_news_source(data)

    repository.get_by_url.assert_awaited_once_with("https://example.com/rss")
    repository.create.assert_awaited_once()
    assert result.name == "Example"
    assert result.url == "https://example.com/rss"
    assert result.type == SourceType.RSS


async def test_create_crawl_is_rejected():
    service, repository = make_service()

    data = NewsSourceCreate(
        name="Example",
        url="https://example.com",
        type=SourceType.CRAWL,
    )

    with pytest.raises(UnsupportedNewsSourceType):
        await service.create_news_source(data)

    repository.create.assert_not_awaited()


async def test_create_duplicate_url_is_rejected():
    service, repository = make_service()
    repository.get_by_url.return_value = NewsSource(
        name="Existing",
        url="https://example.com/rss",
        type=SourceType.RSS,
    )

    data = NewsSourceCreate(
        name="Example",
        url="https://example.com/rss",
        type=SourceType.RSS,
    )

    with pytest.raises(NewsSourceAlreadyExists):
        await service.create_news_source(data)

    repository.create.assert_not_awaited()


async def test_get_missing_news_source_raises_not_found():
    service, repository = make_service()
    repository.get.return_value = None

    with pytest.raises(NewsSourceNotFound):
        await service.get(999)
