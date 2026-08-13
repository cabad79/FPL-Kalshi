"""Captain suggestion algorithm."""

from __future__ import annotations

import logging
from typing import Any

from fpl_mcp.config import FPLConfig
from fpl_mcp.domain import Player
from fpl_mcp.infrastructure.auth_service import FPLAuthService
from fpl_mcp.repositories import FixtureRepository, PlayerRepository
from fpl_mcp.utils.difficulty import fixture_score

logger = logging.getLogger(__name__)


class CaptainService:
    """Ranks squad players by captain suitability."""

    def __init__(
        self,
        player_repo: PlayerRepository,
        fixture_repo: FixtureRepository,
        auth_service: FPLAuthService,
        config: FPLConfig,
    ) -> None:
        self._player_repo = player_repo
        self._fixture_repo = fixture_repo
        self._auth_service = auth_service
        self._config = config

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def suggest(
        self,
        team_id: int | None = None,
        gameweek_id: int | None = None,
    ) -> dict[str, Any]:
        """Suggest the best captain for the upcoming gameweek.

        If *team_id* is not provided, the service attempts to use the
        authenticated user's default team (resolved via auth_service).

        Returns a structured dict with the top recommendation, ranked
        candidates, and per-component score breakdowns.
        """
        resolved_team_id = await self._resolve_team_id(team_id)
        resolved_gw = await self._resolve_gameweek(gameweek_id)

        team_picks = await self._auth_service.get_team_for_gameweek(
            resolved_team_id, resolved_gw
        )
        picks = team_picks.get("picks", [])
        if not picks:
            raise ValueError(
                f"No picks found for team {resolved_team_id} in GW {resolved_gw}."
            )

        candidates = await self._rank_candidates(picks)
        if not candidates:
            raise ValueError("Unable to rank any candidates for captaincy.")

        top = candidates[0]
        return {
            "gameweek": resolved_gw,
            "team_id": resolved_team_id,
            "recommendation": {
                "player_id": top["player_id"],
                "name": top["name"],
                "captain_score": round(top["captain_score"], 2),
                "reason": top["reason"],
            },
            "candidates": candidates,
            "methodology": self._methodology(),
        }

    # ------------------------------------------------------------------ #
    # Helpers — resolution
    # ------------------------------------------------------------------ #

    async def _resolve_team_id(self, team_id: int | None) -> int:
        """Resolve team_id from argument or auth service."""
        if team_id is not None:
            return team_id

        entry_data = await self._auth_service.get_entry_data(0)
        resolved = entry_data.get("id")
        if not resolved:
            raise ValueError(
                "No team_id provided and unable to resolve default team."
            )
        return int(resolved)

    async def _resolve_gameweek(self, gameweek_id: int | None) -> int:
        """Resolve gameweek from argument or next upcoming GW."""
        if gameweek_id is not None:
            return gameweek_id

        # We rely on the bootstrap repo being accessible through the player_repo
        # or fixture_repo, but the cleaner approach per the architecture is to
        # let the caller provide it.  As a fallback we try the fixture repo
        # which may expose a helper, otherwise raise.
        raise ValueError(
            "gameweek_id is required; automatic GW resolution not yet implemented."
        )

    # ------------------------------------------------------------------ #
    # Helpers — ranking
    # ------------------------------------------------------------------ #

    async def _rank_candidates(
        self,
        picks: list[dict],
    ) -> list[dict[str, Any]]:
        """Score every squad pick and return descending list."""
        candidates: list[dict[str, Any]] = []

        for pick in picks:
            player_id = pick.get("element")
            if player_id is None:
                continue

            player = await self._player_repo.get_by_id(player_id)
            if player is None:
                logger.warning("Pick references unknown player %s", player_id)
                continue

            score_data = await self._score_player(player)
            candidates.append(score_data)

        candidates.sort(key=lambda c: c["captain_score"], reverse=True)
        return candidates

    async def _score_player(self, player: Player) -> dict[str, Any]:
        """Compute captain score for a single player."""
        weights = self._weights()

        # Raw components
        ep_next = self._safe_float(player.ep_next)
        form = self._safe_float(player.form)
        ppg = float(player.points_per_game or 0)

        fixtures = await self._fixture_repo.get_player_fixtures(player.id, num=5)
        f_score = self._calculate_fixture_score(fixtures)

        # Weighted score
        raw_score = (
            ep_next * weights["expected_points"]
            + form * weights["form"]
            + ppg * weights["ppg"]
            + f_score * weights["fixtures"]
        )

        # Availability penalty
        availability = self._availability_multiplier(player)
        final_score = raw_score * availability

        # Build reason string
        reason = self._build_reason(player, final_score, availability)

        return {
            "player_id": player.id,
            "name": player.web_name,
            "position": self._position_name(player),
            "team_id": player.team_id,
            "captain_score": round(final_score, 2),
            "components": {
                "ep_next": round(ep_next, 2),
                "form": round(form, 2),
                "points_per_game": round(ppg, 2),
                "fixture_score": round(f_score, 2),
            },
            "weights": weights,
            "availability_multiplier": round(availability, 2),
            "status": player.status,
            "news": player.news,
            "reason": reason,
        }

    def _calculate_fixture_score(self, fixtures: list[dict]) -> float:
        """Convert upcoming fixtures into a 0-10 difficulty score."""
        if not fixtures:
            return 0.0
        difficulties = [f.get("difficulty", 3) for f in fixtures]
        return fixture_score(
            [{"difficulty": d} for d in difficulties], key="difficulty"
        )

    def _availability_multiplier(self, player: Player) -> float:
        """Penalise players who are not fully available."""
        if player.status == "a":
            return 1.0
        chance = player.chance_of_playing_next_round
        if chance is not None:
            return chance / 100.0
        return 0.0

    def _build_reason(
        self,
        player: Player,
        score: float,
        availability: float,
    ) -> str:
        """Generate a human-readable reason for the recommendation."""
        parts = [f"{player.web_name} scores {round(score, 1)} overall."]

        if availability < 1.0:
            parts.append(
                f"Availability concern: {player.news or 'check injury status'}."
            )
        else:
            parts.append("Fully available.")

        ep = self._safe_float(player.ep_next)
        if ep >= 6.0:
            parts.append(f"High expected points ({round(ep, 1)}).")
        elif ep >= 4.0:
            parts.append(f"Solid expected points ({round(ep, 1)}).")
        else:
            parts.append(f"Lower expected points ({round(ep, 1)}).")

        return " ".join(parts)

    # ------------------------------------------------------------------ #
    # Helpers — configuration & constants
    # ------------------------------------------------------------------ #

    def _weights(self) -> dict[str, float]:
        """Return the current captain algorithm weights."""
        return {
            "expected_points": self._config.captain_weight_expected_points,
            "form": self._config.captain_weight_form,
            "ppg": self._config.captain_weight_ppg,
            "fixtures": self._config.captain_weight_fixtures,
        }

    def _methodology(self) -> dict[str, Any]:
        """Document the scoring methodology for transparency."""
        return {
            "description": (
                "Captain score is a weighted sum of expected points (ep_next), "
                "recent form, points-per-game, and upcoming fixture difficulty. "
                "Players with status != 'a' are penalised by their chance of playing."
            ),
            "weights": self._weights(),
            "fixture_scoring": "(6 - avg_difficulty) * 2, capped 0-10",
            "availability_penalty": "multiplied by chance_of_playing_next_round / 100",
        }

    # ------------------------------------------------------------------ #
    # Helpers — utilities
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_float(value: str | None) -> float:
        """Safely convert a stringy FPL float to Python float."""
        try:
            return float(value or 0)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _position_name(player: Player) -> str:
        """Map element_type integer to position code."""
        mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return mapping.get(player.element_type, "UNK")
