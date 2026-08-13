"""Live event scoring models for FPL API."""

from pydantic import BaseModel


class LiveStats(BaseModel):
    """Real-time statistics for a single player within a gameweek.

    Mirrors the stats structure returned by /event/{id}/live/ endpoint.
    """

    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: float
    creativity: float
    threat: float
    ict_index: float
    total_points: int
    in_dreamteam: bool = False


class LiveElement(BaseModel):
    """A single player's live data within a gameweek event.

    Wraps the player's stats alongside the FPL explain array
    (breakdown of points by action).
    """

    id: int
    stats: LiveStats
    explain: list[dict] = []


class LiveEvent(BaseModel):
    """Top-level response model for /event/{id}/live/.

    Contains live scoring data for all players in a given gameweek.
    """

    elements: list[LiveElement]


class DreamTeamEntry(BaseModel):
    """A single player entry in the gameweek's dream team."""

    element: int
    points: int
    position: int
