from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.repositories.article_repository import ArticleRepository
from app.services.article_service import ArticleService

from app.repositories.feed_repository import FeedRepository
from app.services.feed_service import FeedService


def get_article_service(
    db: Session = Depends(get_db),
) -> ArticleService:
    repository = ArticleRepository(db)
    return ArticleService(repository)

def get_feed_service(
    db: Session = Depends(get_db),
) -> FeedService:
    repository = FeedRepository(db)
    return FeedService(repository)