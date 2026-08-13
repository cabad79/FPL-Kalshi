"""Tiered in-memory cache with TTL and automatic expiry cleanup.

NEVER persists PRIVATE data to disk.
"""

import asyncio
import time
from collections.abc import Callable
from enum import Enum
from typing import Any


class CacheTier(Enum):
    """Cache tier classification."""

    PUBLIC = "public"          # Memory only, long TTL, non-sensitive
    PRIVATE = "private"        # Memory only, short TTL, sensitive
    PERSISTENT = "persistent"  # Secure storage, tokens only (managed by credentials.py)


class TieredCache:
    """Three-tier cache system.

    PUBLIC and PRIVATE tiers are stored in memory as dicts with TTL.
    PERSISTENT tier is NOT handled here — tokens are managed by
    SecureCredentialManager in credentials.py.

    Thread-safe via asyncio.Lock.
    """

    # Default TTLs per tier (seconds)
    _DEFAULT_TTLS: dict[CacheTier, int] = {
        CacheTier.PUBLIC: 3600,
        CacheTier.PRIVATE: 60,
    }

    def __init__(self) -> None:
        self._public: dict[str, tuple[Any, float]] = {}
        self._private: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self._stats: dict[str, Any] = {
            "hits_public": 0,
            "misses_public": 0,
            "hits_private": 0,
            "misses_private": 0,
            "evictions_public": 0,
            "evictions_private": 0,
        }

    def _store_for(self, tier: CacheTier) -> dict[str, tuple[Any, float]]:
        if tier == CacheTier.PUBLIC:
            return self._public
        if tier == CacheTier.PRIVATE:
            return self._private
        raise ValueError(f"TieredCache does not manage tier {tier.value!r}")

    def _cleanup_expired(self, store: dict[str, tuple[Any, float]]) -> int:
        """Remove expired entries. Returns count removed."""
        now = time.monotonic()
        expired = [k for k, (_, expires_at) in store.items() if expires_at <= now]
        for k in expired:
            del store[k]
        return len(expired)

    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        tier: CacheTier,
        ttl: int | None = None,
    ) -> Any:
        """Get value from cache or fetch and store it.

        Args:
            key: Cache key.
            fetch_func: Callable to produce the value on cache miss.
            tier: Cache tier (PUBLIC or PRIVATE).
            ttl: Time-to-live in seconds. Uses tier default if None.

        Returns:
            Cached or freshly fetched value.
        """
        if tier == CacheTier.PERSISTENT:
            raise ValueError(
                "PERSISTENT tier is not managed by TieredCache. "
                "Use SecureCredentialManager for tokens."
            )

        resolved_ttl = ttl if ttl is not None else self._DEFAULT_TTLS[tier]
        store = self._store_for(tier)

        async with self._lock:
            # Clean up expired entries opportunistically
            evicted = self._cleanup_expired(store)
            if tier == CacheTier.PUBLIC:
                self._stats["evictions_public"] += evicted
            else:
                self._stats["evictions_private"] += evicted

            if key in store:
                value, expires_at = store[key]
                if expires_at > time.monotonic():
                    if tier == CacheTier.PUBLIC:
                        self._stats["hits_public"] += 1
                    else:
                        self._stats["hits_private"] += 1
                    return value
                # Expired — remove
                del store[key]

            if tier == CacheTier.PUBLIC:
                self._stats["misses_public"] += 1
            else:
                self._stats["misses_private"] += 1

        # Fetch outside the lock to avoid blocking other cache ops
        value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()

        async with self._lock:
            expires_at = time.monotonic() + resolved_ttl
            store[key] = (value, expires_at)

        return value

    def invalidate(
        self,
        key: str | None = None,
        tier: CacheTier | None = None,
    ) -> None:
        """Invalidate cache entries.

        Args:
            key: Specific key to invalidate, or None to invalidate all
                keys in the specified tier(s).
            tier: Specific tier to invalidate, or None to invalidate both
                PUBLIC and PRIVATE.
        """
        tiers = [tier] if tier else [CacheTier.PUBLIC, CacheTier.PRIVATE]
        for t in tiers:
            if t == CacheTier.PERSISTENT:
                continue
            store = self._store_for(t)
            if key is None:
                store.clear()
            elif key in store:
                del store[key]

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        stats = dict(self._stats)
        stats["size_public"] = len(self._public)
        stats["size_private"] = len(self._private)
        return stats
