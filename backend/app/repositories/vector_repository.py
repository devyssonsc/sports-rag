import os

from qdrant_client import QdrantClient

from qdrant_client.models import PointStruct

from qdrant_client.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse


class VectorRepository:

    COLLECTION_NAME = "article_chunks"
    VECTOR_SIZE = 1024

    def __init__(self):

        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
        )
        
        self._ensure_collection_exists()

    def get_collections(self):
        return self.client.get_collections()
    
    def upsert_chunk_embedding(
        self,
        chunk_id: int,
        article_id: int,
        embedding: list[float],
    ) -> None:

        self.client.upsert(
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
        
    def _ensure_collection_exists(self) -> None:
        try:
            self.client.get_collection(self.COLLECTION_NAME)

        except UnexpectedResponse:

            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            
    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ):

        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=embedding,
            limit=limit,
        )

        return results.points