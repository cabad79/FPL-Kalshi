"""Player search, comparison, and analysis service."""

from __future__ import annotations

import logging
from typing import Any

from fpl_mcp.domain import Player
from fpl_mcp.repositories import PlayerRepository, FixtureRepository

logger = logging.getLogger(__name__)


class PlayerService:
    """Business logic for player search, comparison, and analytics."""

    def __init__(
        self,
        player_repo: PlayerRepository,
        fixture_repo: FixtureRepository,
    ) -> None:
        self._player_repo = player_repo
        self._fixture_repo = fixture_repo

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def search(
        self,
        query: str,
        position: str | None = None,
        team: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search players by name with optional position and team filters.

        Returns a structured dict ready for MCP tool responses.
        """
        raw_results = await self._player_repo.search_by_name(query, limit=limit * 3)
        filtered = self._apply_filters(raw_results, position=position, team=team)

        players = filtered[:limit]
        return {
            "query": query,
            "filters_applied": {"position": position, "team": team},
            "count": len(players),
            "players": [self._player_to_dict(p) for p in players],
        }

    async def compare(
        self,
        player_names: list[str],
        metrics: list[str] | None = None,
        include_gameweeks: bool = False,
        num_gameweeks: int = 5,
    ) -> dict[str, Any]:
        """Compare two or more players across selected metrics.

        Returns a structured dict with per-metric comparisons and an
        overall best performer summary.
        """
        if len(player_names) < 2:
            raise ValueError("At least two player names are required for comparison.")

        default_metrics = [
            "points",
            "form",
            "points_per_game",
            "price",
            "selected_by_percent",
            "minutes",
            "goals_scored",
            "assists",
            "ict_index",
        ]
        metrics = metrics or default_metrics

        players: list[Player] = []
        for name in player_names:
            results = await self._player_repo.search_by_name(name, limit=1)
            if not results:
                raise ValueError(f"Player '{name}' not found.")
            players.append(results[0])

        metrics_comparison: dict[str, dict[str, Any]] = {}
        best_performers: dict[str, str] = {}

        for metric in metrics:
            comp = self._compare_metric(players, metric)
            metrics_comparison[metric] = comp
            best_performers[metric] = self._best_for_metric(comp)

        summary = self._build_summary(players, metrics_comparison, best_performers)

        result: dict[str, Any] = {
            "players": {p.web_name: self._player_to_dict(p) for p in players},
            "metrics_comparison": metrics_comparison,
            "best_performers": best_performers,
            "summary": summary,
        }

        if include_gameweeks:
            result["gameweek_history"] = await self._fetch_gameweek_history(
                players, num_gameweeks
            )

        return result

    async def analyze(
        self,
        *,
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
        """Analyze the player pool with filters, sorting, and aggregations."""
        all_players = await self._player_repo.get_all()

        filtered = self._apply_criteria(
            all_players,
            position=position,
            team=team,
            min_price=min_price,
            max_price=max_price,
            min_points=min_points,
            min_ownership=min_ownership,
            max_ownership=max_ownership,
            form_threshold=form_threshold,
        )

        sorted_players = self._sort_players(filtered, sort_by, sort_order)
        results = sorted_players[:limit]

        return {
            "total_players": len(all_players),
            "filtered_count": len(filtered),
            "filters": {
                "position": position,
                "team": team,
                "min_price": min_price,
                "max_price": max_price,
                "min_points": min_points,
                "min_ownership": min_ownership,
                "max_ownership": max_ownership,
                "form_threshold": form_threshold,
            },
            "sort": {"by": sort_by, "order": sort_order},
            "limit": limit,
            "players": [self._player_to_dict(p) for p in results],
            "aggregates": self._compute_aggregates(filtered),
        }

    async def get_top_players(
        self,
        metric: str = "points",
        position: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Return top N players for a given metric."""
        all_players = await self._player_repo.get_all()
        filtered = self._apply_filters(all_players, position=position)
        sorted_players = self._sort_players(filtered, metric, "desc")
        top = sorted_players[:limit]

        return {
            "metric": metric,
            "position_filter": position,
            "limit": limit,
            "players": [self._player_to_dict(p) for p in top],
        }

    async def get_price_changes(
        self,
        direction: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return players ordered by latest price change.

        *direction* may be ``"risers"`` or ``"fallers"``.
        """
        all_players = await self._player_repo.get_all()

        if direction == "risers":
            filtered = [p for p in all_players if p.cost_change_event > 0]
        elif direction == "fallers":
            filtered = [p for p in all_players if p.cost_change_event < 0]
        else:
            filtered = [p for p in all_players if p.cost_change_event != 0]

        sorted_players = sorted(
            filtered,
            key=lambda p: abs(p.cost_change_event),
            reverse=True,
        )
        selected = sorted_players[:limit]

        risers = [p for p in selected if p.cost_change_event > 0]
        fallers = [p for p in selected if p.cost_change_event < 0]

        return {
            "direction": direction or "all",
            "limit": limit,
            "total_changes": len(filtered),
            "risers_count": len(risers),
            "fallers_count": len(fallers),
            "risers": [self._player_to_dict(p) for p in risers],
            "fallers": [self._player_to_dict(p) for p in fallers],
        }

    # ------------------------------------------------------------------ #
    # Helpers — filtering
    # ------------------------------------------------------------------ #

    def _apply_filters(
        self,
        players: list[Player],
        position: str | None = None,
        team: str | None = None,
    ) -> list[Player]:
        """Filter a player list by position and/or team name."""
        result = players[:]
        if position:
            pos_norm = position.upper().strip()
            result = [p for p in result if self._position_name(p) == pos_norm]
        if team:
            team_norm = team.lower().strip()
            result = [
                p for p in result
                if team_norm in self._team_name(p).lower()
            ]
        return result

    def _apply_criteria(
        self,
        players: list[Player],
        *,
        position: str | None = None,
        team: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_points: int | None = None,
        min_ownership: float | None = None,
        max_ownership: float | None = None,
        form_threshold: float | None = None,
    ) -> list[Player]:
        """Apply full analysis criteria to a player list."""
        result = players[:]

        if position:
            pos_norm = position.upper().strip()
            result = [p for p in result if self._position_name(p) == pos_norm]

        if team:
            team_norm = team.lower().strip()
            result = [
                p for p in result
                if team_norm in self._team_name(p).lower()
            ]

        if min_price is not None:
            result = [p for p in result if p.price_millions >= min_price]

        if max_price is not None:
            result = [p for p in result if p.price_millions <= max_price]

        if min_points is not None:
            result = [p for p in result if p.total_points >= min_points]

        if min_ownership is not None:
            result = [
                p for p in result
                if float(p.selected_by_percent or 0) >= min_ownership
            ]

        if max_ownership is not None:
            result = [
                p for p in result
                if float(p.selected_by_percent or 0) <= max_ownership
            ]

        if form_threshold is not None:
            result = [
                p for p in result
                if float(p.form or 0) >= form_threshold
            ]

        return result

    # ------------------------------------------------------------------ #
    # Helpers — sorting & metrics
    # ------------------------------------------------------------------ #

    def _sort_players(
        self,
        players: list[Player],
        sort_by: str,
        sort_order: str,
    ) -> list[Player]:
        """Sort players by a metric key."""
        reverse = sort_order.lower() == "desc"

        def _key(p: Player) -> float:
            val = self._get_metric(p, sort_by)
            return float(val) if val is not None else 0.0

        return sorted(players, key=_key, reverse=reverse)

    def _get_metric(self, player: Player, metric: str) -> Any:
        """Extract a metric value from a Player by string key."""
        mapping: dict[str, Any] = {
            "points": player.total_points,
            "form": float(player.form or 0),
            "points_per_game": float(player.points_per_game or 0),
            "price": player.price_millions,
            "value_form": float(player.value_form or 0),
            "value_season": float(player.value_season or 0),
            "selected_by_percent": float(player.selected_by_percent or 0),
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
            "transfers_in": player.transfers_in,
            "transfers_out": player.transfers_out,
            "cost_change_event": player.cost_change_event,
            "cost_change_start": player.cost_change_start,
            "dreamteam_count": player.dreamteam_count,
        }
        return mapping.get(metric, getattr(player, metric, None))

    def _compare_metric(
        self,
        players: list[Player],
        metric: str,
    ) -> dict[str, Any]:
        """Build a per-player comparison dict for a single metric."""
        return {
            p.web_name: self._get_metric(p, metric)
            for p in players
        }

    def _best_for_metric(self, comparison: dict[str, Any]) -> str:
        """Return the player name with the highest numeric value."""
        try:
            return max(
                comparison.items(),
                key=lambda item: float(item[1]) if item[1] is not None else 0.0,
            )[0]
        except (ValueError, TypeError):
            return "N/A"

    # ------------------------------------------------------------------ #
    # Helpers — summary & aggregates
    # ------------------------------------------------------------------ #

    def _build_summary(
        self,
        players: list[Player],
        metrics_comparison: dict[str, dict[str, Any]],
        best_performers: dict[str, str],
    ) -> dict[str, Any]:
        """Build a summary of who won the most metrics."""
        wins: dict[str, int] = {p.web_name: 0 for p in players}
        for winner in best_performers.values():
            if winner in wins:
                wins[winner] += 1

        overall = max(wins.items(), key=lambda x: x[1])[0] if wins else "N/A"
        return {
            "metrics_won": wins,
            "overall_best": overall,
            "total_metrics_compared": len(metrics_comparison),
        }

    def _compute_aggregates(self, players: list[Player]) -> dict[str, Any]:
        """Calculate aggregate statistics for a player list."""
        if not players:
            return {
                "avg_points": 0.0,
                "avg_price": 0.0,
                "avg_form": 0.0,
                "position_distribution": {},
                "team_distribution": {},
            }

        total_points = sum(p.total_points for p in players)
        total_price = sum(p.price_millions for p in players)
        total_form = sum(float(p.form or 0) for p in players)

        pos_dist: dict[str, int] = {}
        team_dist: dict[str, int] = {}
        for p in players:
            pos = self._position_name(p)
            pos_dist[pos] = pos_dist.get(pos, 0) + 1
            team = self._team_name(p)
            team_dist[team] = team_dist.get(team, 0) + 1

        n = len(players)
        return {
            "avg_points": round(total_points / n, 2),
            "avg_price": round(total_price / n, 2),
            "avg_form": round(total_form / n, 2),
            "position_distribution": pos_dist,
            "team_distribution": team_dist,
        }

    async def _fetch_gameweek_history(
        self,
        players: list[Player],
        num_gameweeks: int,
    ) -> dict[str, Any]:
        """Fetch element-summary history for a list of players."""
        history: dict[str, Any] = {}
        for p in players:
            try:
                summary = await self._player_repo.get_summary(p.id)
                history[p.web_name] = {
                    "history": summary.get("history", [])[-num_gameweeks:],
                    "history_past": summary.get("history_past", []),
                }
            except Exception as exc:
                logger.warning("Failed to fetch history for %s: %s", p.web_name, exc)
                history[p.web_name] = {"history": [], "history_past": []}
        return history

    # ------------------------------------------------------------------ #
    # Helpers — serialization
    # ------------------------------------------------------------------ #

    def _player_to_dict(self, player: Player) -> dict[str, Any]:
        """Serialize a Player into a flat dict for tool responses."""
        return {
            "id": player.id,
            "name": player.full_name,
            "web_name": player.web_name,
            "team": getattr(player, "team_name", player.team_id),
            "position": self._position_name(player),
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
            "selected_by_percent": float(player.selected_by_percent or 0),
            "transfers_in": player.transfers_in,
            "transfers_out": player.transfers_out,
            "status": player.status,
            "news": player.news,
            "chance_of_playing_next_round": player.chance_of_playing_next_round,
            "ep_next": player.ep_next,
            "ep_this": player.ep_this,
            "in_dreamteam": player.in_dreamteam,
            "dreamteam_count": player.dreamteam_count,
            "expected_goals": player.expected_goals,
            "expected_assists": player.expected_assists,
        }

    def _position_name(self, player: Player) -> str:
        """Map element_type integer to position code."""
        mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return mapping.get(player.element_type, "UNK")

    def _team_name(self, player: Player) -> str:
        """Safely resolve a player's team name.

        The Player domain model only guarantees ``team_id``.  If the
        repository has enriched the object with ``team_name`` we use it,
        otherwise we fall back to the raw ID so the code never crashes.
        """
        return getattr(player, "team_name", str(player.team_id))
