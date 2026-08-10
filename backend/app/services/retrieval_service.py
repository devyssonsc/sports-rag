from app.repositories.chunk_repository import ChunkRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding_service import EmbeddingService

from app.schemas.retrieval import (
    RetrievalResponse,
    RetrievedChunk,
)
from app.repositories.article_repository import ArticleRepository


class RetrievalService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        chunk_repository: ChunkRepository,
        article_repository: ArticleRepository
    ):
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.chunk_repository = chunk_repository
        self.article_repository = article_repository

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> RetrievalResponse:

        results = self.retrieve_context(
            query,
            limit,
        )

        return RetrievalResponse(
            query=query,
            results=results,
        )
        
    def retrieve_context(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedChunk]:

        embedding = self.embedding_service.embed_document(query)

        points = self.vector_repository.search(
            embedding,
            limit,
        )

        chunk_ids = [
            int(point.id)
            for point in points
        ]

        chunks = self.chunk_repository.get_by_ids(
            chunk_ids
        )

        chunk_map = {
            chunk.id: chunk
            for chunk in chunks
        }

        article_ids = list(
            {
                chunk.article_id
                for chunk in chunks
            }
        )

        articles = self.article_repository.get_by_ids(
            article_ids
        )

        article_map = {
            article.id: article
            for article in articles
        }

        results = []

        for point in points:

            chunk = chunk_map[int(point.id)]

            article = article_map[
                chunk.article_id
            ]

            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    article_id=chunk.article_id,
                    article_title=article.title,
                    source=article.source,
                    published_at=article.published_at,
                    chunk_index=chunk.chunk_index,
                    score=point.score,
                    content=chunk.content,
                )
            )

        return results