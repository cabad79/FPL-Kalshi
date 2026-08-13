"""Gameweek domain model for FPL API data."""

from datetime import datetime

from pydantic import BaseModel


class Gameweek(BaseModel):
    """Represents a single Fantasy Premier League gameweek.

    Contains deadline information, scoring data, and flags indicating
    the gameweek's position in the season timeline.
    """

    id: int
    name: str
    deadline_time: datetime
    average_entry_score: int | None = None
    highest_score: int | None = None
    finished: bool
    is_current: bool
    is_next: bool
    is_previous: bool
    data_checked: bool | None = None
    most_selected: int | None = None
    most_transferred_in: int | None = None
    most_captained: int | None = None
    most_vice_captained: int | None = None
    chip_plays: list[dict] | None = None
