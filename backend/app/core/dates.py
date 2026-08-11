import time

from datetime import datetime, timezone


def ensure_utc(value: datetime | None) -> datetime | None:
    """Return a timezone-aware datetime in UTC.

    A naive datetime is assumed to already be in UTC; an aware datetime is
    converted to UTC. ``None`` passes through unchanged.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def from_struct_time(value: time.struct_time | None) -> datetime | None:
    """Convert a feedparser ``struct_time`` (already UTC) to an aware UTC datetime."""
    if value is None:
        return None

    return datetime(*value[:6], tzinfo=timezone.utc)
