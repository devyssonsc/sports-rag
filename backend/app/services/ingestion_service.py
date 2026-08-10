from app.repositories.article_repository import ArticleRepository
from app.dto.source_article import SourceArticle
from app.models.article import Article

from app.schemas.ingestion import IngestionResult
from app.models.feed import Feed

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

    def ingest(
        self,
        feed: Feed,
        articles: list[SourceArticle],
    ) -> IngestionResult:
        
        processed = len(articles)
        inserted = 0
        ignored = 0

        for rss_article in articles:

            existing = self.article_repository.get_by_url(rss_article.url)

            if existing:
                ignored += 1
                continue
            
            content = self.article_content_service.extract(
                                rss_article.url
                            )

            article = Article(
                title=rss_article.title,
                summary=rss_article.summary,
                content = content,
                url=rss_article.url,
                source=rss_article.source,
                published_at=rss_article.published_at,
                feed_id=feed.id
            )

            article = self.article_repository.create(article)

            chunks = self.chunk_service.create_chunks(article)

            for chunk in chunks:

                embedding = self.embedding_service.embed_document(
                    chunk.content
                )

                self.vector_repository.upsert_chunk_embedding(
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