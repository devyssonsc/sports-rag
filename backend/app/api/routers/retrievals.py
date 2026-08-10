from fastapi import APIRouter, Depends

from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.retrieval_service import RetrievalService
from app.api.dependencies import get_retrieval_service

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
)

@router.post(
    "/search",
    response_model=RetrievalResponse,
)
def search(
    request: RetrievalRequest,
    service: RetrievalService = Depends(
        get_retrieval_service
    ),
):

    return service.search(
        request.query,
        request.limit,
    )