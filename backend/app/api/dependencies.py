from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db

from app.repositories.article_repository import ArticleRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.repositories.vector_repository import VectorRepository

from app.services.article_content_service import ArticleContentService
from app.services.article_service import ArticleService
from app.services.chat_service import ChatService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.ingestion_service import IngestionService
from app.services.llama_index_chunking_service import LlamaIndexChunkingService
from app.services.llm_service import LLMService
from app.services.news_source_service import NewsSourceService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.rerank_service import RerankService
from app.services.retrieval_service import RetrievalService
from app.services.text_cleaning_service import TextCleaningService
from app.services.discovery.factory import DiscoveryFactory

def get_discovery_factory() -> DiscoveryFactory:
    return DiscoveryFactory()

# ------------------------------------------------------------------
# Repositories
# ------------------------------------------------------------------

def get_article_repository(
    db: AsyncSession = Depends(get_db),
) -> ArticleRepository:
    return ArticleRepository(db)


def get_chunk_repository(
    db: AsyncSession = Depends(get_db),
) -> ChunkRepository:
    return ChunkRepository(db)


def get_news_source_repository(
    db: AsyncSession = Depends(get_db),
) -> NewsSourceRepository:
    return NewsSourceRepository(db)


def get_vector_repository() -> VectorRepository:
    return VectorRepository()


# ------------------------------------------------------------------
# Basic Services
# ------------------------------------------------------------------

def get_text_cleaning_service() -> TextCleaningService:
    return TextCleaningService()


def get_article_content_service(
    text_cleaning_service: TextCleaningService = Depends(
        get_text_cleaning_service
    ),
) -> ArticleContentService:

    return ArticleContentService(
        text_cleaning_service
    )


def get_chunking_service() -> LlamaIndexChunkingService:
    return LlamaIndexChunkingService()


def get_chunk_service(
    chunking_service: LlamaIndexChunkingService = Depends(
        get_chunking_service
    ),
    chunk_repository: ChunkRepository = Depends(
        get_chunk_repository
    ),
) -> ChunkService:

    return ChunkService(
        chunking_service,
        chunk_repository,
    )


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_llm_service() -> LLMService:
    return LLMService()


def get_prompt_builder() -> PromptBuilderService:
    return PromptBuilderService()


@lru_cache
def get_rerank_service() -> RerankService:
    # Cached as a singleton: the cross-encoder model is loaded once and reused
    # across requests, not rebuilt per request.
    return RerankService()


# ------------------------------------------------------------------
# Domain Services
# ------------------------------------------------------------------

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
    rerank_service: RerankService = Depends(
        get_rerank_service
    ),
) -> RetrievalService:

    return RetrievalService(
        embedding_service,
        vector_repository,
        chunk_repository,
        article_repository,
        rerank_service=rerank_service,
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
    article_repository: ArticleRepository = Depends(
        get_article_repository
    ),
    article_content_service: ArticleContentService = Depends(
        get_article_content_service
    ),
    chunk_service: ChunkService = Depends(
        get_chunk_service
    ),
    embedding_service: EmbeddingService = Depends(
        get_embedding_service
    ),
    vector_repository: VectorRepository = Depends(
        get_vector_repository
    ),
) -> IngestionService:

    return IngestionService(
        article_repository,
        article_content_service,
        chunk_service,
        embedding_service,
        vector_repository,
    )


def get_article_service(
    article_repository: ArticleRepository = Depends(
        get_article_repository
    ),
    chunk_repository: ChunkRepository = Depends(
        get_chunk_repository
    ),
) -> ArticleService:

    return ArticleService(
        article_repository,
        chunk_repository,
    )


def get_news_source_service(
    repository: NewsSourceRepository = Depends(
        get_news_source_repository
    ),
) -> NewsSourceService:

    return NewsSourceService(repository)
