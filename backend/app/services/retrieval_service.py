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
        sparse_embedding_service=None,
    ):
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.chunk_repository = chunk_repository
        self.article_repository = article_repository
        # Optional cross-encoder reranker. When absent (production default),
        # retrieval behaves exactly as before.
        self.rerank_service = rerank_service
        # Optional BM25 sparse embedder. Its presence turns retrieval hybrid
        # (dense + sparse fused with RRF).
        self.sparse_embedding_service = sparse_embedding_service

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
        window: int = 0,
    ) -> list[RetrievedChunk]:

        # Reranking is enabled simply by the presence of a rerank_service, so the
        # production path (which wires one in) reranks automatically, while the
        # eval harness toggles it by constructing the service or not.
        use_rerank = self.rerank_service is not None

        # When reranking, pull a larger candidate pool from the vector search
        # (recall), then let the cross-encoder pick the best ``limit`` (precision).
        search_limit = max(candidate_pool, limit) if use_rerank else limit

        embedding = await self.embedding_service.embed_query(query)

        if self.sparse_embedding_service is not None:
            # Hybrid: run dense and sparse searches, fuse their rankings (RRF).
            dense_points = await self.vector_repository.search(
                embedding,
                search_limit,
            )
            sparse_indices, sparse_values = (
                await self.sparse_embedding_service.embed_query(query)
            )
            sparse_points = await self.vector_repository.search_sparse(
                sparse_indices,
                sparse_values,
                search_limit,
            )
            ranked = _reciprocal_rank_fusion(
                dense_points,
                sparse_points,
                search_limit,
            )
        else:
            dense_points = await self.vector_repository.search(
                embedding,
                search_limit,
            )
            ranked = [(int(point.id), point.score) for point in dense_points]

        chunk_ids = [chunk_id for chunk_id, _ in ranked]

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

        for chunk_id, score in ranked:

            # A ranked id may be missing if an index is stale (e.g. the sparse
            # collection references chunks removed by a reindex). Skip it rather
            # than fail the whole query.
            chunk = chunk_map.get(chunk_id)
            if chunk is None:
                continue

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
                    score=score,
                    content=chunk.content,
                )
            )

        if use_rerank:
            results = await self.rerank_service.rerank(
                query,
                results,
                top_n=limit,
            )

        # Sentence-window: retrieval stays precise (small chunks), but each final
        # chunk is widened with its neighbours from the same article so the LLM
        # gets surrounding context. Applied after reranking, on the final chunks.
        if window > 0:
            results = await self._expand_windows(results, window)

        return results

    async def _expand_windows(
        self,
        results: list[RetrievedChunk],
        window: int,
    ) -> list[RetrievedChunk]:

        # One fetch per distinct article, mapping chunk_index -> content.
        by_article: dict[int, dict[int, str]] = {}
        for article_id in {result.article_id for result in results}:
            article_chunks = await self.chunk_repository.get_by_article_id(
                article_id
            )
            by_article[article_id] = {
                chunk.chunk_index: chunk.content
                for chunk in article_chunks
            }

        expanded = []
        for result in results:
            index_map = by_article[result.article_id]
            neighbours = [
                index_map[i]
                for i in range(
                    result.chunk_index - window,
                    result.chunk_index + window + 1,
                )
                if i in index_map
            ]
            expanded.append(
                result.model_copy(
                    update={"content": "\n".join(neighbours)}
                )
            )

        return expanded


def _reciprocal_rank_fusion(
    dense_points,
    sparse_points,
    limit: int,
    k: int = 60,
) -> list[tuple[int, float]]:
    """Fuse two ranked result lists with Reciprocal Rank Fusion.

    Each list contributes 1/(k + rank) per chunk; scores are summed across lists,
    so a chunk ranked well by either dense or sparse retrieval rises. Returns the
    top ``limit`` as (chunk_id, fused_score).
    """
    scores: dict[int, float] = {}

    for points in (dense_points, sparse_points):
        for rank, point in enumerate(points):
            chunk_id = int(point.id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return ranked[:limit]
