import os

from qdrant_client import AsyncQdrantClient

from qdrant_client.models import PointStruct

from qdrant_client.models import (
    Distance,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)
from qdrant_client.http.exceptions import UnexpectedResponse


class VectorRepository:

    COLLECTION_NAME = "article_chunks"
    SPARSE_COLLECTION_NAME = "article_chunks_sparse"
    SPARSE_VECTOR_NAME = "text"
    # Dense vector dimension — must match the embedding model
    # (intfloat/multilingual-e5-large-instruct = 1024).
    VECTOR_SIZE = 1024

    def __init__(self):

        self.client = AsyncQdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
        )

        self._collection_ready = False
        self._sparse_collection_ready = False

    async def get_collections(self):
        return await self.client.get_collections()

    async def upsert_chunk_embedding(
        self,
        chunk_id: int,
        article_id: int,
        embedding: list[float],
    ) -> None:

        await self._ensure_collection_exists()

        await self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            wait=True,
            points=[
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "article_id": article_id,
                    },
                )
            ],
        )

    async def _ensure_collection_exists(self) -> None:
        if self._collection_ready:
            return

        try:
            await self.client.get_collection(self.COLLECTION_NAME)

        except UnexpectedResponse:

            await self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    async def recreate_dense_collection(self) -> None:
        """Drop and recreate the dense collection (clears all vectors).

        Used by reindexing: old points reference chunk ids that no longer exist
        after a re-chunk, so the collection is rebuilt from empty.
        """
        try:
            await self.client.delete_collection(self.COLLECTION_NAME)
        except UnexpectedResponse:
            pass

        await self.client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=self.VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        self._collection_ready = True

        self._collection_ready = True

    async def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ):

        await self._ensure_collection_exists()

        results = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=embedding,
            limit=limit,
        )

        return results.points

    # ------------------------------------------------------------------
    # Sparse (BM25) collection — used for hybrid retrieval
    # ------------------------------------------------------------------

    async def _ensure_sparse_collection_exists(self) -> None:
        if self._sparse_collection_ready:
            return

        try:
            await self.client.get_collection(self.SPARSE_COLLECTION_NAME)
        except UnexpectedResponse:
            await self.client.create_collection(
                collection_name=self.SPARSE_COLLECTION_NAME,
                vectors_config={},
                sparse_vectors_config={
                    self.SPARSE_VECTOR_NAME: SparseVectorParams(),
                },
            )

        self._sparse_collection_ready = True

    async def recreate_sparse_collection(self) -> None:
        """Drop and recreate the sparse collection (clears all points).

        Backfilling must start from empty: after a reindex the chunk ids change,
        so leftover points would reference chunks that no longer exist.
        """
        try:
            await self.client.delete_collection(self.SPARSE_COLLECTION_NAME)
        except UnexpectedResponse:
            pass

        await self.client.create_collection(
            collection_name=self.SPARSE_COLLECTION_NAME,
            vectors_config={},
            sparse_vectors_config={
                self.SPARSE_VECTOR_NAME: SparseVectorParams(),
            },
        )
        self._sparse_collection_ready = True

    async def upsert_sparse_embedding(
        self,
        chunk_id: int,
        article_id: int,
        indices: list[int],
        values: list[float],
    ) -> None:

        await self._ensure_sparse_collection_exists()

        await self.client.upsert(
            collection_name=self.SPARSE_COLLECTION_NAME,
            wait=True,
            points=[
                PointStruct(
                    id=chunk_id,
                    vector={
                        self.SPARSE_VECTOR_NAME: SparseVector(
                            indices=indices,
                            values=values,
                        )
                    },
                    payload={"article_id": article_id},
                )
            ],
        )

    async def search_sparse(
        self,
        indices: list[int],
        values: list[float],
        limit: int = 5,
    ):

        await self._ensure_sparse_collection_exists()

        results = await self.client.query_points(
            collection_name=self.SPARSE_COLLECTION_NAME,
            query=SparseVector(indices=indices, values=values),
            using=self.SPARSE_VECTOR_NAME,
            limit=limit,
        )

        return results.points
