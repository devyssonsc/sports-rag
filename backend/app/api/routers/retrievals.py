from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_embedding_service,
    get_retrieval_service,
    get_vector_repository,
)
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
)

@router.post("/test")
async def test_retrieval(
    query: str,
    embedding_service=Depends(get_embedding_service),
    vector_repository=Depends(get_vector_repository),
):

    embedding = await embedding_service.embed_document(query)

    results = await vector_repository.search(embedding)

    for point in results:
        print(point.payload)

    return [
        {
            "id": str(point.id),
            "score": point.score,
            "payload": point.payload,
        }
        for point in results
    ]

@router.post(
    "/search",
    response_model=RetrievalResponse,
)
async def search(
    request: RetrievalRequest,
    service: RetrievalService = Depends(
        get_retrieval_service
    ),
):

    return await service.search(
        request.query,
        request.limit,
    )
