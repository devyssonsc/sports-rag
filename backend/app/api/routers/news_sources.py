import logging

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.dependencies import get_news_source_service
from app.schemas.news_source import (
    NewsSourceCreate,
    NewsSourceResponse,
)
from app.services.ingestion_runner import run_ingestion
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


@router.post("/{news_source_id}/fetch", status_code=202)
async def fetch_news_source(
    news_source_id: int,
    background_tasks: BackgroundTasks,
    news_source_service: NewsSourceService = Depends(
        get_news_source_service
    ),
):
    # Fail fast if the source does not exist (raises NewsSourceNotFound -> 404)
    # before scheduling the background job.
    await news_source_service.get(news_source_id)

    background_tasks.add_task(run_ingestion, news_source_id)

    return {
        "detail": "Ingestion started",
        "news_source_id": news_source_id,
    }
