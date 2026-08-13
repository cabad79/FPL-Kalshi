"""MCP resource registration for Fantasy Premier League static data."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from fpl_mcp.repositories import BootstrapRepository, FixtureRepository, PlayerRepository
from fpl_mcp.services import (
    CaptainService,
    FixtureService,
    LeagueService,
    LiveService,
    PlayerService,
)
from fpl_mcp.infrastructure.auth_service import FPLAuthService

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Container for all services and repositories used by the MCP layer.

    This container is intentionally flat — the presentation layer may need
    direct access to repositories for lightweight read-only resources.
    """

    def __init__(
        self,
        player_service: PlayerService,
        fixture_service: FixtureService,
        captain_service: CaptainService,
        league_service: LeagueService,
        live_service: LiveService,
        auth_service: FPLAuthService,
        bootstrap_repo: BootstrapRepository,
        player_repo: PlayerRepository,
        fixture_repo: FixtureRepository,
    ) -> None:
        self.player_service = player_service
        self.fixture_service = fixture_service
        self.captain_service = captain_service
        self.league_service = league_service
        self.live_service = live_service
        self.auth_service = auth_service
        self.bootstrap_repo = bootstrap_repo
        self.player_repo = player_repo
        self.fixture_repo = fixture_repo


def _safe(result: dict[str, Any], resource_name: str) -> dict[str, Any] | list[dict[str, Any]]:
    """Wrap a resource call in a standard error envelope.

    On success the original *result* is returned unchanged.
    On failure a dict with an ``error`` key is returned.
    """
    return result


