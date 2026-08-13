"""Live scores and dream-team service.

Provides real-time gameweek data with short cache TTLs.
"""

from __future__ import annotations

import logging
from typing import Any

from fpl_mcp.infrastructure.cache import CacheTier, TieredCache
from fpl_mcp.infrastructure.fpl_client import FPLClient
from fpl_mcp.repositories import PlayerRepository

logger = logging.getLogger(__name__)


class LiveService:
    """Service for live event data and dream-team lookups.

    All data is fetched through the FPL client with a short cache TTL
    suitable for rapidly changing live scores.
    """

    _LIVE_TTL = 30  # seconds
    _DREAM_TEAM_TTL = 60  # seconds

    def __init__(
        self,
        fpl_client: FPLClient,
        player_repo: PlayerRepository,
        cache: TieredCache,
    ) -> None:
        self._client = fpl_client
        self._player_repo = player_repo
        self._cache = cache

    async def get_live_event(self, event_id: int) -> dict[str, Any]:
        """Fetch live scores for a gameweek.

        Cached for 30 seconds to avoid hammering the API during active
        gameweeks.
        """
        cache_key = f"live_event:{event_id}"

        async def _fetch() -> dict[str, Any]:
            data = await self._client.get_live_event(event_id)
            return data

        return await self._cache.get_or_fetch(
            cache_key,
            _fetch,
            tier=CacheTier.PUBLIC,
            ttl=self._LIVE_TTL,
        )

    async def get_dream_team(self, event_id: int) -> dict[str, Any]:
        """Fetch the dream team for a gameweek.

        Cached for 60 seconds.
        """
        cache_key = f"dream_team:{event_id}"

        async def _fetch() -> dict[str, Any]:
            data = await self._client.get_dream_team(event_id)
            return data

        return await self._cache.get_or_fetch(
            cache_key,
            _fetch,
            tier=CacheTier.PUBLIC,
            ttl=self._DREAM_TEAM_TTL,
        )
