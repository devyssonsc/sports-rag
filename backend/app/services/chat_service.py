from app.services.llm_service import LLMService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retrieval_service import RetrievalService

from app.schemas.chat import (
    ChatResponse,
    SourceResponse,
)


class ChatService:

    def __init__(
        self,
        retrieval_service: RetrievalService,
        prompt_builder: PromptBuilderService,
        llm_service: LLMService,
    ):

        self.retrieval_service = retrieval_service
        self.prompt_builder = prompt_builder
        self.llm_service = llm_service

    async def chat(
        self,
        question: str,
    ) -> ChatResponse:

        chunks = await self.retrieval_service.retrieve_context(
            question
        )

        prompt = self.prompt_builder.build(
            question,
            chunks,
        )

        answer = await self.llm_service.generate(
            prompt
        )

        sources = []

        seen = set()

        for chunk in chunks:

            if chunk.article_id in seen:
                continue

            seen.add(chunk.article_id)

            sources.append(
                SourceResponse(
                    article_id=chunk.article_id,
                    article_title=chunk.article_title,
                    source=chunk.source,
                )
            )

        return ChatResponse(
            answer=answer,
            sources=sources,
        )
