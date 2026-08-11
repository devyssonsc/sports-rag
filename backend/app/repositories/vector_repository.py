import os

from qdrant_client import AsyncQdrantClient

from qdrant_client.models import PointStruct

from qdrant_client.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse


class VectorRepository:

    COLLECTION_NAME = "article_chunks"
    VECTOR_SIZE = 1024

    def __init__(self):

        self.client = AsyncQdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
        )

        self._collection_ready = False

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
