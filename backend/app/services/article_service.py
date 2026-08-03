from app.models.article import Article
from app.repositories.article_repository import ArticleRepository
from app.schemas.article import ArticleCreate

from app.repositories.chunk_repository import ChunkRepository
from app.schemas.article_chunks import ArticleChunksResponse
from app.schemas.chunk import ChunkResponse

import logging

from app.core.exceptions import (
    ArticleAlreadyExists,
    ArticleNotFound,
)

logger = logging.getLogger(__name__)

class ArticleService:

    def __init__(
        self,
        article_repository: ArticleRepository,
        chunk_repository: ChunkRepository,
    ):
        self.article_repository = article_repository
        self.chunk_repository = chunk_repository
        
    def get_chunks(
        self,
        article_id: int,
    ) -> ArticleChunksResponse:

        article = self.article_repository.get_by_id(article_id)

        if article is None:
            raise ValueError("Article not found")

        chunks = self.chunk_repository.get_by_article_id(article_id)

        return ArticleChunksResponse(
            article_id=article.id,
            title=article.title,
            chunk_count=len(chunks),
            chunks=[
                ChunkResponse(
                    id=chunk.id,
                    index=chunk.chunk_index,
                    length=len(chunk.content),
                    content=chunk.content,
                )
                for chunk in chunks
            ],
        )

    def create_article(self, article_data: ArticleCreate) -> Article:
        existing_article = self.article_repository.get_by_url(article_data.url)

        if existing_article:
            raise ArticleAlreadyExists(
                f"Article with URL '{article_data.url}' already exists."
            )

        article = Article(
            title=article_data.title,
            url=article_data.url,
            source=article_data.source,
            published_at=article_data.published_at,
        )
        
        logger.info("Creating Article")

        return self.article_repository.create(article)

    def list_articles(self) -> list[Article]:
        return self.article_repository.list()

    def get_article(self, article_id: int) -> Article | None:
        return self.article_repository.get_by_id(article_id)

    def delete_article(self, article_id: int) -> None:
        article = self.article_repository.get_by_id(article_id)

        raise ArticleNotFound(
            f"Article {article_id} not found."
        )

        self.article_repository.delete(article)