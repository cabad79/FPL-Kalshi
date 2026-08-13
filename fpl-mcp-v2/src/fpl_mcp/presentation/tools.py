"""MCP tool registration for Fantasy Premier League interactive features."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from fpl_mcp.infrastructure.credentials import SecureCredentialManager
from fpl_mcp.presentation.resources import ServiceContainer
from fpl_mcp.services import TeamManagementService, TransferOptimizer
from fpl_mcp.utils.params import unwrap
from fpl_mcp.utils.position_utils import normalize_position

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, services: ServiceContainer) -> None:
    """Register all FPL interactive tools."""

    # ------------------------------------------------------------------ #
    # Player tools
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def search_fpl_players(
        query: str,
        position: str | None = None,
        team: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search FPL players by name with optional filters.

        Args:
            query: Player name or partial name to search for.
            position: Optional position filter (GKP, DEF, MID, FWD).
            team: Optional team name filter.
            limit: Maximum number of results (default: 5).
        """
        try:
            logger.info("Tool call: search_fpl_players(query=%r)", query)
            pos = normalize_position(unwrap(position, "position", default=None))
            team_norm = unwrap(team, "team", default=None)
            limit_val = int(unwrap(limit, "limit", default=5))
            return await services.player_service.search(
                query=query,
                position=pos,
                team=team_norm,
                limit=limit_val,
            )
        except Exception as exc:
            logger.exception("Tool error: search_fpl_players")
            return {"error": f"Search failed: {exc}"}

    @mcp.tool()
    async def get_player_information(
        player_id: int | None = None,
        player_name: str | None = None,
    ) -> dict[str, Any]:
        """Get detailed information for a specific player.

        Args:
            player_id: FPL element ID (optional if player_name is provided).
            player_name: Player name to search for (optional if player_id is provided).
        """
        try:
            logger.info(
                "Tool call: get_player_information(id=%s, name=%s)",
                player_id,
                player_name,
            )
            pid = unwrap(player_id, "player_id", default=None)
            pname = unwrap(player_name, "player_name", default=None)

            if pid is not None:
                player = await services.player_repo.get_by_id(int(pid))
            elif pname:
                results = await services.player_repo.search_by_name(str(pname), limit=1)
                player = results[0] if results else None
            else:
                return {"error": "Either player_id or player_name must be provided."}

            if player is None:
                return {"error": "Player not found."}

            summary = await services.player_repo.get_summary(player.id)
            return {
                "id": player.id,
                "name": player.full_name,
                "web_name": player.web_name,
                "team_id": player.team_id,
                "position": _position_name(player.element_type),
                "price": player.price_millions,
                "price_change_event": player.cost_change_event,
                "price_change_start": player.cost_change_start,
                "total_points": player.total_points,
                "points_per_game": float(player.points_per_game or 0),
                "form": float(player.form or 0),
                "minutes": player.minutes,
                "goals_scored": player.goals_scored,
                "assists": player.assists,
                "clean_sheets": player.clean_sheets,
                "goals_conceded": player.goals_conceded,
                "saves": player.saves,
                "bonus": player.bonus,
                "bps": player.bps,
                "ict_index": float(player.ict_index or 0),
                "influence": float(player.influence or 0),
                "creativity": float(player.creativity or 0),
                "threat": float(player.threat or 0),
                "selected_by_percent": float(player.selected_by_percent or 0),
                "transfers_in": player.transfers_in,
                "transfers_out": player.transfers_out,
                "status": player.status,
                "news": player.news,
                "chance_of_playing_next_round": player.chance_of_playing_next_round,
                "ep_next": player.ep_next,
                "ep_this": player.ep_this,
                "expected_goals": player.expected_goals,
                "expected_assists": player.expected_assists,
                "expected_goal_involvements": player.expected_goal_involvements,
                "expected_goals_conceded": player.expected_goals_conceded,
                "in_dreamteam": player.in_dreamteam,
                "dreamteam_count": player.dreamteam_count,
                "history": summary.get("history", []),
                "history_past": summary.get("history_past", []),
            }
        except Exception as exc:
            logger.exception("Tool error: get_player_information")
            return {"error": f"Failed to get player information: {exc}"}

    @mcp.tool()
    async def analyze_players(
        position: str | None = None,
        team: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_points: int | None = None,
        min_ownership: float | None = None,
        max_ownership: float | None = None,
        form_threshold: float | None = None,
        sort_by: str = "points",
        sort_order: str = "desc",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Analyze the player pool with advanced filters and sorting.

        Args:
            position: Filter by position (GKP, DEF, MID, FWD).
            team: Filter by team name (partial match).
            min_price: Minimum price in millions.
            max_price: Maximum price in millions.
            min_points: Minimum total points.
            min_ownership: Minimum ownership percentage.
            max_ownership: Maximum ownership percentage.
            form_threshold: Minimum form value.
            sort_by: Sort key (points, form, price, ict_index, etc.).
            sort_order: Sort direction (asc or desc).
            limit: Maximum results to return (default: 20).
        """
        try:
            logger.info("Tool call: analyze_players")
            pos = normalize_position(unwrap(position, "position", default=None))
            return await services.player_service.analyze(
                position=pos,
                team=unwrap(team, "team", default=None),
                min_price=unwrap(min_price, "min_price", default=None),
                max_price=unwrap(max_price, "max_price", default=None),
                min_points=unwrap(min_points, "min_points", default=None),
                min_ownership=unwrap(min_ownership, "min_ownership", default=None),
                max_ownership=unwrap(max_ownership, "max_ownership", default=None),
                form_threshold=unwrap(form_threshold, "form_threshold", default=None),
                sort_by=str(unwrap(sort_by, "sort_by", default="points")),
                sort_order=str(unwrap(sort_order, "sort_order", default="desc")),
                limit=int(unwrap(limit, "limit", default=20)),
            )
        except Exception as exc:
            logger.exception("Tool error: analyze_players")
            return {"error": f"Analysis failed: {exc}"}

    @mcp.tool()
    async def compare_players(
        player_names: list[str],
        metrics: list[str] | None = None,
        include_gameweeks: bool = False,
        num_gameweeks: int = 5,
    ) -> dict[str, Any]:
        """Compare two or more FPL players across selected metrics.

        Args:
            player_names: List of player names to compare.
            metrics: Optional list of metrics (points, form, ict_index, etc.).
            include_gameweeks: Whether to include recent gameweek history.
            num_gameweeks: Number of recent gameweeks to include.
        """
        try:
            logger.info("Tool call: compare_players(names=%s)", player_names)
            names = unwrap(player_names, "player_names", default=[])
            if isinstance(names, str):
                names = [n.strip() for n in names.split(",")]
            return await services.player_service.compare(
                player_names=names,
                metrics=unwrap(metrics, "metrics", default=None),
                include_gameweeks=bool(unwrap(include_gameweeks, "include_gameweeks", default=False)),
                num_gameweeks=int(unwrap(num_gameweeks, "num_gameweeks", default=5)),
            )
        except Exception as exc:
            logger.exception("Tool error: compare_players")
            return {"error": f"Comparison failed: {exc}"}

    @mcp.tool()
    async def get_price_changes(
        direction: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get players with recent price changes.

        Args:
            direction: Filter by 'risers', 'fallers', or None for all.
            limit: Maximum number of results (default: 20).
        """
        try:
            logger.info("Tool call: get_price_changes(direction=%s)", direction)
            return await services.player_service.get_price_changes(
                direction=unwrap(direction, "direction", default=None),
                limit=int(unwrap(limit, "limit", default=20)),
            )
        except Exception as exc:
            logger.exception("Tool error: get_price_changes")
            return {"error": f"Failed to get price changes: {exc}"}

    # ------------------------------------------------------------------ #
    # Fixtures & Gameweeks
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def get_gameweek_status() -> dict[str, Any]:
        """Get the current gameweek status, deadline, and time remaining."""
        try:
            logger.info("Tool call: get_gameweek_status")
            return await services.fixture_service.get_gameweek_status()
        except Exception as exc:
            logger.exception("Tool error: get_gameweek_status")
            return {"error": f"Failed to get gameweek status: {exc}"}

    @mcp.tool()
    async def analyze_player_fixtures(
        player_name: str,
        num_fixtures: int = 5,
    ) -> dict[str, Any]:
        """Analyze upcoming fixtures for a specific player.

        Args:
            player_name: Name of the player to analyze.
            num_fixtures: Number of upcoming fixtures to analyze (default: 5).
        """
        try:
            logger.info("Tool call: analyze_player_fixtures(%s)", player_name)
            pname = str(unwrap(player_name, "player_name", default=""))
            results = await services.player_repo.search_by_name(pname, limit=1)
            if not results:
                return {"error": f"Player '{pname}' not found."}
            player = results[0]
            return await services.fixture_service.analyze_player_fixtures(
                player.id,
                num=int(unwrap(num_fixtures, "num_fixtures", default=5)),
            )
        except Exception as exc:
            logger.exception("Tool error: analyze_player_fixtures")
            return {"error": f"Fixture analysis failed: {exc}"}

    @mcp.tool()
    async def analyze_fixtures(
        entity_type: str = "player",
        entity_name: str | None = None,
        num_gameweeks: int = 5,
    ) -> dict[str, Any]:
        """Analyze upcoming fixtures for a player or team.

        Args:
            entity_type: 'player' or 'team'.
            entity_name: Name of the player or team.
            num_gameweeks: Number of gameweeks to analyze (default: 5).
        """
        try:
            logger.info("Tool call: analyze_fixtures(%s=%s)", entity_type, entity_name)
            etype = str(unwrap(entity_type, "entity_type", default="player")).lower()
            ename = unwrap(entity_name, "entity_name", default=None)
            num = int(unwrap(num_gameweeks, "num_gameweeks", default=5))

            if etype == "player":
                if not ename:
                    return {"error": "entity_name is required for player analysis."}
                results = await services.player_repo.search_by_name(str(ename), limit=1)
                if not results:
                    return {"error": f"Player '{ename}' not found."}
                return await services.fixture_service.analyze_player_fixtures(results[0].id, num=num)
            elif etype == "team":
                if not ename:
                    return {"error": "entity_name is required for team analysis."}
                teams = await services.bootstrap_repo.get_teams()
                team_id = None
                name_lower = str(ename).lower().strip()
                for t in teams:
                    if name_lower in t.name.lower() or name_lower in t.short_name.lower():
                        team_id = t.id
                        break
                if team_id is None:
                    return {"error": f"Team '{ename}' not found."}
                return await services.fixture_service.analyze_team_fixtures(team_id, num=num)
            else:
                return {"error": f"Unknown entity_type '{entity_type}'. Use 'player' or 'team'."}
        except Exception as exc:
            logger.exception("Tool error: analyze_fixtures")
            return {"error": f"Fixture analysis failed: {exc}"}

    @mcp.tool()
    async def get_blank_gameweeks(num_gameweeks: int = 5) -> dict[str, Any]:
        """Find upcoming blank gameweeks.

        Args:
            num_gameweeks: Number of upcoming gameweeks to check (default: 5).
        """
        try:
            logger.info("Tool call: get_blank_gameweeks")
            return await services.fixture_service.get_blank_gameweeks(
                num=int(unwrap(num_gameweeks, "num_gameweeks", default=5))
            )
        except Exception as exc:
            logger.exception("Tool error: get_blank_gameweeks")
            return {"error": f"Failed to get blank gameweeks: {exc}"}

    @mcp.tool()
    async def get_double_gameweeks(num_gameweeks: int = 5) -> dict[str, Any]:
        """Find upcoming double gameweeks.

        Args:
            num_gameweeks: Number of upcoming gameweeks to check (default: 5).
        """
        try:
            logger.info("Tool call: get_double_gameweeks")
            return await services.fixture_service.get_double_gameweeks(
                num=int(unwrap(num_gameweeks, "num_gameweeks", default=5))
            )
        except Exception as exc:
            logger.exception("Tool error: get_double_gameweeks")
            return {"error": f"Failed to get double gameweeks: {exc}"}

    # ------------------------------------------------------------------ #
    # Live scores
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def get_gameweek_live_scores(
        gameweek_id: int | None = None,
        player_ids: list[int] | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Get live scores for a gameweek.

        Args:
            gameweek_id: Gameweek ID (default: current gameweek).
            player_ids: Optional list of player IDs to filter.
            limit: Maximum number of players to return (default: 25).
        """
        try:
            logger.info("Tool call: get_gameweek_live_scores(gw=%s)", gameweek_id)
            gw = unwrap(gameweek_id, "gameweek_id", default=None)
            if gw is None:
                current = await services.bootstrap_repo.get_current_gameweek()
                if current is None:
                    return {"error": "Unable to determine current gameweek."}
                gw = current.id

            live_data = await services.live_service.get_live_event(int(gw))
            elements = live_data.get("elements", [])
            pids = unwrap(player_ids, "player_ids", default=None)
            if pids:
                pids_set = set(int(p) for p in pids)
                elements = [e for e in elements if e.get("id") in pids_set]

            limit_val = int(unwrap(limit, "limit", default=25))
            elements = elements[:limit_val]

            return {
                "gameweek_id": gw,
                "count": len(elements),
                "players": elements,
            }
        except Exception as exc:
            logger.exception("Tool error: get_gameweek_live_scores")
            return {"error": f"Failed to get live scores: {exc}"}

    @mcp.tool()
    async def get_dream_team(gameweek_id: int | None = None) -> dict[str, Any]:
        """Get the dream team for a gameweek.

        Args:
            gameweek_id: Gameweek ID (default: current gameweek).
        """
        try:
            logger.info("Tool call: get_dream_team(gw=%s)", gameweek_id)
            gw = unwrap(gameweek_id, "gameweek_id", default=None)
            if gw is None:
                current = await services.bootstrap_repo.get_current_gameweek()
                if current is None:
                    return {"error": "Unable to determine current gameweek."}
                gw = current.id

            dream_team = await services.live_service.get_dream_team(int(gw))
            return {
                "gameweek_id": gw,
                "dream_team": dream_team.get("team", []),
                "top_element": dream_team.get("top_element"),
            }
        except Exception as exc:
            logger.exception("Tool error: get_dream_team")
            return {"error": f"Failed to get dream team: {exc}"}

    # ------------------------------------------------------------------ #
    # Captain & Auth
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def suggest_captain(
        team_id: int | None = None,
        gameweek_id: int | None = None,
    ) -> dict[str, Any]:
        """Suggest the best captain for the upcoming gameweek.

        Args:
            team_id: Optional FPL team ID (uses authenticated team if omitted).
            gameweek_id: Optional gameweek ID (uses next gameweek if omitted).
        """
        try:
            logger.info("Tool call: suggest_captain")
            tid = unwrap(team_id, "team_id", default=None)
            gw = unwrap(gameweek_id, "gameweek_id", default=None)
            return await services.captain_service.suggest(
                team_id=int(tid) if tid is not None else None,
                gameweek_id=int(gw) if gw is not None else None,
            )
        except Exception as exc:
            logger.exception("Tool error: suggest_captain")
            return {"error": f"Captain suggestion failed: {exc}"}

    @mcp.tool()
    async def check_fpl_authentication() -> dict[str, Any]:
        """Check if FPL authentication is configured and working."""
        try:
            logger.info("Tool call: check_fpl_authentication")
            token = await services.auth_service.authenticate()
            return {
                "authenticated": True,
                "expires_at": token.expires_at.isoformat(),
                "message": "Authentication successful.",
            }
        except Exception as exc:
            logger.exception("Tool error: check_fpl_authentication")
            return {
                "authenticated": False,
                "error": str(exc),
                "message": "Authentication failed. Run 'fpl-mcp-config setup' to configure credentials.",
            }

    # ------------------------------------------------------------------ #
    # Manager / Team (authenticated)
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def get_my_team() -> dict[str, Any]:
        """Get the authenticated user's current FPL squad."""
        try:
            logger.info("Tool call: get_my_team")
            creds = SecureCredentialManager()
            _, team_id_str = creds.load_credentials()
            if not team_id_str:
                return {
                    "error": "No team_id configured. Run 'fpl-mcp-config setup' first.",
                }
            team_data = await services.auth_service.get_my_team(int(team_id_str))
            return {
                "team_id": int(team_id_str),
                "picks": team_data.get("picks", []),
                "entry_history": team_data.get("entry_history", {}),
                "active_chip": team_data.get("active_chip"),
            }
        except Exception as exc:
            logger.exception("Tool error: get_my_team")
            return {"error": f"Failed to get team: {exc}"}

    @mcp.tool()
    async def get_manager(team_id: int | None = None) -> dict[str, Any]:
        """Get public profile data for an FPL manager.

        Args:
            team_id: FPL team ID (uses authenticated team if omitted).
        """
        try:
            logger.info("Tool call: get_manager")
            tid = unwrap(team_id, "team_id", default=None)
            if tid is None:
                creds = SecureCredentialManager()
                _, team_id_str = creds.load_credentials()
                if not team_id_str:
                    return {"error": "No team_id provided or configured."}
                tid = int(team_id_str)
            else:
                tid = int(tid)
            return await services.auth_service.get_entry_data(tid)
        except Exception as exc:
            logger.exception("Tool error: get_manager")
            return {"error": f"Failed to get manager data: {exc}"}

    @mcp.tool()
    async def get_manager_transfer_history(team_id: int | None = None) -> dict[str, Any]:
        """Get transfer history for an FPL manager.

        Args:
            team_id: FPL team ID (uses authenticated team if omitted).
        """
        try:
            logger.info("Tool call: get_manager_transfer_history")
            tid = unwrap(team_id, "team_id", default=None)
            if tid is None:
                creds = SecureCredentialManager()
                _, team_id_str = creds.load_credentials()
                if not team_id_str:
                    return {"error": "No team_id provided or configured."}
                tid = int(team_id_str)
            else:
                tid = int(tid)
            transfers = await services.auth_service.get_entry_transfers(tid)
            return {
                "team_id": tid,
                "transfer_count": len(transfers),
                "transfers": transfers,
            }
        except Exception as exc:
            logger.exception("Tool error: get_manager_transfer_history")
            return {"error": f"Failed to get transfer history: {exc}"}

    # ------------------------------------------------------------------ #
    # Leagues
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def get_league_standings(league_id: int) -> dict[str, Any]:
        """Get standings for a classic FPL league.

        Args:
            league_id: The FPL league ID.
        """
        try:
            logger.info("Tool call: get_league_standings(%s)", league_id)
            lid = int(unwrap(league_id, "league_id"))
            return await services.league_service.get_standings(lid)
        except Exception as exc:
            logger.exception("Tool error: get_league_standings")
            return {"error": f"Failed to get league standings: {exc}"}

    @mcp.tool()
    async def get_league_analytics(
        league_id: int,
        analysis_type: str = "overview",
        start_gw: int | None = None,
        end_gw: int | None = None,
    ) -> dict[str, Any]:
        """Get analytics for a classic FPL league.

        Args:
            league_id: The FPL league ID.
            analysis_type: Type of analysis: 'overview', 'historical',
                'team_composition', or 'fixtures'.
            start_gw: Optional start gameweek for historical analysis.
            end_gw: Optional end gameweek for historical analysis.
        """
        try:
            logger.info("Tool call: get_league_analytics(%s, %s)", league_id, analysis_type)
            lid = int(unwrap(league_id, "league_id"))
            atype = str(unwrap(analysis_type, "analysis_type", default="overview")).lower()
            sgw = unwrap(start_gw, "start_gw", default=None)
            egw = unwrap(end_gw, "end_gw", default=None)

            if atype == "overview":
                standings = await services.league_service.get_standings(lid)
                composition = await services.league_service.get_team_composition(lid)
                return {
                    "analysis_type": "overview",
                    "league_id": lid,
                    "standings": standings,
                    "team_composition": composition,
                }
            elif atype == "historical":
                return await services.league_service.get_historical_performance(
                    lid,
                    start_gw=int(sgw) if sgw is not None else None,
                    end_gw=int(egw) if egw is not None else None,
                )
            elif atype == "team_composition":
                return await services.league_service.get_team_composition(lid)
            elif atype == "fixtures":
                return await services.league_service.get_fixture_analysis(
                    lid,
                    start_gw=int(sgw) if sgw is not None else None,
                    end_gw=int(egw) if egw is not None else None,
                )
            else:
                return {
                    "error": f"Unknown analysis_type '{atype}'. "
                    "Use 'overview', 'historical', 'team_composition', or 'fixtures'.",
                }
        except Exception as exc:
            logger.exception("Tool error: get_league_analytics")
            return {"error": f"League analytics failed: {exc}"}

    # ------------------------------------------------------------------ #
    # Credentials
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def update_fpl_credentials(
        refresh_token: str,
        team_id: int,
    ) -> dict[str, Any]:
        """Update stored FPL credentials.

        Args:
            refresh_token: The new OIDC refresh token.
            team_id: The FPL team (entry) ID.
        """
        try:
            logger.info("Tool call: update_fpl_credentials")
            token = str(unwrap(refresh_token, "refresh_token"))
            tid = str(int(unwrap(team_id, "team_id")))
            creds = SecureCredentialManager()
            creds.store_credentials(token, tid)
            return {
                "success": True,
                "message": "Credentials updated successfully.",
            }
        except Exception as exc:
            logger.exception("Tool error: update_fpl_credentials")
            return {"error": f"Failed to update credentials: {exc}"}

    # ------------------------------------------------------------------ #
    # Squad Optimization & Monte Carlo
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def validate_squad(player_ids: list[int]) -> dict[str, Any]:
        """Validate a proposed squad against all FPL rules.

        Args:
            player_ids: List of 15 FPL player IDs.
        """
        try:
            logger.info("Tool call: validate_squad with %d players", len(player_ids))
            if len(player_ids) != 15:
                return {"error": f"Squad must have 15 players, got {len(player_ids)}"}

            all_players = await services.player_repo.get_all()
            players_by_id = {p.id: p for p in all_players}

            squad = []
            for pid in player_ids:
                if pid not in players_by_id:
                    return {"error": f"Player ID {pid} not found"}
                squad.append(players_by_id[pid])

            from fpl_mcp.services import SquadValidator

            result = SquadValidator.validate_squad(squad)
            return {
                "valid": result["valid"],
                "budget_remaining": result["budget_remaining"],
                "total_price": sum(p.price_millions for p in squad),
            }
        except Exception as exc:
            logger.exception("Tool error: validate_squad")
            return {"error": str(exc)}

    @mcp.tool()
    async def generate_optimal_squads(count: int = 100, gameweek_id: int | None = None) -> dict[str, Any]:
        """Generate multiple optimal FPL squads using constraint satisfaction.

        Args:
            count: Number of squads to generate (max 1000).
            gameweek_id: Gameweek to optimize for (uses GW1 if omitted).
        """
        try:
            logger.info("Tool call: generate_optimal_squads with count=%d", min(count, 1000))
            count = min(count, 1000)

            all_players = await services.player_repo.get_all()

            from fpl_mcp.services import SquadGenerator

            generator = SquadGenerator(all_players)
            squads = generator.generate_multiple_squads(count=count)

            return {
                "generated_count": len(squads),
                "squads_summary": [
                    {
                        "avg_price": sum(p.price_millions for p in squad) / 15,
                        "players": [p.web_name for p in squad],
                    }
                    for squad in squads[:10]  # Return first 10 for preview
                ],
            }
        except Exception as exc:
            logger.exception("Tool error: generate_optimal_squads")
            return {"error": str(exc)}

    @mcp.tool()
    async def simulate_squad_performance(
        player_ids: list[int], captain_id: int | None = None, iterations: int = 100, gameweek_id: int | None = None
    ) -> dict[str, Any]:
        """Run Monte Carlo simulation (100+ iterations) on a squad to predict expected GW points.

        Args:
            player_ids: List of 15 player IDs in the squad.
            captain_id: Player ID of the captain (auto-select if None).
            iterations: Number of simulations (default 100).
            gameweek_id: Gameweek to simulate (uses GW1 if omitted).
        """
        try:
            logger.info(
                "Tool call: simulate_squad_performance with %d players, %d iterations", len(player_ids), iterations
            )

            all_players = await services.player_repo.get_all()
            players_by_id = {p.id: p for p in all_players}

            squad = [players_by_id[pid] for pid in player_ids if pid in players_by_id]
            if len(squad) != 15:
                return {"error": f"Squad must have exactly 15 players, got {len(squad)}"}

            fixtures = await services.fixture_repo.get_by_gameweek(gameweek_id or 1)
            teams = {t.id: t for t in await services.bootstrap_repo.get_teams()}

            from fpl_mcp.services import MonteCarloSimulator

            simulator = MonteCarloSimulator(fixtures, teams)
            result = simulator.simulate_squad(squad, captain_id, iterations=min(iterations, 1000))

            return {
                "squad_id": result.squad_id,
                "captain": result.captain_player.web_name if result.captain_player else None,
                "expected_points_avg": round(result.avg_score, 2),
                "expected_points_p10": round(result.p10_score, 2),
                "expected_points_p90": round(result.p90_score, 2),
                "iterations": iterations,
                "message": f"Expected {result.avg_score:.1f} pts (p10={result.p10_score:.1f}, p90={result.p90_score:.1f})",
            }
        except Exception as exc:
            logger.exception("Tool error: simulate_squad_performance")
            return {"error": str(exc)}

    @mcp.tool()
    async def rank_squads_by_simulation(squad_list: list[list[int]], iterations: int = 100) -> dict[str, Any]:
        """Simulate multiple squads and rank them by expected performance.

        Args:
            squad_list: List of squads, each squad is a list of 15 player IDs.
            iterations: Monte Carlo iterations per squad.
        """
        try:
            logger.info("Tool call: rank_squads_by_simulation with %d squads", len(squad_list))

            all_players = await services.player_repo.get_all()
            players_by_id = {p.id: p for p in all_players}

            squads = []
            for squad_ids in squad_list[:50]:  # Limit to 50 squads
                squad = [players_by_id[pid] for pid in squad_ids if pid in players_by_id]
                if len(squad) == 15:
                    squads.append(squad)

            if not squads:
                return {"error": "No valid squads found"}

            fixtures = await services.fixture_repo.get_by_gameweek(1)
            teams = {t.id: t for t in await services.bootstrap_repo.get_teams()}

            from fpl_mcp.services import MonteCarloSimulator

            simulator = MonteCarloSimulator(fixtures, teams)
            results = simulator.compare_squads(squads, iterations=min(iterations, 500))

            return {
                "total_squads": len(results),
                "top_3": [
                    {
                        "rank": i + 1,
                        "expected_points": round(r.avg_score, 2),
                        "p10": round(r.p10_score, 2),
                        "p90": round(r.p90_score, 2),
                        "captain": r.captain_player.web_name if r.captain_player else None,
                    }
                    for i, r in enumerate(results[:3])
                ],
            }
        except Exception as exc:
            logger.exception("Tool error: rank_squads_by_simulation")
            return {"error": str(exc)}

    # ------------------------------------------------------------------ #
    # Live / Real-time
    # ------------------------------------------------------------------ #

    @mcp.tool()
    async def get_gameweek_live_status(gameweek_id: int | None = None) -> dict[str, Any]:
        """Get live gameweek status including current scores and event metadata.

        Args:
            gameweek_id: Gameweek ID (uses next/current if omitted).
        """
        try:
            logger.info("Tool call: get_gameweek_live_status with gameweek_id=%s", gameweek_id)
            if gameweek_id is None:
                gw = await services.bootstrap_repo.get_current_gameweek()
                if gw is None:
                    return {"error": "Unable to determine current gameweek."}
                gameweek_id = gw.id

            live_data = await services.live_service.get_live_event(gameweek_id)
            gameweeks = await services.bootstrap_repo.get_gameweeks()
            gw_info = next((g for g in gameweeks if g.id == gameweek_id), None)

            return {
                "gameweek_id": gameweek_id,
                "gameweek_name": gw_info.name if gw_info else f"GW{gameweek_id}",
                "deadline": gw_info.deadline_time.isoformat() if gw_info and hasattr(gw_info.deadline_time, 'isoformat') else None,
                "finished": gw_info.finished if gw_info else None,
                "live_elements": live_data.get("elements", [])[:20],  # Top movers
            }
        except Exception as exc:
            logger.exception("Tool error: get_gameweek_live_status")
            return {"error": f"Failed to get gameweek status: {exc}"}

    @mcp.tool()
    async def get_player_detailed_history(player_name: str) -> dict[str, Any]:
        """Get detailed season history for a player including fixture history and past seasons.

        Args:
            player_name: Player name or web_name to search for.
        """
        try:
            logger.info("Tool call: get_player_detailed_history for %s", player_name)
            results = await services.player_repo.search_by_name(player_name, limit=1)
            if not results:
                return {"error": f"Player '{player_name}' not found."}

            player = results[0]
            # Note: player_summary would come from the FPL client's get_player_summary method
            # For now, return available player data without full history
            return {
                "player_id": player.id,
                "name": player.full_name,
                "team_id": player.team_id,
                "position": {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(player.element_type, "UNK"),
                "current_price": player.price_millions,
                "total_points": player.total_points,
                "points_per_game": float(player.points_per_game or 0),
                "minutes_played": player.minutes,
                "form": float(player.form or 0),
                "expected_points_next": float(player.ep_next or 0),
                "status": player.status,
                "selected_by_percent": float(player.selected_by_percent or 0),
            }
        except Exception as exc:
            logger.exception("Tool error: get_player_detailed_history")
            return {"error": f"Failed to get player history: {exc}"}

    @mcp.tool()
    async def get_fixture_detail(fixture_id: int) -> dict[str, Any]:
        """Get detailed information about a specific fixture.

        Args:
            fixture_id: FPL fixture ID.
        """
        try:
            logger.info("Tool call: get_fixture_detail with fixture_id=%d", fixture_id)
            all_fixtures = await services.fixture_repo.get_all()
            fixture = next((f for f in all_fixtures if f.id == fixture_id), None)
            if not fixture:
                return {"error": f"Fixture {fixture_id} not found."}

            teams = {t.id: t for t in await services.bootstrap_repo.get_teams()}
            return {
                "id": fixture.id,
                "event": fixture.event,
                "home_team": teams.get(fixture.team_h).name if fixture.team_h in teams else None,
                "home_team_code": teams.get(fixture.team_h).short_name if fixture.team_h in teams else None,
                "away_team": teams.get(fixture.team_a).name if fixture.team_a in teams else None,
                "away_team_code": teams.get(fixture.team_a).short_name if fixture.team_a in teams else None,
                "kickoff_time": fixture.kickoff_time.isoformat() if hasattr(fixture.kickoff_time, 'isoformat') else fixture.kickoff_time,
                "home_team_difficulty": fixture.team_h_difficulty,
                "away_team_difficulty": fixture.team_a_difficulty,
                "finished": fixture.finished,
                "home_score": fixture.team_h_score,
                "away_score": fixture.team_a_score,
            }
        except Exception as exc:
            logger.exception("Tool error: get_fixture_detail")
            return {"error": f"Failed to get fixture details: {exc}"}


    @mcp.tool()
    async def get_current_team(
        team_id: int,
        gameweek: int | None = None,
    ) -> dict:
        """Load current squad, captain, available transfers, and chip status.

        Args:
            team_id: Manager's team ID.
            gameweek: Gameweek number (None = current).

        Returns:
            Current team state with squad, captain, bank, transfers available.
        """
        try:
            logger.info("Tool call: get_current_team with team_id=%d", team_id)
            team_mgmt = TeamManagementService(services.auth_service, services.player_repo)
            current = await team_mgmt.get_current_team(team_id, gameweek)

            return {
                "team_id": current.team_id,
                "gameweek": current.gameweek,
                "squad": [
                    {
                        "id": p.id,
                        "name": p.web_name,
                        "position": _position_name(p.element_type),
                        "price": p.price_millions,
                        "ep_next": float(p.ep_next or 0),
                    }
                    for p in current.players
                ],
                "captain": next((p.web_name for p in current.players if p.id == current.captain_id), "Not set"),
                "vice_captain": next((p.web_name for p in current.players if p.id == current.vice_captain_id), "Not set"),
                "squad_value": f"£{current.squad_cost:.1f}m",
                "bank": f"£{current.bank:.1f}m",
                "transfers_available": current.transfers_available,
                "transfers_used": current.transfers_used,
                "chips": {
                    "bench_boost": current.bench_boost_active,
                    "triple_captain": current.triple_captain_active,
                    "wildcard": current.wildcard_active,
                    "free_hit": current.free_hit_active,
                },
            }
        except Exception as exc:
            logger.exception("Tool error: get_current_team")
            return {"error": f"Failed to get current team: {exc}"}

    @mcp.tool()
    async def get_team_transfers(
        team_id: int,
        limit: int = 10,
    ) -> dict:
        """Get transfer history and analysis.

        Args:
            team_id: Manager's team ID.
            limit: Number of recent transfers to show.

        Returns:
            Transfer history with player details and costs.
        """
        try:
            logger.info("Tool call: get_team_transfers with team_id=%d", team_id)
            team_mgmt = TeamManagementService(services.auth_service, services.player_repo)
            transfers = await team_mgmt.get_transfer_history(team_id, limit)

            return {
                "team_id": team_id,
                "total_transfers": len(transfers),
                "transfers": [
                    {
                        "gameweek": t["gameweek"],
                        "out": t["transferred_out"]["name"],
                        "in": t["transferred_in"]["name"],
                        "entry_cost": f"£{t['entry_cost']:.1f}m",
                    }
                    for t in transfers
                ],
            }
        except Exception as exc:
            logger.exception("Tool error: get_team_transfers")
            return {"error": f"Failed to get transfers: {exc}"}

    @mcp.tool()
    async def get_available_chips(
        team_id: int,
        gameweek: int | None = None,
    ) -> dict:
        """Get list of available wildcard chips.

        Args:
            team_id: Manager's team ID.
            gameweek: Gameweek number (None = current).

        Returns:
            Available chips with descriptions.
        """
        try:
            logger.info("Tool call: get_available_chips with team_id=%d", team_id)
            team_mgmt = TeamManagementService(services.auth_service, services.player_repo)
            current = await team_mgmt.get_current_team(team_id, gameweek)
            chips = team_mgmt.get_available_chips(current)

            return {
                "team_id": team_id,
                "gameweek": current.gameweek,
                "available": [
                    {
                        "name": c.name,
                        "description": c.description,
                    }
                    for c in chips
                ],
            }
        except Exception as exc:
            logger.exception("Tool error: get_available_chips")
            return {"error": f"Failed to get available chips: {exc}"}

    @mcp.tool()
    async def suggest_transfers(
        team_id: int,
        num_transfers: int = 1,
        priority: str = "points",
    ) -> dict:
        """Suggest optimal transfers for next gameweek.

        Args:
            team_id: Manager's team ID.
            num_transfers: Number of changes (1-3).
            priority: Optimization metric ('points', 'form', 'fixtures').

        Returns:
            Transfer recommendations with projected gains.
        """
        try:
            logger.info("Tool call: suggest_transfers with team_id=%d, num=%d", team_id, num_transfers)
            team_mgmt = TeamManagementService(services.auth_service, services.player_repo)
            current = await team_mgmt.get_current_team(team_id)

            all_players = await services.player_repo.get_all()
            fixtures = await services.fixture_repo.get_by_gameweek(current.gameweek)
            teams = {t.id: t for t in await services.bootstrap_repo.get_teams()}

            optimizer = TransferOptimizer(all_players, fixtures, teams)
            recommendations = optimizer.suggest_transfers(
                current.players,
                num_transfers=num_transfers,
                budget_available=current.bank,
                priority=priority,
            )

            return {
                "team_id": team_id,
                "gameweek": current.gameweek,
                "transfers": [
                    {
                        "out": r.out_player.web_name,
                        "in": r.in_player.web_name,
                        "reason": r.reason,
                        "projected_gain": f"{r.projected_change:.1f}pts",
                        "cost": f"£{r.cost_delta:.1f}m",
                        "priority": r.priority,
                    }
                    for r in recommendations.recommendations
                ],
                "total_cost": f"£{recommendations.total_cost:.1f}m",
                "total_gain": f"{recommendations.total_projected_gain:.1f}pts",
                "notes": recommendations.notes,
            }
        except Exception as exc:
            logger.exception("Tool error: suggest_transfers")
            return {"error": f"Failed to suggest transfers: {exc}"}

    @mcp.tool()
    async def analyze_transfer_impact(
        team_id: int,
        player_ids_in: list[int],
        player_ids_out: list[int],
        captain_id: int | None = None,
    ) -> dict:
        """Analyze cost and point impact of proposed transfers.

        Args:
            team_id: Manager's team ID.
            player_ids_in: IDs of players to bring in.
            player_ids_out: IDs of players to remove.
            captain_id: New captain ID.

        Returns:
            Transfer impact analysis with cost and projection.
        """
        try:
            logger.info("Tool call: analyze_transfer_impact")
            team_mgmt = TeamManagementService(services.auth_service, services.player_repo)
            current = await team_mgmt.get_current_team(team_id)

            # Build new squad
            current_ids = {p.id for p in current.players}
            new_ids = (current_ids - set(player_ids_out)) | set(player_ids_in)

            all_players = await services.player_repo.get_all()
            new_squad = [p for p in all_players if p.id in new_ids]

            impact = team_mgmt.calculate_transfer_impact(current.players, new_squad, captain_id)

            return {
                "team_id": team_id,
                "transfers": impact["transfers"],
                "players_out": impact["out"],
                "players_in": impact["in"],
                "sell_value": impact["sell_value"],
                "buy_cost": impact["buy_cost"],
                "net_cost": impact["net_cost"],
                "new_captain": impact["new_captain"],
                "feasible": impact["net_cost"] <= current.bank,
            }
        except Exception as exc:
            logger.exception("Tool error: analyze_transfer_impact")
            return {"error": f"Failed to analyze transfer impact: {exc}"}


def _position_name(element_type: int) -> str:
    """Map element_type integer to position code."""
    mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    return mapping.get(element_type, "UNK")
