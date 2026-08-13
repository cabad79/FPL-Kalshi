"""Concurrency utilities for controlled async execution."""

import asyncio
from collections.abc import Awaitable, Iterable
from typing import Any


async def gather_limited(
    coros: Iterable[Awaitable[Any]],
    limit: int = 5,
    return_exceptions: bool = False,
) -> list[Any]:
    """Run awaitables with a concurrency limit.

    Args:
        coros: Iterable of awaitables to execute.
        limit: Maximum number of concurrent tasks.
        return_exceptions: If True, exceptions are returned in the result list
            instead of being raised.

    Returns:
        List of results in the same order as the input awaitables.
    """
    semaphore = asyncio.Semaphore(limit)

    async def _run(coro: Awaitable[Any]) -> Any:
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *(_run(c) for c in coros),
        return_exceptions=return_exceptions,
    )
