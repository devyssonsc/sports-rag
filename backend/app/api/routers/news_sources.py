import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_discovery_factory,
    get_ingestion_service,
    get_news_source_service,
)
from app.schemas.ingestion import IngestionResult
from app.schemas.news_source import (
    NewsSourceCreate,
    NewsSourceResponse,
)
from app.services.discovery.factory import DiscoveryFactory
from app.services.ingestion_service import IngestionService
from app.services.news_source_service import NewsSourceService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/news-sources",
    tags=["News Sources"],
)


@router.post("", response_model=NewsSourceResponse)
async def create_news_source(
    news_source: NewsSourceCreate,
    service: NewsSourceService = Depends(get_news_source_service),
):
    logger.info(news_source)
    return await service.create_news_source(news_source)


@router.get("", response_model=list[NewsSourceResponse])
async def list_news_sources(
    service: NewsSourceService = Depends(get_news_source_service),
):
    return await service.list_news_sources()


@router.post("/{news_source_id}/fetch", response_model=IngestionResult)
async def fetch_news_source(
    news_source_id: int,
    news_source_service: NewsSourceService = Depends(
        get_news_source_service
    ),
    discovery_factory: DiscoveryFactory = Depends(get_discovery_factory),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    news_source = await news_source_service.get(news_source_id)

    strategy = discovery_factory.get(news_source)

    articles = await strategy.discover(news_source)

    return await ingestion_service.ingest(news_source, articles)
