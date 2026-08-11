import time

from datetime import datetime, timedelta, timezone

from app.core.dates import ensure_utc, from_struct_time


def test_ensure_utc_assumes_naive_is_utc():
    result = ensure_utc(datetime(2026, 8, 11, 12, 0, 0))

    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(0)
    assert result.hour == 12


def test_ensure_utc_converts_offset_to_utc():
    aware = datetime(
        2026, 8, 11, 12, 0, 0, tzinfo=timezone(timedelta(hours=1))
    )

    result = ensure_utc(aware)

    assert result.utcoffset() == timedelta(0)
    assert result.hour == 11  # 12:00+01:00 -> 11:00 UTC


def test_ensure_utc_none():
    assert ensure_utc(None) is None


def test_from_struct_time():
    st = time.struct_time((2026, 8, 11, 18, 54, 18, 1, 223, 0))

    assert from_struct_time(st) == datetime(
        2026, 8, 11, 18, 54, 18, tzinfo=timezone.utc
    )


def test_from_struct_time_none():
    assert from_struct_time(None) is None
