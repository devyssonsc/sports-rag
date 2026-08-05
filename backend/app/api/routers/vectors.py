from fastapi import APIRouter, Depends

from app.api.dependencies import get_vector_repository
from app.repositories.vector_repository import VectorRepository

from app.api.dependencies import get_embedding_service
from app.services.embedding_service import EmbeddingService

router = APIRouter(
    prefix="/vectors",
    tags=["Vectors"],
)


@router.get("/collections")
def list_collections(
    repository: VectorRepository = Depends(get_vector_repository),
):

    collections = repository.get_collections()

    return {
        "collections": [
            {
                "name": collection.name,
            }
            for collection in collections.collections
        ]
    }
    
@router.post("/test")
def test_vector(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    repository: VectorRepository = Depends(get_vector_repository),
):

    text = "Lionel Messi scored two goals against Brazil."

    embedding = embedding_service.embed_document(text)

    repository.upsert_chunk_embedding(
        chunk_id=1,
        article_id=1,
        embedding=embedding,
    )

    return {
        "message": "Vector stored successfully."
    }