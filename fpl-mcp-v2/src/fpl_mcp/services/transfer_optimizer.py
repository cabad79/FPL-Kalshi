"""Transfer optimization and change recommendations."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fpl_mcp.domain.fixture import Fixture
from fpl_mcp.domain.player import Player
from fpl_mcp.domain.team import Team
from fpl_mcp.services.squad_validator import SquadValidator

logger = logging.getLogger(__name__)


@dataclass
class TransferRecommendation:
    """A single transfer recommendation."""

    out_player: Player
    in_player: Player
    reason: str
    projected_change: float  # Expected point difference
    cost_delta: float  # Net cost (positive = spending)
    priority: int  # 1=critical, 2=important, 3=nice-to-have


@dataclass
class TransferSet:
    """Complete transfer recommendation set."""

    recommendations: list[TransferRecommendation]
    total_cost: float
    total_projected_gain: float
    use_wildcard: bool
    use_free_hit: bool
    use_triple_captain: bool
    use_bench_boost: bool
    notes: list[str]


class TransferOptimizer:
    """Suggests optimal transfers and wildcard usage."""

    def __init__(
        self,
        all_players: list[Player],
        fixtures: list[Fixture],
        teams: dict[int, Team],
    ):
        self._all_players = [p for p in all_players if p.status == "a"]
        self._fixtures = fixtures
        self._teams = teams

    def suggest_transfers(
        self,
        current_squad: list[Player],
        num_transfers: int = 1,
        budget_available: float = 0.5,
        priority: str = "points",  # "points", "form", "fixtures"
    ) -> TransferSet:
        """Suggest optimal transfers for the coming gameweek.

        Args:
            current_squad: Current 15-player squad
            num_transfers: How many changes to make (1-3)
            budget_available: Available £m for transfers
            priority: Optimization metric

        Returns:
            TransferSet with recommendations and strategy
        """
        current_ids = {p.id for p in current_squad}
        candidates = [p for p in self._all_players if p.id not in current_ids]

        # Score each position for replacement
        position_scores = self._score_positions(current_squad, candidates)

        # Find weakest links
        weakest = sorted(position_scores.items(), key=lambda x: x[1]["score"])[:3]

        recommendations = []
        total_cost = 0.0
        total_gain = 0.0

        for player_to_remove, score_data in weakest[:num_transfers]:
            # Find best replacement in that position
            position = player_to_remove.element_type
            position_candidates = [c for c in candidates if c.element_type == position]

            best_replacement = None
            best_gain = 0.0

            for candidate in position_candidates:
                cost_delta = candidate.price_millions - player_to_remove.price_millions
                if cost_delta <= budget_available:
                    candidate_score = self._score_player(candidate, priority)
                    current_score = self._score_player(player_to_remove, priority)
                    gain = candidate_score - current_score

                    if gain > best_gain:
                        best_gain = gain
                        best_replacement = (candidate, cost_delta, gain)

            if best_replacement:
                candidate, cost, gain = best_replacement
                reason = self._build_transfer_reason(
                    player_to_remove, candidate, priority, gain
                )
                recommendations.append(
                    TransferRecommendation(
                        out_player=player_to_remove,
                        in_player=candidate,
                        reason=reason,
                        projected_change=gain,
                        cost_delta=cost,
                        priority=1 if gain > 2.0 else 2 if gain > 1.0 else 3,
                    )
                )
                total_cost += cost
                total_gain += gain
                budget_available -= cost

        return TransferSet(
            recommendations=sorted(
                recommendations, key=lambda r: r.projected_change, reverse=True
            ),
            total_cost=round(total_cost, 1),
            total_projected_gain=round(total_gain, 1),
            use_wildcard=False,
            use_free_hit=False,
            use_triple_captain=False,
            use_bench_boost=False,
            notes=self._generate_notes(recommendations),
        )

    def suggest_wildcard_squad(
        self,
        current_squad: list[Player],
        fixtures: list[Fixture],
        budget: float = 100.0,
    ) -> list[Player]:
        """Suggest a complete squad rebuild using wildcard.

        Args:
            current_squad: Current squad (will be replaced)
            fixtures: Upcoming fixtures for form boost
            budget: Total budget (usually £100m)

        Returns:
            New 15-player squad suggestion
        """
        # Score all available players
        all_scores = []
        for player in self._all_players:
            score = self._score_player(player, "points")
            all_scores.append((player, score))

        all_scores.sort(key=lambda x: x[1], reverse=True)

        # Greedy selection with constraints
        squad = []
        spent = 0.0
        clubs_used = {}

        for pos_type in [1, 2, 3, 4]:  # GKP, DEF, MID, FWD
            pos_targets = {1: 2, 2: 5, 3: 5, 4: 3}
            pos_count = 0

            for player, score in all_scores:
                if (
                    player.element_type == pos_type
                    and player not in squad
                    and pos_count < pos_targets[pos_type]
                    and spent + player.price_millions <= budget
                    and clubs_used.get(player.team_id, 0) < 3
                ):
                    squad.append(player)
                    spent += player.price_millions
                    clubs_used[player.team_id] = clubs_used.get(player.team_id, 0) + 1
                    pos_count += 1

        # Fill remaining spots with best available
        while len(squad) < 15 and spent < budget:
            for player, score in all_scores:
                if (
                    player not in squad
                    and spent + player.price_millions <= budget
                    and clubs_used.get(player.team_id, 0) < 3
                ):
                    squad.append(player)
                    spent += player.price_millions
                    clubs_used[player.team_id] = clubs_used.get(player.team_id, 0) + 1
                    break

        # Validate
        try:
            SquadValidator.validate_squad(squad)
            return squad
        except Exception as e:
            logger.warning(f"Wildcard squad validation failed: {e}")
            return current_squad

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _score_positions(
        self,
        squad: list[Player],
        candidates: list[Player],
    ) -> dict[Player, dict[str, float]]:
        """Score each squad player by their replaceability."""
        scores = {}
        for player in squad:
            player_score = self._score_player(player, "points")
            position_candidates = [c for c in candidates if c.element_type == player.element_type]

            if position_candidates:
                best_replacement = max(
                    position_candidates, key=lambda p: self._score_player(p, "points")
                )
                replacement_score = self._score_player(best_replacement, "points")
                gap = replacement_score - player_score
            else:
                gap = 0.0

            scores[player] = {
                "score": gap,
                "current_score": player_score,
                "best_replacement": best_replacement if position_candidates else None,
            }

        return scores

    def _score_player(self, player: Player, metric: str) -> float:
        """Score a player on a metric."""
        if metric == "points":
            # Weighted: form + ep_next
            form = float(player.form or 0)
            ep = float(player.ep_next or 0)
            return (form * 0.4) + (ep * 0.6)
        elif metric == "form":
            return float(player.form or 0)
        elif metric == "fixtures":
            # Fixture difficulty bonus
            fixtures = self._get_player_fixtures(player.team_id, 3)
            difficulty_sum = sum(f.team_h_difficulty + f.team_a_difficulty for f in fixtures)
            return 10 - (difficulty_sum / len(fixtures)) if fixtures else 5.0
        else:
            return float(player.ep_next or 0)

    def _get_player_fixtures(self, team_id: int, num: int = 5) -> list[Fixture]:
        """Get next N fixtures for a team."""
        fixtures = []
        for fixture in self._fixtures:
            if fixture.team_h == team_id or fixture.team_a == team_id:
                fixtures.append(fixture)
            if len(fixtures) >= num:
                break
        return fixtures

    def _build_transfer_reason(
        self,
        out_player: Player,
        in_player: Player,
        metric: str,
        projected_gain: float,
    ) -> str:
        """Build explanation for a transfer."""
        parts = [f"Replace {out_player.web_name} with {in_player.web_name}"]

        if metric == "points":
            parts.append(f"projected {projected_gain:.1f}pt gain")
        elif metric == "form":
            parts.append(f"form upgrade (+{projected_gain:.1f})")
        elif metric == "fixtures":
            parts.append(f"better fixture schedule ahead")

        return "; ".join(parts)

    def _generate_notes(self, recommendations: list[TransferRecommendation]) -> list[str]:
        """Generate strategic notes about the transfer plan."""
        notes = []

        if not recommendations:
            notes.append("Squad is optimal; no changes recommended.")
        else:
            total_gain = sum(r.projected_change for r in recommendations)
            notes.append(f"Expected total gain: {total_gain:.1f} points")

            if any(r.priority == 1 for r in recommendations):
                notes.append("High-priority changes identified")

        return notes
