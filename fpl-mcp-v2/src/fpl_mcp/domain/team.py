"""Team domain model for FPL API data."""

from pydantic import BaseModel, Field


class Team(BaseModel):
    """Represents a Premier League team in the FPL ecosystem.

    Includes overall and positional strength ratings used for fixture
    difficulty calculations.
    """

    id: int
    name: str
    short_name: str
    strength: int = Field(..., ge=1, le=5)
    strength_overall_home: int
    strength_overall_away: int
    strength_attack_home: int
    strength_attack_away: int
    strength_defence_home: int
    strength_defence_away: int
    position: int | None = None  # League position
