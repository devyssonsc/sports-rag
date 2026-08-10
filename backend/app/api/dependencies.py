from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.repositories.article_repository import ArticleRepository
from app.services.article_service import ArticleService

from app.repositories.feed_repository import FeedRepository
from app.services.feed_service import FeedService

from app.repositories.article_repository import ArticleRepository
from app.services.ingestion_service import IngestionService
from app.services.article_content_service import ArticleContentService
from app.repositories.chunk_repository import ChunkRepository
from app.services.chunk_service import ChunkService
from app.services.llama_index_chunking_service import LlamaIndexChunkingService
from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import VectorRepository
from app.services.text_cleaning_service import TextCleaningService
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.chat_service import ChatService
from app.services.discovery.factory import DiscoveryFactory

def get_vector_repository() -> VectorRepository:
    return VectorRepository()

def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

def get_llm_service() -> LLMService:
    return LLMService()


def get_prompt_builder() -> PromptBuilderService:
    return PromptBuilderService()


def get_discovery_factory() -> DiscoveryFactory:
    return DiscoveryFactory()

def get_article_repository(
    db: Session = Depends(get_db),
) -> ArticleRepository:

    return ArticleRepository(db)

def get_chunk_repository(
    db: Session = Depends(get_db),
):
    return ChunkRepository(db)


def get_retrieval_service(
    embedding_service: EmbeddingService = Depends(
        get_embedding_service
    ),
    vector_repository: VectorRepository = Depends(
        get_vector_repository
    ),
    chunk_repository: ChunkRepository = Depends(
        get_chunk_repository
    ),
    article_repository: ArticleRepository = Depends(
        get_article_repository
    ),
) -> RetrievalService:

    return RetrievalService(
        embedding_service,
        vector_repository,
        chunk_repository,
        article_repository,
    )


def get_chat_service(
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service
    ),
    prompt_builder: PromptBuilderService = Depends(
        get_prompt_builder
    ),
    llm_service: LLMService = Depends(
        get_llm_service
    ),
) -> ChatService:

    return ChatService(
        retrieval_service,
        prompt_builder,
        llm_service,
    )


def get_ingestion_service(
    db: Session = Depends(get_db),
):
    article_repository = ArticleRepository(db)
    text_cleaning_service = TextCleaningService()
    article_content_service = ArticleContentService(text_cleaning_service)
    chunk_repository = ChunkRepository(db)

    chunking_service = LlamaIndexChunkingService()

    chunk_service = ChunkService(
        chunking_service,
        chunk_repository,
    )

    embedding_service = EmbeddingService()

    vector_repository = VectorRepository()

    return IngestionService(
        article_repository,
        article_content_service,
        chunk_service,
        embedding_service,
        vector_repository,
    )


def get_article_service(
    db: Session = Depends(get_db),
) -> ArticleService:

    article_repository = ArticleRepository(db)
    chunk_repository = ChunkRepository(db)

    return ArticleService(
        article_repository,
        chunk_repository,
    )

def get_feed_service(
    db: Session = Depends(get_db),
) -> FeedService:
    repository = FeedRepository(db)
    return FeedService(repository)