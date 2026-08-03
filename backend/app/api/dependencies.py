from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.repositories.article_repository import ArticleRepository
from app.services.article_service import ArticleService

from app.repositories.feed_repository import FeedRepository
from app.services.feed_service import FeedService

from app.services.rss_service import RSSService

from app.repositories.article_repository import ArticleRepository
from app.services.ingestion_service import IngestionService
from app.services.article_content_service import ArticleContentService
from app.repositories.chunk_repository import ChunkRepository
from app.services.chunk_service import ChunkService
from app.services.chunking_service import ChunkingService

def get_article_repository(
    db: Session = Depends(get_db),
) -> ArticleRepository:

    return ArticleRepository(db)

def get_chunk_repository(
    db: Session = Depends(get_db),
):
    return ChunkRepository(db)


def get_ingestion_service(
    db: Session = Depends(get_db),
):
    article_repository = ArticleRepository(db)
    article_content_service = ArticleContentService()
    chunk_repository = ChunkRepository(db)

    chunking_service = ChunkingService()

    chunk_service = ChunkService(
        chunking_service,
        chunk_repository,
    )

    return IngestionService(
        article_repository,
        article_content_service,
        chunk_service
    )


def get_rss_service():
    return RSSService()

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