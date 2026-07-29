from fastapi import APIRouter, Depends

from app.schemas.article import ArticleCreate, ArticleResponse
from app.services.article_service import ArticleService
from app.api.dependencies import get_article_service

router = APIRouter(prefix="/articles", tags=["Articles"])

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