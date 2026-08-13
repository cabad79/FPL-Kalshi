"""League analytics: standings, historical performance, composition, fixtures."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from fpl_mcp.config import FPLConfig
from fpl_mcp.domain import Player
from fpl_mcp.infrastructure.auth_service import FPLAuthService
from fpl_mcp.repositories import BootstrapRepository, PlayerRepository
from fpl_mcp.utils.concurrency import gather_limited

logger = logging.getLogger(__name__)


class LeagueService:
    """High-level league analytics divided into small, focused methods."""

    def __init__(
        self,
        auth_service: FPLAuthService,
        player_repo: PlayerRepository,
        bootstrap_repo: BootstrapRepository,
        config: FPLConfig,
    ) -> None:
        self._auth = auth_service
        self._player_repo = player_repo
        self._bootstrap_repo = bootstrap_repo
        self._config = config

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def get_standings(self, league_id: int) -> dict[str, Any]:
        """Fetch and format classic league standings."""
        raw = await self._fetch_league_raw(league_id)
        standings = raw.get("standings", {}).get("results", [])
        limited = standings[: self._config.league_results_limit]

        return {
            "league_id": league_id,
            "league_name": raw.get("league", {}).get("name", "Unknown"),
            "total_teams": len(standings),
            "results_limit": self._config.league_results_limit,
            "standings": [self._format_standing_entry(s) for s in limited],
        }

    async def get_historical_performance(
        self,
        league_id: int,
        start_gw: int | None = None,
        end_gw: int | None = None,
    ) -> dict[str, Any]:
        """Build per-gameweek time series for every team in the league."""
        team_ids = await self._extract_team_ids(league_id)

        histories = await gather_limited(
            [self._fetch_team_history(tid) for tid in team_ids],
            limit=5,
            return_exceptions=True,
        )

        start_gw, end_gw = self._resolve_gw_range(start_gw, end_gw)
        series = self._build_historical_series(histories, team_ids, start_gw, end_gw)

        return {
            "league_id": league_id,
            "gameweek_range": {"start": start_gw, "end": end_gw},
            "team_count": len(team_ids),
            "series": series,
        }

    async def get_team_composition(
        self,
        league_id: int,
        gameweek: int | None = None,
    ) -> dict[str, Any]:
        """Analyse squad picks across the league for a gameweek."""
        resolved_gw = gameweek or await self._infer_next_gameweek()
        team_ids = await self._extract_team_ids(league_id)

        picks_list = await gather_limited(
            [self._fetch_picks(tid, resolved_gw) for tid in team_ids],
            limit=5,
            return_exceptions=True,
        )

        # Pre-load player index for fast sync lookups inside helpers
        player_index = await self._build_player_index()

        all_picks = self._flatten_valid_picks(picks_list)
        ownership = self._calculate_ownership(all_picks, player_index)
        captain_counter = self._count_captains(all_picks, player_index)
        template, differentials = self._split_template_differentials(ownership, team_ids)

        return {
            "league_id": league_id,
            "gameweek": resolved_gw,
            "teams_analysed": len(team_ids),
            "total_picks": len(all_picks),
            "ownership": ownership,
            "captain_picks": captain_counter,
            "template_players": template,
            "differential_players": differentials,
        }

    async def get_fixture_analysis(
        self,
        league_id: int,
        start_gw: int | None = None,
        end_gw: int | None = None,
    ) -> dict[str, Any]:
        """Analyse upcoming fixture difficulty weighted by squad composition."""
        resolved_start, resolved_end = self._resolve_gw_range(start_gw, end_gw)
        team_ids = await self._extract_team_ids(league_id)

        # Get current picks for every team
        current_gw = await self._infer_next_gameweek()
        picks_list = await gather_limited(
            [self._fetch_picks(tid, current_gw) for tid in team_ids],
            limit=5,
            return_exceptions=True,
        )

        player_index = await self._build_player_index()
        all_picks = self._flatten_valid_picks(picks_list)
        pl_team_weights = self._compute_pl_team_weights(all_picks, player_index)

        fixtures = await self._bootstrap_repo.get_gameweeks()
        fixture_analysis = self._analyse_weighted_fixtures(
            fixtures, pl_team_weights, resolved_start, resolved_end
        )

        return {
            "league_id": league_id,
            "gameweek_range": {"start": resolved_start, "end": resolved_end},
            "teams_analysed": len(team_ids),
            "pl_team_weights": pl_team_weights,
            "fixture_analysis": fixture_analysis,
        }

    # ------------------------------------------------------------------ #
    # Helpers — fetching & parsing
    # ------------------------------------------------------------------ #

    async def _fetch_league_raw(self, league_id: int) -> dict[str, Any]:
        """Fetch raw league standings payload."""
        url = f"/leagues-classic/{league_id}/standings/"
        return await self._auth.make_authed_request(url)

    async def _extract_team_ids(self, league_id: int) -> list[int]:
        """Extract entry IDs from league standings."""
        raw = await self._fetch_league_raw(league_id)
        results = raw.get("standings", {}).get("results", [])
        ids = [r["entry"] for r in results if "entry" in r]
        return ids[: self._config.league_results_limit]

    async def _fetch_team_history(self, team_id: int) -> dict[str, Any]:
        """Fetch /entry/{id}/history/ for a single team."""
        url = f"/entry/{team_id}/history/"
        return await self._auth.make_authed_request(url)

    async def _fetch_picks(
        self,
        team_id: int,
        gameweek: int,
    ) -> dict[str, Any] | Exception:
        """Fetch picks for a team in a gameweek."""
        try:
            return await self._auth.get_team_for_gameweek(team_id, gameweek)
        except Exception as exc:
            logger.warning(
                "Failed to fetch picks for team %s GW %s: %s", team_id, gameweek, exc
            )
            return exc

    # ------------------------------------------------------------------ #
    # Helpers — player index (avoids repeated async lookups)
    # ------------------------------------------------------------------ #

    async def _build_player_index(self) -> dict[int, Player]:
        """Build an in-memory ID -> Player map from the repository."""
        all_players = await self._player_repo.get_all()
        return {p.id: p for p in all_players}

    # ------------------------------------------------------------------ #
    # Helpers — gameweek resolution
    # ------------------------------------------------------------------ #

    async def _infer_next_gameweek(self) -> int:
        """Return the ID of the next upcoming gameweek."""
        nxt = await self._bootstrap_repo.get_next_gameweek()
        if nxt:
            return nxt.id
        raise RuntimeError("Unable to determine next gameweek.")

    def _resolve_gw_range(
        self,
        start: int | None,
        end: int | None,
    ) -> tuple[int, int]:
        """Clamp GW range to sensible defaults."""
        s = start if start is not None else 1
        e = end if end is not None else 38
        return min(s, e), max(s, e)

    # ------------------------------------------------------------------ #
    # Helpers — standings formatting
    # ------------------------------------------------------------------ #

    def _format_standing_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Normalise a single standings row."""
        return {
            "rank": entry.get("rank"),
            "entry_id": entry.get("entry"),
            "team_name": entry.get("entry_name"),
            "player_name": entry.get("player_name"),
            "total_points": entry.get("total"),
            "gameweek_points": entry.get("event_total"),
            "rank_last_week": entry.get("last_rank"),
        }

    # ------------------------------------------------------------------ #
    # Helpers — historical series
    # ------------------------------------------------------------------ #

    def _build_historical_series(
        self,
        histories: list[Any],
        team_ids: list[int],
        start_gw: int,
        end_gw: int,
    ) -> dict[str, Any]:
        """Build points / rank / value series per team."""
        series: dict[str, Any] = {
            "points": {},
            "rank": {},
            "value": {},
            "chip_usage": {},
        }

        for tid, hist in zip(team_ids, histories):
            if isinstance(hist, Exception):
                continue

            current = hist.get("current", [])
            name = self._extract_team_name(hist, tid)

            points_gw: list[dict] = []
            rank_gw: list[dict] = []
            value_gw: list[dict] = []
            chips: list[str] = []

            for gw in current:
                gw_id = gw.get("event")
                if gw_id is None or not (start_gw <= gw_id <= end_gw):
                    continue
                points_gw.append({"gameweek": gw_id, "value": gw.get("points", 0)})
                rank_gw.append({"gameweek": gw_id, "value": gw.get("overall_rank")})
                value_gw.append(
                    {
                        "gameweek": gw_id,
                        "value": round((gw.get("value", 0) or 0) / 10.0, 1),
                    }
                )
                if gw.get("chip"):
                    chips.append(gw["chip"])

            series["points"][name] = points_gw
            series["rank"][name] = rank_gw
            series["value"][name] = value_gw
            series["chip_usage"][name] = chips

        return series

    def _extract_team_name(self, history: dict[str, Any], fallback_id: int) -> str:
        """Attempt to extract a human-readable team name from history payload."""
        # FPL /entry/{id}/history/ does not include the name, but the caller
        # may have enriched it.  Fall back to the entry_id.
        return history.get("entry_name") or str(fallback_id)

    # ------------------------------------------------------------------ #
    # Helpers — composition analytics
    # ------------------------------------------------------------------ #

    def _flatten_valid_picks(
        self,
        picks_list: list[Any],
    ) -> list[dict[str, Any]]:
        """Unwrap and validate pick payloads, skipping exceptions."""
        flat: list[dict[str, Any]] = []
        for item in picks_list:
            if isinstance(item, Exception):
                continue
            picks = item.get("picks", []) if isinstance(item, dict) else []
            flat.extend(p for p in picks if isinstance(p, dict))
        return flat

    def _calculate_ownership(
        self,
        all_picks: list[dict[str, Any]],
        player_index: dict[int, Player],
    ) -> dict[str, dict[str, Any]]:
        """Count how many squads own each player."""
        counter: Counter[int] = Counter()
        for p in all_picks:
            element = p.get("element")
            if element is not None:
                counter[element] += 1

        total = max(len(set(p.get("entry") for p in all_picks)), 1)
        ownership: dict[str, dict[str, Any]] = {}

        for player_id, count in counter.most_common():
            player = player_index.get(player_id)
            if player is None:
                continue
            pct = round((count / total) * 100, 1)
            ownership[player.web_name] = {
                "player_id": player_id,
                "owned_by": count,
                "percentage": pct,
                "position": self._position_name(player),
            }

        return ownership

    def _count_captains(
        self,
        all_picks: list[dict[str, Any]],
        player_index: dict[int, Player],
    ) -> dict[str, int]:
        """Tally captain picks across the league."""
        captains: Counter[int] = Counter()
        for p in all_picks:
            if p.get("is_captain"):
                element = p.get("element")
                if element is not None:
                    captains[element] += 1

        result: dict[str, int] = {}
        for player_id, count in captains.most_common():
            player = player_index.get(player_id)
            if player:
                result[player.web_name] = count
            else:
                result[str(player_id)] = count
        return result

    def _split_template_differentials(
        self,
        ownership: dict[str, dict[str, Any]],
        team_ids: list[int],
    ) -> tuple[list[str], list[str]]:
        """Classify players as template (>50 % ownership) or differential (<20 %)."""
        threshold_template = 50.0
        threshold_diff = 20.0

        template = []
        differentials = []
        for name, data in ownership.items():
            pct = data.get("percentage", 0)
            if pct >= threshold_template:
                template.append(name)
            elif pct <= threshold_diff:
                differentials.append(name)

        return template, differentials

    # ------------------------------------------------------------------ #
    # Helpers — fixture weighting
    # ------------------------------------------------------------------ #

    def _compute_pl_team_weights(
        self,
        all_picks: list[dict[str, Any]],
        player_index: dict[int, Player],
    ) -> dict[str, float]:
        """Map each PL team to a weight proportional to squad representation."""
        # Count how many picks belong to each PL team
        team_counts: Counter[int] = Counter()
        for p in all_picks:
            element = p.get("element")
            if element is None:
                continue
            player = player_index.get(element)
            if player:
                team_counts[player.team_id] += 1

        total = sum(team_counts.values()) or 1
        weights: dict[str, float] = {}
        for team_id, count in team_counts.items():
            weights[str(team_id)] = round(count / total, 3)
        return weights

    def _analyse_weighted_fixtures(
        self,
        gameweeks: list[Any],
        pl_team_weights: dict[str, float],
        start_gw: int,
        end_gw: int,
    ) -> list[dict[str, Any]]:
        """Stub for weighted fixture difficulty analysis.

        In a full implementation this would cross-reference upcoming fixtures
        against the weighted PL-team ownership and return a per-gameweek
        difficulty forecast.  For now we return the gameweek list with weights
        attached so the presentation layer can render a basic view.
        """
        analysis: list[dict[str, Any]] = []
        for gw in gameweeks:
            if gw.id < start_gw or gw.id > end_gw:
                continue
            analysis.append(
                {
                    "gameweek": gw.id,
                    "name": gw.name,
                    "pl_team_weights": pl_team_weights,
                }
            )
        return analysis

    # ------------------------------------------------------------------ #
    # Helpers — utilities
    # ------------------------------------------------------------------ #

    @staticmethod
    def _position_name(player: Any) -> str:
        """Map element_type integer to position code."""
        mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return mapping.get(getattr(player, "element_type", None), "UNK")
