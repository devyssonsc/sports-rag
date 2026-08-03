from fastapi import APIRouter, Depends

from app.schemas.feed import FeedCreate, FeedResponse
from app.services.feed_service import FeedService
from app.api.dependencies import get_feed_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feeds", tags=["Feeds"])

@router.post("", response_model=FeedResponse)
def create_feed(
    feed: FeedCreate,
    service: FeedService = Depends(get_feed_service)
):
    logger.info(feed)
    return service.create_feed(feed)

@router.get("", response_model=list[FeedResponse])
def list_feeds(
    service: FeedService = Depends(get_feed_service)
):
    return service.list_feeds()
