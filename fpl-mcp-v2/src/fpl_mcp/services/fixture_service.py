"""Fixture analysis and gameweek status service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fpl_mcp.domain import Player
from fpl_mcp.repositories import (
    BootstrapRepository,
    FixtureRepository,
    PlayerRepository,
)
from fpl_mcp.utils.difficulty import assess_fixtures, fixture_score

logger = logging.getLogger(__name__)


class FixtureService:
    """Business logic for fixture difficulty, blanks, doubles, and GW status."""

    def __init__(
        self,
        fixture_repo: FixtureRepository,
        player_repo: PlayerRepository,
        bootstrap_repo: BootstrapRepository,
    ) -> None:
        self._fixture_repo = fixture_repo
        self._player_repo = player_repo
        self._bootstrap_repo = bootstrap_repo

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def analyze_player_fixtures(
        self,
        player_id: int,
        num: int = 5,
    ) -> dict[str, Any]:
        """Analyze upcoming fixtures for a specific player.

        Returns difficulty score (0-10), fixture list, home/away counts,
        and a textual assessment.
        """
        player = await self._player_repo.get_by_id(player_id)
        if player is None:
            raise ValueError(f"Player with ID {player_id} not found.")

        fixtures = await self._fixture_repo.get_player_fixtures(player_id, num=num)
        return self._build_analysis(player, fixtures, perspective="player")

    async def analyze_team_fixtures(
        self,
        team_id: int,
        num: int = 5,
    ) -> dict[str, Any]:
        """Analyze upcoming fixtures for a Premier League team."""
        team_fixtures = await self._fixture_repo.get_by_team(team_id)
        upcoming = self._upcoming_fixtures(team_fixtures, num)
        return self._build_team_analysis(team_id, upcoming)

    async def get_blank_gameweeks(self, num: int = 5) -> dict[str, Any]:
        """Return blank gameweeks in the upcoming range."""
        blanks = await self._fixture_repo.get_blank_gameweeks(num_gameweeks=num)
        return {
            "count": len(blanks),
            "blank_gameweeks": blanks,
        }

    async def get_double_gameweeks(self, num: int = 5) -> dict[str, Any]:
        """Return double gameweeks in the upcoming range."""
        doubles = await self._fixture_repo.get_double_gameweeks(num_gameweeks=num)
        return {
            "count": len(doubles),
            "double_gameweeks": doubles,
        }

    async def get_gameweek_status(self) -> dict[str, Any]:
        """Return current gameweek status, deadline, and time remaining."""
        current = await self._bootstrap_repo.get_current_gameweek()
        nxt = await self._bootstrap_repo.get_next_gameweek()

        if current and current.is_current and not current.finished:
            gw = current
            status = "In Progress"
        elif nxt:
            gw = nxt
            status = self._classify_deadline(gw.deadline_time)
        else:
            return {
                "current_gameweek": None,
                "next_gameweek": None,
                "status": "Unknown",
                "deadline": None,
                "time_until_deadline": None,
            }

        now = datetime.now(timezone.utc)
        deadline = gw.deadline_time
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        delta = deadline - now
        hours_until = delta.total_seconds() / 3600

        return {
            "current_gameweek": current.id if current else None,
            "next_gameweek": nxt.id if nxt else None,
            "status": status,
            "deadline": deadline.isoformat(),
            "time_until_deadline": self._format_delta(delta),
            "hours_until_deadline": round(hours_until, 2),
        }

    # ------------------------------------------------------------------ #
    # Helpers — analysis builders
    # ------------------------------------------------------------------ #

    def _build_analysis(
        self,
        player: Player,
        fixtures: list[dict],
        perspective: str,
    ) -> dict[str, Any]:
        """Build a fixture analysis dict for a player or team."""
        if not fixtures:
            return {
                "player_id": player.id,
                "player_name": player.web_name,
                "difficulty_score": 0.0,
                "assessment": "No upcoming fixtures found.",
                "fixtures": [],
                "home_count": 0,
                "away_count": 0,
            }

        # Extract difficulty values from the fixture dicts returned by the repo.
        difficulties = [f.get("difficulty", 3) for f in fixtures]
        score = fixture_score(
            [{"difficulty": d} for d in difficulties], key="difficulty"
        )

        home_count = sum(1 for f in fixtures if f.get("is_home"))
        away_count = len(fixtures) - home_count

        return {
            "player_id": player.id,
            "player_name": player.web_name,
            "team_id": player.team_id,
            "difficulty_score": score,
            "assessment": assess_fixtures(score),
            "fixtures": fixtures,
            "home_count": home_count,
            "away_count": away_count,
            "fixture_count": len(fixtures),
        }

    def _build_team_analysis(
        self,
        team_id: int,
        fixtures: list[dict],
    ) -> dict[str, Any]:
        """Build a fixture analysis dict for a team."""
        if not fixtures:
            return {
                "team_id": team_id,
                "difficulty_score": 0.0,
                "assessment": "No upcoming fixtures found.",
                "fixtures": [],
                "home_count": 0,
                "away_count": 0,
            }

        difficulties = [f.get("difficulty", 3) for f in fixtures]
        score = fixture_score(
            [{"difficulty": d} for d in difficulties], key="difficulty"
        )

        home_count = sum(1 for f in fixtures if f.get("is_home"))
        away_count = len(fixtures) - home_count

        return {
            "team_id": team_id,
            "difficulty_score": score,
            "assessment": assess_fixtures(score),
            "fixtures": fixtures,
            "home_count": home_count,
            "away_count": away_count,
            "fixture_count": len(fixtures),
        }

    def _upcoming_fixtures(
        self,
        fixtures: list[Any],
        num: int,
    ) -> list[dict]:
        """Filter to upcoming fixtures and limit to *num*."""
        now = datetime.now(timezone.utc)

        upcoming: list[dict] = []
        for f in fixtures:
            # Support both Fixture domain objects and raw dicts
            if isinstance(f, dict):
                kickoff = f.get("kickoff_time")
                is_finished = f.get("finished", False)
            else:
                kickoff = f.kickoff_time
                is_finished = f.finished

            if isinstance(kickoff, str):
                kickoff = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
            if kickoff and kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=timezone.utc)

            if not is_finished and kickoff and kickoff >= now:
                upcoming.append(f if isinstance(f, dict) else f.model_dump())

        upcoming.sort(key=lambda x: x.get("kickoff_time", ""))
        return upcoming[:num]

    # ------------------------------------------------------------------ #
    # Helpers — gameweek status
    # ------------------------------------------------------------------ #

    def _classify_deadline(self, deadline: datetime) -> str:
        """Classify how imminent a gameweek deadline is."""
        now = datetime.now(timezone.utc)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        hours = (deadline - now).total_seconds() / 3600
        if hours < 0:
            return "Complete"
        if hours < 6:
            return "Imminent"
        if hours < 48:
            return "Upcoming"
        return "Planned"

    def _format_delta(self, delta: Any) -> str:
        """Format a timedelta into a human-readable string."""
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return "Deadline passed"

        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "0m"
