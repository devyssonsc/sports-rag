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
        article_repository: ArticleRepository,
        rerank_service=None,
    ):
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.chunk_repository = chunk_repository
        self.article_repository = article_repository
        # Optional cross-encoder reranker. When absent (production default),
        # retrieval behaves exactly as before.
        self.rerank_service = rerank_service

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> RetrievalResponse:

        results = await self.retrieve_context(
            query,
            limit,
        )

        return RetrievalResponse(
            query=query,
            results=results,
        )

    async def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        candidate_pool: int = 20,
    ) -> list[RetrievedChunk]:

        # Reranking is enabled simply by the presence of a rerank_service, so the
        # production path (which wires one in) reranks automatically, while the
        # eval harness toggles it by constructing the service or not.
        use_rerank = self.rerank_service is not None

        # When reranking, pull a larger candidate pool from the vector search
        # (recall), then let the cross-encoder pick the best ``limit`` (precision).
        search_limit = max(candidate_pool, limit) if use_rerank else limit

        embedding = await self.embedding_service.embed_query(query)

        points = await self.vector_repository.search(
            embedding,
            search_limit,
        )

        chunk_ids = [
            int(point.id)
            for point in points
        ]

        chunks = await self.chunk_repository.get_by_ids(
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

        articles = await self.article_repository.get_by_ids(
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

        if use_rerank:
            results = await self.rerank_service.rerank(
                query,
                results,
                top_n=limit,
            )

        return results
