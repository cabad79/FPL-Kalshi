"""Player domain model for FPL API data."""

from pydantic import BaseModel, Field


class PlayerStatus(str):
    """Enumeration of valid player availability statuses.

    Values:
        a: Available
        i: Injured
        s: Suspended
        n: Unavailable
        d: Dubious (50/50)
    """

    AVAILABLE = "a"
    INJURED = "i"
    SUSPENDED = "s"
    UNAVAILABLE = "n"
    DUBIOUS = "d"


class Player(BaseModel):
    """Represents a single player in Fantasy Premier League.

    Derived from the ``elements`` array in the /bootstrap-static/
    endpoint. Includes all statistics, form, and expected goals metrics.
    """

    id: int
    first_name: str
    second_name: str
    web_name: str
    team_id: int
    element_type: int  # 1=GKP, 2=DEF, 3=MID, 4=FWD
    now_cost: int  # In 0.1m units (e.g., 105 = £10.5m)
    total_points: int
    points_per_game: float
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
    form: str
    value_form: str
    value_season: str
    cost_change_start: int
    cost_change_event: int
    selected_by_percent: str
    transfers_in: int
    transfers_out: int
    transfers_in_event: int
    transfers_out_event: int
    event_points: int
    ep_this: str | None = None
    ep_next: str | None = None
    chance_of_playing_next_round: int | None = None
    chance_of_playing_this_round: int | None = None
    news: str = ""
    status: str = "a"  # a, i, s, n, d
    in_dreamteam: bool = False
    dreamteam_count: int = 0
    expected_goals: str | None = None
    expected_assists: str | None = None
    expected_goal_involvements: str | None = None
    expected_goals_conceded: str | None = None

    @property
    def full_name(self) -> str:
        """Return the player's full name (first + second name)."""
        return f"{self.first_name} {self.second_name}"

    @property
    def price_millions(self) -> float:
        """Return the player's price in millions (e.g., 10.5)."""
        return self.now_cost / 10.0
