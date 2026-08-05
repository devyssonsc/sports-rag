from fastapi import APIRouter, Depends

from app.api.dependencies import get_embedding_service
from app.schemas.embedding import (
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.services.embedding_service import EmbeddingService

router = APIRouter(
    prefix="/embeddings",
    tags=["Embeddings"],
)


@router.post(
    "",
    response_model=EmbeddingResponse,
)
def test_embedding(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):

    embedding = embedding_service.embed_document(request.text)

    return EmbeddingResponse(
        model=embedding_service.MODEL_NAME,
        dimensions=len(embedding),
        preview=embedding[:10],
    )