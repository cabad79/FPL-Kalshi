"""Starting lineup probability and transfer risk analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fpl_mcp.domain.player import Player
from fpl_mcp.domain.fixture import Fixture
from fpl_mcp.domain.team import Team

logger = logging.getLogger(__name__)


@dataclass
class LineupProbability:
    """Player's expected starting lineup probability."""

    player_id: int
    player_name: str
    team: str
    position: str
    current_status: str  # "a" (available), "d" (doubt), "i" (injured), "s" (suspended)
    chance_of_playing_next_round: int | None  # 0-100
    minutes_last_gw: int
    game_time_percent: float  # (minutes / 90) over last 5 GWs
    recent_form: float  # average points last 3 GWs
    rotation_risk: str  # "low", "medium", "high"
    expected_lineup_prob: float  # 0-1 probability of starting next GW
    transfer_risk: str  # "low", "medium", "high"
    reasons: list[str]


@dataclass
class FixtureDifficultyAssessment:
    """Detailed fixture difficulty analysis."""

    team: str
    team_id: int
    opponent: str
    opponent_id: int
    is_home: bool
    fpl_difficulty: int  # 1-5 from FPL API
    xg_against_avg: float | None  # Expected Goals Against (from external)
    injury_status: str  # "critical", "concerning", "minor", "clear"
    key_missing_players: list[str]
    expected_score_diff: float  # Positive = team stronger


class LineupAnalyzer:
    """Analyzes lineup probabilities and rotation risk."""

    ROTATION_THRESHOLDS = {
        "low": (70, 100),  # 70%+ playing time
        "medium": (40, 70),  # 40-70%
        "high": (0, 40),  # <40%
    }

    @staticmethod
    def calculate_lineup_probability(
        player: Player,
        minutes_last_5_gws: int,
        recent_form_3gws: float,
        team_context: str = "normal",  # "normal", "mid_rotation", "squad_change"
    ) -> LineupProbability:
        """Calculate probability of player starting next gameweek.

        Args:
            player: Player object with current status
            minutes_last_5_gws: Total minutes played in last 5 gameweeks
            recent_form_3gws: Average points in last 3 gameweeks
            team_context: Team's current situation

        Returns:
            LineupProbability with detailed assessment
        """
        # Game time percentage
        game_time_percent = min((minutes_last_5_gws / (90 * 5)) * 100, 100)

        # Determine rotation risk
        if game_time_percent >= 70:
            rotation_risk = "low"
        elif game_time_percent >= 40:
            rotation_risk = "medium"
        else:
            rotation_risk = "high"

        # Starting lineup probability calculation
        # Base from chance_of_playing_next_round
        base_prob = (player.chance_of_playing_next_round or 75) / 100

        # Adjust for game time percentage
        # High game time (>70%) → confidence boost
        # Low game time (<40%) → rotation risk
        game_time_factor = (game_time_percent / 100) * 0.5 + 0.5
        base_prob *= game_time_factor

        # Adjust for recent form
        # High recent form → likely to stay in lineup
        # Poor form → risk of benching
        if recent_form_3gws >= 5.0:
            form_boost = 1.1
        elif recent_form_3gws >= 3.0:
            form_boost = 1.0
        else:
            form_boost = 0.9

        base_prob *= form_boost

        # Adjust for status
        if player.status == "a":
            status_factor = 1.0
        elif player.status == "d":  # Doubt
            status_factor = 0.6
        elif player.status in ["i", "s"]:  # Injured/Suspended
            status_factor = 0.0
        else:
            status_factor = 0.8

        expected_lineup_prob = min(base_prob * status_factor, 1.0)

        # Transfer risk
        # Recent form poor + low game time = high risk
        if recent_form_3gws < 2.0 and game_time_percent < 40:
            transfer_risk = "high"
        elif recent_form_3gws < 3.0 or game_time_percent < 50:
            transfer_risk = "medium"
        else:
            transfer_risk = "low"

        # Build reasons
        reasons = []
        if player.status != "a":
            reasons.append(f"Status: {player.status}")
        if game_time_percent < 50:
            reasons.append(f"Rotation risk: {game_time_percent:.0f}% game time")
        if recent_form_3gws < 3.0:
            reasons.append(f"Poor form: {recent_form_3gws:.1f} pts/GW")
        if expected_lineup_prob < 0.7:
            reasons.append(f"Starting probability: {expected_lineup_prob:.0%}")

        return LineupProbability(
            player_id=player.id,
            player_name=player.web_name,
            team=f"{player.id}",  # Team ID
            position=LineupAnalyzer._position_name(player.element_type),
            current_status=player.status,
            chance_of_playing_next_round=player.chance_of_playing_next_round,
            minutes_last_gw=0,  # Would be populated from match data
            game_time_percent=game_time_percent,
            recent_form=recent_form_3gws,
            rotation_risk=rotation_risk,
            expected_lineup_prob=expected_lineup_prob,
            transfer_risk=transfer_risk,
            reasons=reasons if reasons else ["All clear"],
        )

    @staticmethod
    def assess_fixture_difficulty(
        fixture: Fixture,
        team: Team,
        opponent: Team,
        team_injuries: list[str] | None = None,
    ) -> FixtureDifficultyAssessment:
        """Assess fixture difficulty with injury context.

        Args:
            fixture: Fixture object
            team: Team playing
            opponent: Opponent team
            team_injuries: List of key injured players

        Returns:
            Detailed fixture assessment
        """
        is_home = fixture.team_h == team.id

        # FPL difficulty (1-5 scale)
        fpl_difficulty = (
            fixture.team_h_difficulty if is_home else fixture.team_a_difficulty
        )

        # Determine injury severity for opponent
        if team_injuries and len(team_injuries) >= 3:
            injury_status = "critical"
        elif team_injuries and len(team_injuries) >= 1:
            injury_status = "concerning"
        else:
            injury_status = "clear"

        # Expected score differential
        # Lower FPL difficulty = stronger position (1 is best, 5 is worst)
        score_diff = (5 - fpl_difficulty) * 0.5  # Positive = favorable

        return FixtureDifficultyAssessment(
            team=team.name,
            team_id=team.id,
            opponent=opponent.name,
            opponent_id=opponent.id,
            is_home=is_home,
            fpl_difficulty=fpl_difficulty,
            xg_against_avg=None,  # Would populate from external source
            injury_status=injury_status,
            key_missing_players=team_injuries or [],
            expected_score_diff=score_diff,
        )

    @staticmethod
    def _position_name(element_type: int) -> str:
        """Map element_type to position."""
        mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return mapping.get(element_type, "UNK")


