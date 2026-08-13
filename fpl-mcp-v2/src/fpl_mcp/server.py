"""MCP server initialization and lifecycle management."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from fpl_mcp.config import FPLConfig
from fpl_mcp.infrastructure.auth_service import FPLAuthService
from fpl_mcp.infrastructure.cache import TieredCache
from fpl_mcp.infrastructure.credentials import SecureCredentialManager
from fpl_mcp.infrastructure.fpl_client import FPLClient
from fpl_mcp.infrastructure.rate_limiter import RateLimiter
from fpl_mcp.presentation.prompts import register_prompts
from fpl_mcp.presentation.resources import ServiceContainer, register_resources
from fpl_mcp.presentation.tools import register_tools
from fpl_mcp.repositories import BootstrapRepository, FixtureRepository, PlayerRepository
from fpl_mcp.services import (
    CaptainService,
    FixtureService,
    LeagueService,
    PlayerService,
)

# LiveService may not exist yet in the services package; provide a graceful fallback.
try:
    from fpl_mcp.services.live_service import LiveService
except ImportError:
    # Minimal stub that satisfies the interface needed by the presentation layer.
    class LiveService:  # type: ignore[no-redef]
        """Fallback LiveService stub until the real implementation is available."""

        def __init__(self, fpl_client: FPLClient, player_repo: PlayerRepository, cache: TieredCache) -> None:
            self._client = fpl_client
            self._player_repo = player_repo
            self._cache = cache

        async def get_live_event(self, event_id: int) -> dict[str, Any]:
            return await self._client.get_live_event(event_id)

        async def get_dream_team(self, event_id: int) -> dict[str, Any]:
            return await self._client.get_dream_team(event_id)


logger = logging.getLogger(__name__)


class FPLMCPServer:
    """MCP server for Fantasy Premier League data and tools.

    Responsibilities:
    - Assemble the dependency graph (config → infra → repos → services).
    - Register resources, tools, and prompts with a ``MCPServer`` instance.
    - Run the server via stdio transport.
    """

    def __init__(self, services: ServiceContainer, config: FPLConfig) -> None:
        self._services = services
        self._config = config

    def create_server(self) -> FastMCP:
        """Create and configure the MCP server."""
        mcp = FastMCP(
            name="Fantasy Premier League",
            instructions=(
                "Access Fantasy Premier League data including player stats, "
                "fixtures, gameweeks, live scores, and squad analytics. "
                "Authenticated features (my team, leagues, transfers) require "
                "credentials configured via the CLI."
            ),
        )
        register_resources(mcp, self._services)
        register_tools(mcp, self._services)
        register_prompts(mcp)
        logger.info("MCP server '%s' created and registered.", mcp.name)
        return mcp

    async def run(self) -> None:
        """Run the MCP server on stdio transport.

        Uses ``run_stdio_async`` directly rather than ``mcp.run()`` because
        this coroutine already executes inside an ``asyncio.run()`` loop
        started by the entry point; ``mcp.run()`` would try to start a
        second event loop via ``anyio.run`` and raise ``RuntimeError``.
        """
        mcp = self.create_server()
        logger.info("Starting MCP server on stdio transport...")
        await mcp.run_stdio_async()


async def create_services(config: FPLConfig) -> ServiceContainer:
    """Bootstrap the full service dependency graph.

    This factory creates all infrastructure, repositories, and services
    required by the presentation layer.
    """
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=15.0),
        limits=httpx.Limits(max_connections=10),
    )
    rate_limiter = RateLimiter(
        max_requests=config.rate_limit_max,
        per_seconds=config.rate_limit_period,
    )
    cache = TieredCache()
    credentials = SecureCredentialManager()
    auth_service = FPLAuthService(
        http_client=http_client,
        credentials=credentials,
        token_url=config.resolved_token_url,
        client_id=config.oidc_client_id,
    )
    fpl_client = FPLClient(
        http_client=http_client,
        rate_limiter=rate_limiter,
        base_url=config.api_base_url,
        user_agent=config.user_agent,
    )
    bootstrap_repo = BootstrapRepository(fpl_client, cache)
    player_repo = PlayerRepository(fpl_client, cache)
    fixture_repo = FixtureRepository(fpl_client, cache)
    player_service = PlayerService(player_repo, fixture_repo)
    fixture_service = FixtureService(fixture_repo, player_repo, bootstrap_repo)
    captain_service = CaptainService(player_repo, fixture_repo, auth_service, config)
    league_service = LeagueService(auth_service, player_repo, bootstrap_repo, config)
    live_service = LiveService(fpl_client, player_repo, cache)
    return ServiceContainer(
        player_service=player_service,
        fixture_service=fixture_service,
        captain_service=captain_service,
        league_service=league_service,
        live_service=live_service,
        auth_service=auth_service,
        bootstrap_repo=bootstrap_repo,
        player_repo=player_repo,
        fixture_repo=fixture_repo,
    )
