from app.models.article import Article
from app.repositories.article_repository import ArticleRepository
from app.schemas.article import ArticleCreate
import logging

from app.core.exceptions import (
    ArticleAlreadyExists,
    ArticleNotFound,
)

logger = logging.getLogger(__name__)

class ArticleService:
    def __init__(self, repository: ArticleRepository):
        self.repository = repository

    def create_article(self, article_data: ArticleCreate) -> Article:
        existing_article = self.repository.get_by_url(article_data.url)

        if existing_article:
            raise ArticleAlreadyExists(
                f"Article with URL '{article_data.url}' already exists."
            )

        article = Article(
            title=article_data.title,
            url=article_data.url,
            source=article_data.source,
            published_at=article_data.published_at,
        )
        
        logger.info("Creating Article")

        return self.repository.create(article)

    def list_articles(self) -> list[Article]:
        return self.repository.list()

    def get_article(self, article_id: int) -> Article | None:
        return self.repository.get_by_id(article_id)

    def delete_article(self, article_id: int) -> None:
        article = self.repository.get_by_id(article_id)

        raise ArticleNotFound(
            f"Article {article_id} not found."
        )

        self.repository.delete(article)