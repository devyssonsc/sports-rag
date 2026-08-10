from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.chat_service import ChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    service: ChatService = Depends(
        get_chat_service
    ),
):

    return service.chat(
        request.question
    )