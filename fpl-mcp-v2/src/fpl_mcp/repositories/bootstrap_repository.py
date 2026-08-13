"""Bootstrap data repository with Pydantic validation and caching.

Provides typed access to bootstrap-static data with PUBLIC tier caching.
"""

from fpl_mcp.domain.bootstrap import BootstrapStatic, ElementType, GameSettings
from fpl_mcp.domain.gameweek import Gameweek
from fpl_mcp.domain.team import Team
from fpl_mcp.infrastructure.cache import CacheTier, TieredCache
from fpl_mcp.infrastructure.fpl_client import FPLClient
from fpl_mcp.utils.gameweek import get_current_gameweek_id, get_next_gameweek_id


class BootstrapRepository:
    """Repository for bootstrap-static data.

    Caches the full bootstrap response in CacheTier.PUBLIC with a 3600s TTL.
    All derived data (teams, gameweeks, element types) is served from the
    cached bootstrap without additional API calls.
    """

    _BOOTSTRAP_KEY = "bootstrap_static"
    _BOOTSTRAP_TTL = 3600

    def __init__(self, client: FPLClient, cache: TieredCache) -> None:
        self._client = client
        self._cache = cache

    async def _fetch_bootstrap(self) -> dict:
        """Raw fetch — used by cache on miss."""
        return await self._client.get_bootstrap_static()

    async def get_bootstrap(self) -> BootstrapStatic:
        """Get and validate bootstrap-static data.

        Returns:
            BootstrapStatic Pydantic model.
        """
        data = await self._cache.get_or_fetch(
            self._BOOTSTRAP_KEY,
            self._fetch_bootstrap,
            tier=CacheTier.PUBLIC,
            ttl=self._BOOTSTRAP_TTL,
        )
        return BootstrapStatic.model_validate(data)

    async def get_teams(self) -> list[Team]:
        """Get all teams from bootstrap."""
        bootstrap = await self.get_bootstrap()
        return bootstrap.teams

    async def get_gameweeks(self) -> list[Gameweek]:
        """Get all gameweeks from bootstrap."""
        bootstrap = await self.get_bootstrap()
        return bootstrap.events

    async def get_current_gameweek(self) -> Gameweek | None:
        """Get the current gameweek, or None if not determinable."""
        gameweeks = await self.get_gameweeks()
        gw_id = await get_current_gameweek_id(gameweeks)
        if gw_id is None:
            return None
        for gw in gameweeks:
            if gw.id == gw_id:
                return gw
        return None

    async def get_next_gameweek(self) -> Gameweek | None:
        """Get the next gameweek, or None if not determinable."""
        gameweeks = await self.get_gameweeks()
        gw_id = await get_next_gameweek_id(gameweeks)
        if gw_id is None:
            return None
        for gw in gameweeks:
            if gw.id == gw_id:
                return gw
        return None

    async def get_element_types(self) -> list[ElementType]:
        """Get all element types (positions) from bootstrap."""
        bootstrap = await self.get_bootstrap()
        return bootstrap.element_types

    async def get_game_settings(self) -> GameSettings:
        """Get game settings from bootstrap."""
        bootstrap = await self.get_bootstrap()
        return bootstrap.game_settings
