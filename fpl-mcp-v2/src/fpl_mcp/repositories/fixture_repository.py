"""Fixture repository with blank/double gameweek detection.

All derived data (blank GW, double GW) is computed from cached fixtures
without additional API calls.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fpl_mcp.domain.fixture import Fixture
from fpl_mcp.infrastructure.cache import CacheTier, TieredCache
from fpl_mcp.infrastructure.fpl_client import FPLClient


class FixtureRepository:
    """Repository for fixture data.

    Fixtures are cached in CacheTier.PUBLIC. Blank and double gameweek
    computations are derived from the cached fixture set without extra API calls.
    """

    _FIXTURES_KEY = "fixtures"
    _FIXTURES_TTL = 3600

    def __init__(self, client: FPLClient, cache: TieredCache) -> None:
        self._client = client
        self._cache = cache

    async def _fetch_fixtures(self) -> list[dict[str, Any]]:
        return await self._client.get_fixtures()

    async def get_all(self) -> list[Fixture]:
        """Get all fixtures, cached."""
        data = await self._cache.get_or_fetch(
            self._FIXTURES_KEY,
            self._fetch_fixtures,
            tier=CacheTier.PUBLIC,
            ttl=self._FIXTURES_TTL,
        )
        return [Fixture.model_validate(f) for f in data]

    async def get_by_gameweek(self, gameweek_id: int) -> list[Fixture]:
        """Get fixtures for a specific gameweek."""
        fixtures = await self.get_all()
        return [f for f in fixtures if f.event == gameweek_id]

    async def get_by_team(self, team_id: int) -> list[Fixture]:
        """Get fixtures for a specific team (home or away)."""
        fixtures = await self.get_all()
        return [f for f in fixtures if f.team_h == team_id or f.team_a == team_id]

    async def get_player_fixtures(self, player_id: int, num: int = 5) -> list[dict]:
        """Get upcoming fixtures for a player's team.

        This is a placeholder — the actual team resolution requires the
        player repository. The presentation layer wires both together.

        Returns an empty list to satisfy the interface; services layer
        provides the full implementation using player_repo + fixture_repo.
        """
        # NOTE: Full implementation lives in FixtureService which has access
        # to both PlayerRepository and FixtureRepository.
        return []

    async def get_blank_gameweeks(self, num_gameweeks: int = 5) -> list[dict]:
        """Find blank gameweeks (gameweeks where a team has no fixture).

        Computed entirely from cached fixtures without extra API calls.

        Args:
            num_gameweeks: Number of upcoming gameweeks to analyze.

        Returns:
            List of dicts with gameweek_id and teams_without_fixture.
        """
        fixtures = await self.get_all()
        # Collect all team IDs
        all_team_ids: set[int] = set()
        for f in fixtures:
            all_team_ids.add(f.team_h)
            all_team_ids.add(f.team_a)

        # Group fixtures by gameweek
        gw_fixtures: dict[int, list[Fixture]] = defaultdict(list)
        for f in fixtures:
            if f.event is not None:
                gw_fixtures[f.event].append(f)

        # Determine upcoming gameweeks (sorted, unfinished or future)
        upcoming_gws = sorted(
            gw for gw in gw_fixtures if not all(f.finished for f in gw_fixtures[gw])
        )[:num_gameweeks]

        blanks: list[dict] = []
        for gw in upcoming_gws:
            teams_in_gw: set[int] = set()
            for f in gw_fixtures[gw]:
                teams_in_gw.add(f.team_h)
                teams_in_gw.add(f.team_a)

            missing = sorted(all_team_ids - teams_in_gw)
            if missing:
                blanks.append({
                    "gameweek_id": gw,
                    "teams_without_fixture": missing,
                    "blank_count": len(missing),
                })

        return blanks

    async def get_double_gameweeks(self, num_gameweeks: int = 5) -> list[dict]:
        """Find double gameweeks (gameweeks where a team has 2+ fixtures).

        Computed entirely from cached fixtures without extra API calls.

        Args:
            num_gameweeks: Number of upcoming gameweeks to analyze.

        Returns:
            List of dicts with gameweek_id and teams_with_multiple_fixtures.
        """
        fixtures = await self.get_all()

        # Group fixtures by gameweek
        gw_fixtures: dict[int, list[Fixture]] = defaultdict(list)
        for f in fixtures:
            if f.event is not None:
                gw_fixtures[f.event].append(f)

        # Determine upcoming gameweeks
        upcoming_gws = sorted(
            gw for gw in gw_fixtures if not all(f.finished for f in gw_fixtures[gw])
        )[:num_gameweeks]

        doubles: list[dict] = []
        for gw in upcoming_gws:
            team_counts: dict[int, int] = defaultdict(int)
            for f in gw_fixtures[gw]:
                team_counts[f.team_h] += 1
                team_counts[f.team_a] += 1

            multi = sorted(tid for tid, count in team_counts.items() if count > 1)
            if multi:
                doubles.append({
                    "gameweek_id": gw,
                    "teams_with_multiple_fixtures": multi,
                    "double_count": len(multi),
                })

        return doubles
