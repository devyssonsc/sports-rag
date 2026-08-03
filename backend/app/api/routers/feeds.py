from fastapi import APIRouter, Depends

from app.schemas.feed import FeedCreate, FeedResponse
from app.services.feed_service import FeedService
from app.api.dependencies import get_feed_service, get_ingestion_service, get_rss_service
import logging

from app.services.rss_service import RSSService

from app.schemas.ingestion import IngestionResult
from app.services.ingestion_service import IngestionService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feeds", tags=["Feeds"])

from app.services.article_content_service import ArticleContentService
from app.services.chunking_service import ChunkingService

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

@router.post("/{feed_id}/fetch", response_model=IngestionResult)
def fetch_feed(
    feed_id: int,
    feed_service: FeedService = Depends(get_feed_service),
    rss_service: RSSService = Depends(get_rss_service),
    ingestion_service: IngestionService = Depends(get_ingestion_service)
):

    feed = feed_service.get(feed_id)

    articles = rss_service.parse(feed.url)
    
    return ingestion_service.ingest(feed, articles)