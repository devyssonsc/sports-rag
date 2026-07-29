from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.repositories.article_repository import ArticleRepository
from app.services.article_service import ArticleService


def get_article_service(
    db: Session = Depends(get_db),
) -> ArticleService:
    repository = ArticleRepository(db)
    return ArticleService(repository)