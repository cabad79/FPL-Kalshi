"""Bootstrap static data models for FPL API."""

from pydantic import BaseModel

from .fixture import Fixture
from .gameweek import Gameweek
from .player import Player
from .team import Team


class GameSettings(BaseModel):
    """FPL game rules configuration."""

    squad_squadplay: int
    squad_squadsize: int
    squad_team_limit: int
    squad_total_spend: int
    transfers_cap: int
    transfers_sell_on_fee: float


class ElementType(BaseModel):
    """Player position type definition.

    Maps to: 1=GKP, 2=DEF, 3=MID, 4=FWD.
    """

    id: int
    plural_name: str
    plural_name_short: str
    singular_name: str
    singular_name_short: str
    squad_select: int
    squad_min_play: int
    squad_max_play: int


class BootstrapStatic(BaseModel):
    """Root model for the /bootstrap-static/ endpoint response.

    Contains all static data for a given FPL season: gameweeks, teams,
    players, game settings, and element types.
    """

    events: list[Gameweek]
    game_settings: GameSettings
    teams: list[Team]
    total_players: int
    elements: list[Player]
    element_types: list[ElementType]
