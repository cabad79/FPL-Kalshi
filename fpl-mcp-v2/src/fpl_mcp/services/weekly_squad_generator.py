"""Automated weekly squad generation for each gameweek."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fpl_mcp.domain.fixture import Fixture
from fpl_mcp.domain.player import Player
from fpl_mcp.domain.team import Team

logger = logging.getLogger(__name__)


@dataclass
class WeeklySquadReport:
    """Complete weekly squad generation report."""

    gameweek: int
    generated_date: str
    deadline_date: str
    days_until_deadline: int
    squad: list[Player]
    captain_id: int
    captain_name: str
    expected_points: float
    confidence_range: tuple[float, float]  # (p10, p90)
    changes_from_previous: dict[str, Any]
    transfer_recommendations: list[str]
    fixture_difficulty: float
    ownership_advantage: float
    risks: list[str]
    status: str  # "ready", "needs_verification", "pending_changes"


class WeeklySquadGenerator:
    """Generates optimized squad for upcoming gameweek automatically."""

    GW1_DEADLINE = datetime(2026, 8, 22, 11, 0)  # FPL deadline (11:00 GMT Fri)
    DAYS_BEFORE_DEADLINE = 2  # Generate 2 days before GW

    def __init__(
        self,
        all_players: list[Player],
        fixtures: list[Fixture],
        teams: dict[int, Team],
    ):
        self._all_players = all_players
        self._fixtures = fixtures
        self._teams = teams

    def calculate_deadline_date(self, gameweek: int) -> datetime:
        """Calculate GW deadline (Friday 11:00 GMT).

        FPL deadlines:
        - GW1: Aug 22, 2026 (Friday)
        - GW2: Aug 29, 2026 (Friday)
        - Every subsequent Friday at 11:00 GMT
        """
        gw1_deadline = datetime(2026, 8, 22, 11, 0)
        days_offset = (gameweek - 1) * 7
        gw_deadline = gw1_deadline + timedelta(days=days_offset)
        return gw_deadline

    def calculate_generation_date(self, gameweek: int) -> datetime:
        """Calculate when to auto-generate squad (2 days before deadline)."""
        deadline = self.calculate_deadline_date(gameweek)
        generation_date = deadline - timedelta(days=self.DAYS_BEFORE_DEADLINE)
        return generation_date

    def is_generation_time(self, gameweek: int, current_date: datetime | None = None) -> bool:
        """Check if it's time to generate squad for this GW.

        Returns True if current date is within 48 hours before deadline.
        """
        current = current_date or datetime.now()
        deadline = self.calculate_deadline_date(gameweek)
        generation_start = deadline - timedelta(days=self.DAYS_BEFORE_DEADLINE)

        return generation_start <= current < deadline

    def generate_weekly_report(
        self,
        gameweek: int,
        previous_squad: list[Player] | None = None,
        form_update: dict[int, float] | None = None,
    ) -> WeeklySquadReport:
        """Generate comprehensive weekly squad report.

        Args:
            gameweek: Gameweek number (1-38)
            previous_squad: Squad from previous GW (for comparison)
            form_update: Updated form scores {player_id: form_value}

        Returns:
            Complete report ready for manager review
        """
        deadline = self.calculate_deadline_date(gameweek)
        generation_date = self.calculate_generation_date(gameweek)
        days_left = (deadline - datetime.now()).days

        # Get fixtures for this GW
        gw_fixtures = [f for f in self._fixtures if f.event == gameweek]

        # Generate optimized squad (would use SquadGenerator + MonteCarloSimulator)
        # For now, placeholder
        squad = self._all_players[:15]  # Simplified
        captain = self._get_captain_for_gw(squad, gw_fixtures)

        # Calculate changes from previous
        changes = self._calculate_changes(previous_squad or [], squad)

        # Generate recommendations
        recommendations = self._generate_transfer_recommendations(squad, form_update or {})

        # Assess fixture difficulty
        avg_difficulty = self._calculate_avg_difficulty(squad, gw_fixtures)

        # Calculate ownership advantage
        ownership_avg = sum(float(p.selected_by_percent or 0) for p in squad) / len(squad)

        # Identify risks
        risks = self._identify_gw_risks(squad, gw_fixtures)

        return WeeklySquadReport(
            gameweek=gameweek,
            generated_date=datetime.now().isoformat(),
            deadline_date=deadline.isoformat(),
            days_until_deadline=days_left,
            squad=squad,
            captain_id=captain.id,
            captain_name=captain.web_name,
            expected_points=0.0,  # Would come from MC sim
            confidence_range=(0.0, 0.0),  # Would come from MC sim
            changes_from_previous=changes,
            transfer_recommendations=recommendations,
            fixture_difficulty=avg_difficulty,
            ownership_advantage=ownership_avg,
            risks=risks,
            status=self._determine_status(squad, risks),
        )

    # ======================================================================
    # Helpers
    # ======================================================================

    def _get_captain_for_gw(
        self, squad: list[Player], fixtures: list[Fixture]
    ) -> Player:
        """Select best captain for gameweek."""
        # Score players by: form + ep_next + fixture_difficulty
        best_player = max(
            squad,
            key=lambda p: (
                float(p.form or 0) * 0.4
                + float(p.ep_next or 0) * 0.6
            ),
        )
        return best_player

    def _calculate_changes(
        self, previous_squad: list[Player], new_squad: list[Player]
    ) -> dict[str, Any]:
        """Calculate transfers made since previous GW."""
        prev_ids = {p.id for p in previous_squad}
        new_ids = {p.id for p in new_squad}

        transferred_out = [p for p in previous_squad if p.id not in new_ids]
        transferred_in = [p for p in new_squad if p.id not in prev_ids]

        return {
            "transfers_made": len(transferred_out),
            "out": [p.web_name for p in transferred_out],
            "in": [p.web_name for p in transferred_in],
        }

    def _generate_transfer_recommendations(
        self, squad: list[Player], form_update: dict[int, float]
    ) -> list[str]:
        """Generate transfer recommendations for upcoming GW."""
        recommendations = []

        for player in squad:
            # Check if form has dropped
            new_form = form_update.get(player.id, float(player.form or 0))
            if new_form < 2.0:
                recommendations.append(
                    f"Consider replacing {player.web_name} (form: {new_form:.1f})"
                )

            # Check for injury risk
            if player.chance_of_playing_next_round and player.chance_of_playing_next_round < 75:
                recommendations.append(
                    f"Monitor {player.web_name} (playing time risk: {player.chance_of_playing_next_round}%)"
                )

        return recommendations

    def _calculate_avg_difficulty(
        self, squad: list[Player], fixtures: list[Fixture]
    ) -> float:
        """Calculate average fixture difficulty for squad."""
        difficulties = []
        for player in squad:
            for fixture in fixtures:
                if fixture.team_h == player.team_id:
                    difficulties.append(fixture.team_h_difficulty)
                    break
                elif fixture.team_a == player.team_id:
                    difficulties.append(fixture.team_a_difficulty)
                    break

        return sum(difficulties) / len(difficulties) if difficulties else 3.0

    def _identify_gw_risks(
        self, squad: list[Player], fixtures: list[Fixture]
    ) -> list[str]:
        """Identify risks for this gameweek."""
        risks = []

        # Check for hard fixtures
        hard_fixtures = []
        for player in squad:
            for fixture in fixtures:
                difficulty = None
                if fixture.team_h == player.team_id:
                    difficulty = fixture.team_h_difficulty
                elif fixture.team_a == player.team_id:
                    difficulty = fixture.team_a_difficulty

                if difficulty and difficulty >= 4:
                    hard_fixtures.append(player.web_name)

        if hard_fixtures:
            risks.append(f"Hard fixtures for: {', '.join(hard_fixtures[:3])}")

        # Check for injury risk players
        injured = [p.web_name for p in squad if p.status != "a"]
        if injured:
            risks.append(f"Injury concern: {', '.join(injured)}")

        return risks

    def _determine_status(self, squad: list[Player], risks: list[str]) -> str:
        """Determine squad status."""
        if len(risks) > 3:
            return "needs_verification"
        elif any("Injury" in r for r in risks):
            return "pending_changes"
        else:
            return "ready"


class SquadChangeAutomation:
    """Automates squad changes each gameweek based on analysis."""

    def __init__(self, team_id: int):
        self.team_id = team_id

    def calculate_next_generation_time(self, current_gameweek: int) -> datetime:
        """When to generate squad for next gameweek.

        Generates 2 days before next GW deadline.
        """
        next_gw = current_gameweek + 1
        generator = WeeklySquadGenerator([], [], {})
        return generator.calculate_generation_date(next_gw)

    def get_schedule_for_season(self) -> dict[int, dict[str, datetime]]:
        """Get generation schedule for entire 38-GW season."""
        generator = WeeklySquadGenerator([], [], {})
        schedule = {}

        for gw in range(1, 39):
            deadline = generator.calculate_deadline_date(gw)
            generation = generator.calculate_generation_date(gw)

            schedule[gw] = {
                "generate_date": generation,
                "deadline_date": deadline,
                "days_before": (deadline - generation).days,
            }

        return schedule


# Example usage documentation:
"""
AUTOMATED WEEKLY SQUAD GENERATION

1. Set up recurring task (e.g., cron job) to run every day at 10:00 GMT
2. Check if it's time to generate squad using: generator.is_generation_time(current_gw)
3. If True, generate report: report = generator.generate_weekly_report(current_gw)
4. Present report to manager with recommendations
5. Manager reviews changes and confirms
6. Submit squad before deadline

Example Schedule (GW1):
- Aug 20 (Wed): Auto-generate report (2 days before)
- Aug 20-22: Manager reviews and makes final decisions
- Aug 22 11:00 GMT: DEADLINE - Submit squad

Example Cron Job:
```bash
# Run every day at 10:00 GMT
0 10 * * * /path/to/fpl_squad_generator.py --team-id 4247143 --current-gw $(date +%GW)
```

Integration with MCP:
- Tool: generate_weekly_squad_report(gameweek, form_update)
- Tool: get_gw_deadline(gameweek)
- Tool: get_squad_generation_schedule()
"""