class SquadCompatibilityAnalyzer:
    """Validates squad against team limits, fixtures, and rotation risk."""

    MAX_PLAYERS_PER_TEAM = 3

    @staticmethod
    def validate_team_limits(squad: list[Player]) -> dict[str, Any]:
        """Check max 3 players per team rule.

        Returns:
            Dict with violations and compliance status
        """
        teams = {}
        violations = []

        for player in squad:
            team_id = player.team_id
            teams[team_id] = teams.get(team_id, 0) + 1

            if teams[team_id] > SquadCompatibilityAnalyzer.MAX_PLAYERS_PER_TEAM:
                violations.append(
                    f"Team {team_id}: {teams[team_id]} players (max 3)"
                )

        return {
            "compliant": len(violations) == 0,
            "team_distribution": teams,
            "violations": violations,
        }

    @staticmethod
    def assess_rotation_risk(
        squad: list[Player],
        lineup_probs: dict[int, LineupProbability],
    ) -> dict[str, Any]:
        """Assess squad rotation risk.

        Args:
            squad: 15-player squad
            lineup_probs: Player ID → LineupProbability mapping

        Returns:
            Risk assessment with flagged players
        """
        high_risk = []
        medium_risk = []

        for player in squad:
            if player.id in lineup_probs:
                prob = lineup_probs[player.id]
                if prob.rotation_risk == "high":
                    high_risk.append(
                        {
                            "player": player.web_name,
                            "prob": prob.expected_lineup_prob,
                            "reason": prob.reasons,
                        }
                    )
                elif prob.rotation_risk == "medium":
                    medium_risk.append(
                        {
                            "player": player.web_name,
                            "prob": prob.expected_lineup_prob,
                        }
                    )

        # Calculate squad starting XI probability
        starting_probs = [
            lineup_probs.get(p.id, LineupProbability(
                p.id, p.web_name, "", "", p.status, 100, 0, 100, 0, "low", 1.0, "low", []
            )).expected_lineup_prob
            for p in squad
        ]
        avg_starting_prob = sum(starting_probs) / len(starting_probs) if starting_probs else 0

        return {
            "high_risk_players": high_risk,
            "medium_risk_players": medium_risk,
            "average_starting_probability": avg_starting_prob,
            "expected_xi_completeness": f"{avg_starting_prob:.0%}",
        }

    @staticmethod
    def assess_fixture_difficulty_spread(
        squad: list[Player],
        fixtures: list[Fixture],
        teams: dict[int, Team],
    ) -> dict[str, Any]:
        """Assess difficulty of fixtures for squad players.

        Returns:
            Difficulty distribution and easy/hard matchups
        """
        difficulties = {}
        easy_fixtures = []  # Difficulty 1-2
        hard_fixtures = []  # Difficulty 4-5

        for player in squad:
            team_id = player.team_id
            for fixture in fixtures:
                if fixture.team_h == team_id:
                    diff = fixture.team_h_difficulty
                    is_home = True
                    break
                elif fixture.team_a == team_id:
                    diff = fixture.team_a_difficulty
                    is_home = False
                    break
            else:
                continue

            difficulties[player.web_name] = diff

            opponent_id = fixture.team_a if is_home else fixture.team_h
            opponent = teams.get(opponent_id)

            if diff <= 2:
                easy_fixtures.append(
                    f"{player.web_name} vs {opponent.name if opponent else 'TBD'} (diff {diff})"
                )
            elif diff >= 4:
                hard_fixtures.append(
                    f"{player.web_name} vs {opponent.name if opponent else 'TBD'} (diff {diff})"
                )

        avg_difficulty = (
            sum(difficulties.values()) / len(difficulties)
            if difficulties
            else 3
        )

        return {
            "average_difficulty": avg_difficulty,
            "easy_fixtures": easy_fixtures,
            "hard_fixtures": hard_fixtures,
            "fixture_distribution": difficulties,
        }
