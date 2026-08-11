from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.core.exceptions import (
    NewsSourceAlreadyExists,
    NewsSourceNotFound,
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
    assert result.type == SourceType.RSS
    assert result.article_url_pattern is None


async def test_create_crawl_with_pattern_succeeds():
    service, repository = make_service()
    repository.get_by_url.return_value = None
    repository.create.side_effect = lambda news_source: news_source

    data = NewsSourceCreate(
        name="Example",
        url="https://example.com/futebol",
        type=SourceType.CRAWL,
        article_url_pattern=r"^https://example\.com/futebol/\d+$",
    )

    result = await service.create_news_source(data)

    repository.create.assert_awaited_once()
    assert result.type == SourceType.CRAWL
    assert result.article_url_pattern == r"^https://example\.com/futebol/\d+$"


def test_crawl_requires_article_url_pattern():
    with pytest.raises(ValidationError):
        NewsSourceCreate(
            name="Example",
            url="https://example.com/futebol",
            type=SourceType.CRAWL,
        )


def test_invalid_regex_is_rejected():
    with pytest.raises(ValidationError):
        NewsSourceCreate(
            name="Example",
            url="https://example.com/futebol",
            type=SourceType.CRAWL,
            article_url_pattern="[unclosed(",
        )


def test_sitemap_does_not_require_pattern():
    # A SITEMAP source is already a curated list; the pattern is optional.
    data = NewsSourceCreate(
        name="Example",
        url="https://example.com/sitemap_news.xml",
        type=SourceType.SITEMAP,
    )

    assert data.article_url_pattern is None


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
