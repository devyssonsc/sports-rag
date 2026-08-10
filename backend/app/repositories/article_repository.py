from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, article: Article) -> Article:
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def get_by_id(self, article_id: int) -> Article | None:
        statement = select(Article).where(Article.id == article_id)
        return self.db.scalar(statement)

    def get_by_url(self, url: str) -> Article | None:
        statement = select(Article).where(Article.url == url)
        return self.db.scalar(statement)

    def list(self) -> list[Article]:
        statement = select(Article)
        return list(self.db.scalars(statement).all())
    
    def get_by_ids(
        self,
        article_ids: list[int],
    ) -> list[Article]:

        return (
            self.db.query(Article)
            .filter(Article.id.in_(article_ids))
            .all()
        )

    def delete(self, article: Article) -> None:
        self.db.delete(article)
        self.db.commit()