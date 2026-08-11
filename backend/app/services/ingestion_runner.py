import logging

from datetime import datetime, timezone

from app.database.postgres import SessionLocal

from app.repositories.article_repository import ArticleRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.repositories.vector_repository import VectorRepository

from app.services.article_content_service import ArticleContentService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.ingestion_service import IngestionService
from app.services.llama_index_chunking_service import LlamaIndexChunkingService
from app.services.news_source_service import NewsSourceService
from app.services.text_cleaning_service import TextCleaningService

from app.services.discovery.factory import DiscoveryFactory


logger = logging.getLogger(__name__)


async def run_ingestion(news_source_id: int) -> None:
    """Discover and ingest a news source in the background.

    Runs outside the HTTP request, so it opens its own database session
    (the request-scoped session is already closed by the time this runs).
    Failures are logged, not raised, since there is no client waiting.
    """
    async with SessionLocal() as db:

        news_source_service = NewsSourceService(NewsSourceRepository(db))

        try:
            news_source = await news_source_service.get(news_source_id)
        except Exception:
            logger.exception(
                "Ingestion aborted: news source %s could not be loaded",
                news_source_id,
            )
            return

        ingestion_service = IngestionService(
            ArticleRepository(db),
            ArticleContentService(TextCleaningService()),
            ChunkService(LlamaIndexChunkingService(), ChunkRepository(db)),
            EmbeddingService(),
            VectorRepository(),
        )

        try:
            strategy = DiscoveryFactory().get(news_source)
            articles = await strategy.discover(news_source)
            result = await ingestion_service.ingest(news_source, articles)
        except Exception:
            logger.exception(
                "Ingestion failed for news source %s", news_source_id
            )
            return

        # Naive UTC to match the (timezone-naive) last_fetched_at column.
        news_source.last_fetched_at = datetime.now(timezone.utc).replace(
            tzinfo=None
        )
        await db.commit()

        logger.info(
            "Ingestion finished for source %s: "
            "processed=%s inserted=%s ignored=%s skipped=%s",
            news_source_id,
            result.processed,
            result.inserted,
            result.ignored,
            result.skipped,
        )
