"""Fixture domain model for FPL API data."""

from datetime import datetime

from pydantic import BaseModel, Field


class Fixture(BaseModel):
    """Represents a single Premier League fixture in the FPL system.

    Includes difficulty ratings for both home and away teams, which are
    used to assess fixture attractiveness (1=easiest, 5=hardest).
    """

    id: int
    event: int | None = None  # Gameweek ID
    finished: bool
    finished_provisional: bool
    kickoff_time: datetime
    team_h: int
    team_a: int
    team_h_score: int | None = None
    team_a_score: int | None = None
    team_h_difficulty: int = Field(..., ge=1, le=5)
    team_a_difficulty: int = Field(..., ge=1, le=5)
    pulse_id: int | None = None