def register_resources(mcp: FastMCP, services: ServiceContainer) -> None:
    """Register all FPL static and derived resources."""

    # ------------------------------------------------------------------ #
    # Players
    # ------------------------------------------------------------------ #

    @mcp.resource("fpl://static/players")
    async def get_all_players() -> list[dict[str, Any]]:
        """Return all players in the FPL database."""
        try:
            logger.info("Resource request: fpl://static/players")
            players = await services.player_repo.get_all()
            return [
                {
                    "id": p.id,
                    "name": p.full_name,
                    "web_name": p.web_name,
                    "team_id": p.team_id,
                    "position": _position_name(p.element_type),
                    "price": p.price_millions,
                    "total_points": p.total_points,
                    "form": float(p.form or 0),
                    "selected_by_percent": float(p.selected_by_percent or 0),
                }
                for p in players
            ]
        except Exception as exc:
            logger.exception("Resource error: fpl://static/players")
            return [{"error": f"Failed to fetch players: {exc}"}]

    @mcp.resource("fpl://static/players/{name}")
    async def get_player_by_name(name: str) -> dict[str, Any]:
        """Return a single player matched by name."""
        try:
            logger.info("Resource request: fpl://static/players/%s", name)
            results = await services.player_repo.search_by_name(name, limit=1)
            if not results:
                return {"error": f"Player '{name}' not found."}
            p = results[0]
            return {
                "id": p.id,
                "name": p.full_name,
                "web_name": p.web_name,
                "team_id": p.team_id,
                "position": _position_name(p.element_type),
                "price": p.price_millions,
                "total_points": p.total_points,
                "points_per_game": float(p.points_per_game or 0),
                "form": float(p.form or 0),
                "minutes": p.minutes,
                "goals_scored": p.goals_scored,
                "assists": p.assists,
                "clean_sheets": p.clean_sheets,
                "goals_conceded": p.goals_conceded,
                "saves": p.saves,
                "bonus": p.bonus,
                "bps": p.bps,
                "ict_index": float(p.ict_index or 0),
                "influence": float(p.influence or 0),
                "creativity": float(p.creativity or 0),
                "threat": float(p.threat or 0),
                "selected_by_percent": float(p.selected_by_percent or 0),
                "transfers_in": p.transfers_in,
                "transfers_out": p.transfers_out,
                "status": p.status,
                "news": p.news,
                "chance_of_playing_next_round": p.chance_of_playing_next_round,
                "ep_next": p.ep_next,
                "ep_this": p.ep_this,
                "expected_goals": p.expected_goals,
                "expected_assists": p.expected_assists,
            }
        except Exception as exc:
            logger.exception("Resource error: fpl://static/players/%s", name)
            return {"error": f"Failed to fetch player '{name}': {exc}"}

    # ------------------------------------------------------------------ #
    # Teams
    # ------------------------------------------------------------------ #

    @mcp.resource("fpl://static/teams")
    async def get_all_teams() -> list[dict[str, Any]]:
        """Return all Premier League teams."""
        try:
            logger.info("Resource request: fpl://static/teams")
            teams = await services.bootstrap_repo.get_teams()
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "short_name": t.short_name,
                    "strength": t.strength,
                    "strength_overall_home": t.strength_overall_home,
                    "strength_overall_away": t.strength_overall_away,
                    "strength_attack_home": t.strength_attack_home,
                    "strength_attack_away": t.strength_attack_away,
                    "strength_defence_home": t.strength_defence_home,
                    "strength_defence_away": t.strength_defence_away,
                }
                for t in teams
            ]
        except Exception as exc:
            logger.exception("Resource error: fpl://static/teams")
            return [{"error": f"Failed to fetch teams: {exc}"}]

    @mcp.resource("fpl://static/teams/{name}")
    async def get_team_by_name(name: str) -> dict[str, Any]:
        """Return a single team matched by name."""
        try:
            logger.info("Resource request: fpl://static/teams/%s", name)
            teams = await services.bootstrap_repo.get_teams()
            name_lower = name.lower().strip()
            for t in teams:
                if name_lower in t.name.lower() or name_lower in t.short_name.lower():
                    return {
                        "id": t.id,
                        "name": t.name,
                        "short_name": t.short_name,
                        "strength": t.strength,
                        "strength_overall_home": t.strength_overall_home,
                        "strength_overall_away": t.strength_overall_away,
                        "strength_attack_home": t.strength_attack_home,
                        "strength_attack_away": t.strength_attack_away,
                        "strength_defence_home": t.strength_defence_home,
                        "strength_defence_away": t.strength_defence_away,
                    }
            return {"error": f"Team '{name}' not found."}
        except Exception as exc:
            logger.exception("Resource error: fpl://static/teams/%s", name)
            return {"error": f"Failed to fetch team '{name}': {exc}"}

    # ------------------------------------------------------------------ #
    # Gameweeks
    # ------------------------------------------------------------------ #

    @mcp.resource("fpl://gameweeks/current")
    async def get_current_gameweek() -> dict[str, Any]:
        """Return the current (or next upcoming) gameweek."""
        try:
            logger.info("Resource request: fpl://gameweeks/current")
            gw = await services.bootstrap_repo.get_current_gameweek()
            if gw is None:
                return {"error": "Unable to determine current gameweek."}
            return {
                "id": gw.id,
                "name": gw.name,
                "deadline_time": gw.deadline_time.isoformat(),
                "finished": gw.finished,
                "is_current": gw.is_current,
                "is_next": gw.is_next,
                "is_previous": gw.is_previous,
                "average_entry_score": gw.average_entry_score,
                "highest_score": gw.highest_score,
            }
        except Exception as exc:
            logger.exception("Resource error: fpl://gameweeks/current")
            return {"error": f"Failed to fetch current gameweek: {exc}"}

    @mcp.resource("fpl://gameweeks/all")
    async def get_all_gameweeks() -> list[dict[str, Any]]:
        """Return all gameweeks in the season."""
        try:
            logger.info("Resource request: fpl://gameweeks/all")
            gameweeks = await services.bootstrap_repo.get_gameweeks()
            return [
                {
                    "id": g.id,
                    "name": g.name,
                    "deadline_time": g.deadline_time.isoformat(),
                    "finished": g.finished,
                    "is_current": g.is_current,
                    "is_next": g.is_next,
                    "is_previous": g.is_previous,
                    "average_entry_score": g.average_entry_score,
                    "highest_score": g.highest_score,
                }
                for g in gameweeks
            ]
        except Exception as exc:
            logger.exception("Resource error: fpl://gameweeks/all")
            return [{"error": f"Failed to fetch gameweeks: {exc}"}]

    # ------------------------------------------------------------------ #
    # Fixtures
    # ------------------------------------------------------------------ #

    @mcp.resource("fpl://fixtures")
    async def get_all_fixtures() -> list[dict[str, Any]]:
        """Return all fixtures in the season."""
        try:
            logger.info("Resource request: fpl://fixtures")
            fixtures = await services.fixture_repo.get_all()
            return [_fixture_to_dict(f) for f in fixtures]
        except Exception as exc:
            logger.exception("Resource error: fpl://fixtures")
            return [{"error": f"Failed to fetch fixtures: {exc}"}]

    @mcp.resource("fpl://fixtures/gameweek/{gameweek_id}")
    async def get_gameweek_fixtures(gameweek_id: int) -> list[dict[str, Any]]:
        """Return fixtures for a specific gameweek."""
        try:
            logger.info("Resource request: fpl://fixtures/gameweek/%s", gameweek_id)
            fixtures = await services.fixture_repo.get_by_gameweek(gameweek_id)
            return [_fixture_to_dict(f) for f in fixtures]
        except Exception as exc:
            logger.exception("Resource error: fpl://fixtures/gameweek/%s", gameweek_id)
            return [{"error": f"Failed to fetch fixtures for GW {gameweek_id}: {exc}"}]

    @mcp.resource("fpl://fixtures/team/{team_name}")
    async def get_team_fixtures(team_name: str) -> list[dict[str, Any]]:
        """Return fixtures for a team matched by name."""
        try:
            logger.info("Resource request: fpl://fixtures/team/%s", team_name)
            teams = await services.bootstrap_repo.get_teams()
            team_id = None
            name_lower = team_name.lower().strip()
            for t in teams:
                if name_lower in t.name.lower() or name_lower in t.short_name.lower():
                    team_id = t.id
                    break
            if team_id is None:
                return [{"error": f"Team '{team_name}' not found."}]
            fixtures = await services.fixture_repo.get_by_team(team_id)
            return [_fixture_to_dict(f) for f in fixtures]
        except Exception as exc:
            logger.exception("Resource error: fpl://fixtures/team/%s", team_name)
            return [{"error": f"Failed to fetch fixtures for team '{team_name}': {exc}"}]

    @mcp.resource("fpl://players/{player_name}/fixtures")
    async def get_player_fixtures(player_name: str) -> dict[str, Any]:
        """Return upcoming fixtures for a player matched by name."""
        try:
            logger.info("Resource request: fpl://players/%s/fixtures", player_name)
            results = await services.player_repo.search_by_name(player_name, limit=1)
            if not results:
                return {"error": f"Player '{player_name}' not found."}
            player = results[0]
            analysis = await services.fixture_service.analyze_player_fixtures(
                player.id, num=5
            )
            return analysis
        except Exception as exc:
            logger.exception("Resource error: fpl://players/%s/fixtures", player_name)
            return {"error": f"Failed to fetch fixtures for player '{player_name}': {exc}"}

    # ------------------------------------------------------------------ #
    # Blank / Double Gameweeks
    # ------------------------------------------------------------------ #

    @mcp.resource("fpl://gameweeks/blank")
    async def get_blank_gameweeks() -> list[dict[str, Any]]:
        """Return upcoming blank gameweeks."""
        try:
            logger.info("Resource request: fpl://gameweeks/blank")
            blanks = await services.fixture_repo.get_blank_gameweeks(num_gameweeks=5)
            return blanks
        except Exception as exc:
            logger.exception("Resource error: fpl://gameweeks/blank")
            return [{"error": f"Failed to fetch blank gameweeks: {exc}"}]

    @mcp.resource("fpl://gameweeks/double")
    async def get_double_gameweeks() -> list[dict[str, Any]]:
        """Return upcoming double gameweeks."""
        try:
            logger.info("Resource request: fpl://gameweeks/double")
            doubles = await services.fixture_repo.get_double_gameweeks(num_gameweeks=5)
            return doubles
        except Exception as exc:
            logger.exception("Resource error: fpl://gameweeks/double")
            return [{"error": f"Failed to fetch double gameweeks: {exc}"}]


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _position_name(element_type: int) -> str:
    """Map element_type integer to position code."""
    mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    return mapping.get(element_type, "UNK")


def _fixture_to_dict(fixture: Any) -> dict[str, Any]:
    """Serialize a Fixture domain object to a flat dict."""
    return {
        "id": fixture.id,
        "event": fixture.event,
        "finished": fixture.finished,
        "finished_provisional": fixture.finished_provisional,
        "kickoff_time": fixture.kickoff_time.isoformat()
        if hasattr(fixture.kickoff_time, "isoformat")
        else fixture.kickoff_time,
        "team_h": fixture.team_h,
        "team_a": fixture.team_a,
        "team_h_score": fixture.team_h_score,
        "team_a_score": fixture.team_a_score,
        "team_h_difficulty": fixture.team_h_difficulty,
        "team_a_difficulty": fixture.team_a_difficulty,
    }
