"""Rate limiter with sliding window and exponential backoff for 429s.

NOT a singleton — inject one instance into FPLClient.
"""

import asyncio
import time
from typing import Any


class RateLimiter:
    """Sliding-window rate limiter with configurable limits.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        per_seconds: Time window in seconds.
        backoff_base: Base seconds for exponential backoff on 429 responses.
        backoff_max: Maximum backoff seconds.
    """

    def __init__(
        self,
        max_requests: int = 20,
        per_seconds: int = 60,
        backoff_base: float = 1.0,
        backoff_max: float = 60.0,
    ) -> None:
        self._max_requests = max_requests
        self._time_window = float(per_seconds)
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max
        self._request_times: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire a slot in the rate limit window.

        Blocks asynchronously until a slot is available.

        Returns:
            True when the slot is acquired.
        """
        while True:
            async with self._lock:
                now = time.monotonic()
                cutoff = now - self._time_window
                # Remove timestamps outside the window
                self._request_times = [t for t in self._request_times if t > cutoff]
                if len(self._request_times) < self._max_requests:
                    self._request_times.append(now)
                    return True
                # Compute wait time until the oldest request exits the window
                wait_time = self._time_window - (now - self._request_times[0])
                wait_time = max(0.01, wait_time)
            await asyncio.sleep(wait_time)

    async def acquire_with_backoff(self, attempt: int = 0) -> None:
        """Acquire a slot, optionally backing off for retries.

        Args:
            attempt: Current retry attempt (0-based). Used to compute
                exponential backoff before calling acquire().
        """
        if attempt > 0:
            delay = min(self._backoff_base * (2 ** (attempt - 1)), self._backoff_max)
            await asyncio.sleep(delay)
        await self.acquire()

    @property
    def stats(self) -> dict[str, Any]:
        """Return current rate limiter statistics."""
        now = time.monotonic()
        cutoff = now - self._time_window
        active = len([t for t in self._request_times if t > cutoff])
        return {
            "max_requests": self._max_requests,
            "time_window_seconds": self._time_window,
            "active_requests": active,
            "remaining": max(0, self._max_requests - active),
        }
