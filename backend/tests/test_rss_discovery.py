import time
import types

from datetime import timedelta
from unittest.mock import patch

from app.models.news_source import NewsSource
from app.models.source_type import SourceType
from app.services.discovery.rss_discovery import RSSDiscovery


def fake_feed(entries):
    return types.SimpleNamespace(
        entries=entries,
        feed={"title": "ESPN"},
    )


def source():
    return NewsSource(
        name="ESPN",
        url="https://example.com/rss",
        type=SourceType.RSS,
    )


async def test_rss_normalizes_published_at_to_utc():
    # struct_time is already UTC (as feedparser returns it)
    st = time.struct_time((2026, 8, 11, 18, 54, 18, 1, 223, 0))
    feed = fake_feed(
        [
            {
                "title": "Article A",
                "link": "https://example.com/1",
                "summary": "s",
                "published_parsed": st,
            }
        ]
    )

    with patch("feedparser.parse", return_value=feed):
        articles = await RSSDiscovery().discover(source())

    a = articles[0]
    assert a.published_at is not None
    assert a.published_at.utcoffset() == timedelta(0)
    assert (a.published_at.year, a.published_at.hour) == (2026, 18)


async def test_rss_published_at_none_when_no_date():
    feed = fake_feed(
        [
            {
                "title": "Article B",
                "link": "https://example.com/2",
                "summary": None,
            }
        ]
    )

    with patch("feedparser.parse", return_value=feed):
        articles = await RSSDiscovery().discover(source())

    assert articles[0].published_at is None
