from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feed import Feed


class FeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, feed: Feed) -> Feed:
        self.db.add(feed)
        self.db.commit()
        self.db.refresh(feed)
        return feed

    def get_by_id(self, feed_id: int) -> Feed | None:
        statement = select(Feed).where(Feed.id == feed_id)
        return self.db.scalar(statement)

    def get_by_url(self, url: str) -> Feed | None:
        statement = select(Feed).where(Feed.url == url)
        return self.db.scalar(statement)

    def list(self) -> list[Feed]:
        statement = select(Feed)
        return list(self.db.scalars(statement).all())
    
    def get(self, feed_id: int) -> Feed | None:
        return (
            self.db.query(Feed)
            .filter(Feed.id == feed_id)
            .first()
        )
