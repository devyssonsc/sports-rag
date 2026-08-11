import asyncio

import trafilatura

from app.services.text_cleaning_service import TextCleaningService


class ArticleContentService:

    def __init__(
        self,
        text_cleaning_service: TextCleaningService,
    ):
        self.text_cleaning_service = text_cleaning_service

    async def extract(
        self,
        url: str,
    ) -> str | None:

        text = await asyncio.to_thread(self._extract_sync, url)

        if text is None:
            return None

        return self.text_cleaning_service.clean(text)

    def _extract_sync(
        self,
        url: str,
    ) -> str | None:

        downloaded = trafilatura.fetch_url(url)

        if downloaded is None:
            return None

        return trafilatura.extract(downloaded)
