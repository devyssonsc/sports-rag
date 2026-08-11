from unittest.mock import AsyncMock

from app.dto.source_article import SourceArticle
from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.services.ingestion_service import IngestionService


def make_service():
    article_repository = AsyncMock()
    article_content_service = AsyncMock()
    chunk_service = AsyncMock()
    embedding_service = AsyncMock()
    vector_repository = AsyncMock()

    service = IngestionService(
        article_repository,
        article_content_service,
        chunk_service,
        embedding_service,
        vector_repository,
    )
    return service, {
        "article_repository": article_repository,
        "article_content_service": article_content_service,
        "chunk_service": chunk_service,
    }


def one_article():
    return [
        SourceArticle(
            title="t",
            url="https://site.com/1",
            summary=None,
            published_at=None,
            source="Site",
        )
    ]


def source():
    return NewsSource(name="Site", url="https://site.com", type=SourceType.SITEMAP)


async def test_skips_none_content():
    service, m = make_service()
    m["article_repository"].get_by_url.return_value = None
    m["article_content_service"].extract.return_value = None

    result = await service.ingest(source(), one_article())

    assert result.skipped == 1
    assert result.inserted == 0
    m["article_repository"].create.assert_not_awaited()


async def test_skips_too_short_content():
    service, m = make_service()
    m["article_repository"].get_by_url.return_value = None
    m["article_content_service"].extract.return_value = "cookie boilerplate"

    result = await service.ingest(source(), one_article())

    assert result.skipped == 1
    assert result.inserted == 0
    m["article_repository"].create.assert_not_awaited()


async def test_ingests_valid_content():
    service, m = make_service()
    m["article_repository"].get_by_url.return_value = None
    m["article_content_service"].extract.return_value = "x" * (
        IngestionService.MIN_CONTENT_LENGTH + 1
    )
    m["article_repository"].create.side_effect = lambda article: article
    m["chunk_service"].create_chunks.return_value = []

    result = await service.ingest(source(), one_article())

    assert result.inserted == 1
    assert result.skipped == 0
    m["article_repository"].create.assert_awaited_once()


async def test_ignores_duplicate_by_url():
    service, m = make_service()
    m["article_repository"].get_by_url.return_value = object()  # already exists

    result = await service.ingest(source(), one_article())

    assert result.ignored == 1
    assert result.inserted == 0
    m["article_content_service"].extract.assert_not_awaited()
