from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.api.routers.news_sources as router_module

from app.api.dependencies import get_news_source_service
from app.main import app


def test_fetch_returns_202_and_schedules_background(monkeypatch):
    scheduled = []

    async def fake_run(news_source_id):
        scheduled.append(news_source_id)

    monkeypatch.setattr(router_module, "run_ingestion", fake_run)

    service = AsyncMock()
    service.get.return_value = object()  # source exists
    app.dependency_overrides[get_news_source_service] = lambda: service

    try:
        client = TestClient(app)
        response = client.post("/news-sources/7/fetch")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["news_source_id"] == 7
    # ingestion was scheduled to run in the background, not inline
    assert scheduled == [7]
