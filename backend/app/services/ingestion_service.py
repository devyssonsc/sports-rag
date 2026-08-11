from app.repositories.article_repository import ArticleRepository
from app.dto.source_article import SourceArticle
from app.models.article import Article

from app.schemas.ingestion import IngestionResult
from app.models.news_source import NewsSource

from app.services.article_content_service import ArticleContentService
from app.services.chunk_service import ChunkService

from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import VectorRepository

class IngestionService:

    def __init__(
        self,
        article_repository: ArticleRepository,
        article_content_service: ArticleContentService,
        chunk_service: ChunkService,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
    ):
        self.article_repository = article_repository
        self.article_content_service = article_content_service
        self.chunk_service = chunk_service
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository

    async def ingest(
        self,
        news_source: NewsSource,
        articles: list[SourceArticle],
    ) -> IngestionResult:

        processed = len(articles)
        inserted = 0
        ignored = 0

        for source_article in articles:

            existing = await self.article_repository.get_by_url(
                source_article.url
            )

            if existing:
                ignored += 1
                continue

            content = await self.article_content_service.extract(
                                source_article.url
                            )

            article = Article(
                title=source_article.title,
                summary=source_article.summary,
                content = content,
                url=source_article.url,
                source=source_article.source,
                published_at=source_article.published_at,
                news_source_id=news_source.id
            )

            article = await self.article_repository.create(article)

            chunks = await self.chunk_service.create_chunks(article)

            for chunk in chunks:

                embedding = await self.embedding_service.embed_document(
                    chunk.content
                )

                await self.vector_repository.upsert_chunk_embedding(
                    chunk_id=chunk.id,
                    article_id=chunk.article_id,
                    embedding=embedding,
                )

            inserted += 1

        return IngestionResult(
            processed=processed,
            inserted=inserted,
            ignored=ignored,
        )
