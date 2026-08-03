from fastapi import APIRouter, Depends

from app.schemas.article import ArticleCreate, ArticleResponse
from app.services.article_service import ArticleService
from app.api.dependencies import get_article_service, get_article_repository, get_chunk_repository

from fastapi import APIRouter, Depends, HTTPException
from app.repositories.article_repository import ArticleRepository
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.article_chunks import ArticleChunksResponse
from app.schemas.article_chunks import ChunkResponse

router = APIRouter(prefix="/articles", tags=["Articles"])

@router.get(
    "/{article_id}/chunks",
    response_model=ArticleChunksResponse,
)
def get_article_chunks(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service),
):
    return article_service.get_chunks(article_id)

@router.post("", response_model=ArticleResponse)
def create_article(
    article: ArticleCreate,
    service: ArticleService = Depends(get_article_service)
):
    return service.create_article(article)

@router.get("", response_model=list[ArticleResponse])
def list_articles(
    service: ArticleService = Depends(get_article_service)
):
    return service.list_articles()

def get_article_chunks(
    article_id: int,
    article_repository: ArticleRepository = Depends(get_article_repository),
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
):

    article = article_repository.get_by_id(article_id)

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    chunks = chunk_repository.get_by_article_id(article_id)

    return ArticleChunksResponse(
        article_id=article.id,
        title=article.title,
        chunk_count=len(chunks),
        chunks=[
            ChunkResponse(
                index=chunk.chunk_index,
                length=len(chunk.content),
                content=chunk.content,
            )
            for chunk in chunks
        ],
    )
