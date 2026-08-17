"""Retry helper for the evaluation harness.

The harness makes hundreds of LLM calls per run, so a single transient provider
error (503, rate limit, connection blip) should not abort the whole run. This
retries such errors with exponential backoff; non-transient errors propagate.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

import together

T = TypeVar("T")

_RETRYABLE = (
    together.InternalServerError,
    together.RateLimitError,
    together.APIConnectionError,
    together.APITimeoutError,
)


async def with_retry(
    factory: Callable[[], Awaitable[T]],
    attempts: int = 5,
    base_delay: float = 1.0,
) -> T:
    """Call ``factory()`` and await it, retrying transient provider errors."""
    delay = base_delay
    for attempt in range(attempts):
        try:
            return await factory()
        except _RETRYABLE:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2
    # Unreachable: the loop either returns or raises.
    raise RuntimeError("with_retry exhausted without returning")
