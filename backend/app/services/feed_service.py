from app.models.feed import Feed
from app.repositories.feed_repository import FeedRepository
from app.schemas.feed import FeedCreate
import logging

from app.core.exceptions import FeedAlreadyExists, FeedNotFound

logger = logging.getLogger(__name__)


class FeedService:
    def __init__(self, repository: FeedRepository):
        self.repository = repository

    def create_feed(self, feed_data: FeedCreate) -> Feed:
        existing_feed = self.repository.get_by_url(feed_data.url)

        if existing_feed:
            raise FeedAlreadyExists(
                f"Feed with URL '{feed_data.url}' already exists."
            )

        feed = Feed(
            name=feed_data.name,
            url=feed_data.url,
        )

        logger.info("Creating feed: %s", feed.url)

        return self.repository.create(feed)

    def list_feeds(self) -> list[Feed]:
        return self.repository.list()
    
    def get(self, feed_id: int) -> Feed:

        feed = self.repository.get(feed_id)

        if not feed:
            raise FeedNotFound()

        return feed