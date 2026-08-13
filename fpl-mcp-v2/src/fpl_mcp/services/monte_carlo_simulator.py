"""Monte Carlo simulation of FPL squads for a gameweek."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from fpl_mcp.domain.fixture import Fixture
from fpl_mcp.domain.player import Player
from fpl_mcp.domain.team import Team

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Result of one squad simulation."""

    squad_id: str
    squad_players: list[Player]
    total_score: float
    avg_score: float
    p10_score: float
    p90_score: float
    captain_player: Player | None = None
    captain_points: float = 0.0


class MonteCarloSimulator:
    """Simulate FPL squad performance across multiple gameweeks using Monte Carlo."""

    def __init__(
        self,
        fixtures: list[Fixture],
        teams: dict[int, Team],
        seed: int | None = None,
        special_gameweeks: dict[int, str] | None = None,
    ):
        self._fixtures = fixtures
        self._teams = teams
        self._difficulty_bonus = {1: 1.0, 2: 0.95, 3: 0.85, 4: 0.75, 5: 0.65}
        self._special_gameweeks = special_gameweeks or self._detect_special_gameweeks()
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def simulate_squad(
        self, squad: list[Player], captain_id: int | None = None, iterations: int = 100
    ) -> SimulationResult:
        """Simulate a squad's expected points for the gameweek.

        Args:
            squad: List of 15 Player objects.
            captain_id: ID of the captain (gets 2x points); if None, auto-select.
            iterations: Monte Carlo iterations.

        Returns:
            SimulationResult with avg/p10/p90 scores.
        """
        if captain_id is None:
            # Auto-select captain: highest ep_next
            captain_id = max(squad, key=lambda p: float(p.ep_next or 0)).id

        captain = next((p for p in squad if p.id == captain_id), None)

        scores = []
        for _ in range(iterations):
            gw_score = self._simulate_gameweek(squad, captain_id)
            scores.append(gw_score)

        return SimulationResult(
            squad_id=f"squad_{random.randint(100000, 999999)}",
            squad_players=squad,
            total_score=sum(scores),
            avg_score=np.mean(scores),
            p10_score=np.percentile(scores, 10),
            p90_score=np.percentile(scores, 90),
            captain_player=captain,
            captain_points=float(captain.ep_next or 0) * 2,
        )

    def _simulate_gameweek(self, squad: list[Player], captain_id: int) -> float:
        """Simulate one gameweek for a squad."""
        total = 0.0

        for player in squad:
            # Base expected points
            ep = float(player.ep_next or 0)

            # DGW/BGW adjustment
            team_status = self._special_gameweeks.get(player.team_id, "normal")
            if team_status == "dgw":
                ep *= 1.5  # Double gameweek bonus
            elif team_status == "bgw":
                ep = 0.0  # Blank gameweek

            # Fixture difficulty bonus/penalty (only for normal gameweeks)
            if team_status != "bgw":
                fixture_info = self._get_fixture_info(player.team_id)
                if fixture_info:
                    _, difficulty = fixture_info
                    ep *= self._difficulty_bonus.get(difficulty, 0.85)

            # Form variance
            form = float(player.form or 0)
            form_variance = random.gauss(0, 0.3) * (1 + form / 10)

            # Playing time risk (2% chance of 0 if dubious)
            if player.chance_of_playing_next_round is not None:
                if player.chance_of_playing_next_round < 100:
                    if random.random() > (player.chance_of_playing_next_round / 100):
                        ep = 0

            # Final score
            player_score = max(0, ep + form_variance)

            # Apply captain multiplier
            if player.id == captain_id:
                player_score *= 2

            total += player_score

        return total

    def _detect_special_gameweeks(self) -> dict[int, str]:
        """Detect double gameweeks (DGW) and blank gameweeks (BGW)."""
        gameweek_status = {}
        fixture_count = {}

        for fixture in self._fixtures:
            fixture_count[fixture.team_h] = fixture_count.get(fixture.team_h, 0) + 1
            fixture_count[fixture.team_a] = fixture_count.get(fixture.team_a, 0) + 1

        for team_id, count in fixture_count.items():
            if count == 2:
                gameweek_status[team_id] = "dgw"
            elif count == 0:
                gameweek_status[team_id] = "bgw"
            else:
                gameweek_status[team_id] = "normal"

        return gameweek_status

    def _get_fixture_info(self, team_id: int) -> tuple[str, int] | None:
        """Get fixture difficulty for a team."""
        for fixture in self._fixtures:
            if fixture.team_h == team_id:
                return ("H", fixture.team_h_difficulty)
            elif fixture.team_a == team_id:
                return ("A", fixture.team_a_difficulty)
        return None

    def compare_squads(
        self, squads: list[list[Player]], captain_ids: list[int | None] | None = None, iterations: int = 100
    ) -> list[SimulationResult]:
        """Simulate and rank multiple squads.

        Args:
            squads: List of squads.
            captain_ids: Captain ID for each squad (auto-select if None).
            iterations: Monte Carlo iterations per squad.

        Returns:
            List of SimulationResult sorted by avg score (descending).
        """
        if captain_ids is None:
            captain_ids = [None] * len(squads)

        results = []
        for i, squad in enumerate(squads):
            result = self.simulate_squad(squad, captain_ids[i], iterations)
            result.squad_id = f"squad_{i}"
            results.append(result)

        # Sort by average score descending
        results.sort(key=lambda r: r.avg_score, reverse=True)
        return results
