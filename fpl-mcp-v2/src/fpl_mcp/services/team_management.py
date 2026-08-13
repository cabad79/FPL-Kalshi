"""Current team management and transfer analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fpl_mcp.domain.player import Player
from fpl_mcp.domain.team import Team
from fpl_mcp.infrastructure.auth_service import FPLAuthService
from fpl_mcp.repositories import PlayerRepository

logger = logging.getLogger(__name__)


@dataclass
class WildcardChip:
    """Represents a wildcard chip available to the manager."""

    name: str  # "wildcard", "free_hit", "triple_captain", "bench_boost"
    used_in_gameweek: int | None = None
    remaining: bool = True
    description: str = ""


@dataclass
class CurrentTeam:
    """Current squad state."""

    team_id: int
    gameweek: int
    players: list[Player]
    captain_id: int | None = None
    vice_captain_id: int | None = None
    bench_boost_active: bool = False
    triple_captain_active: bool = False
    wildcard_active: bool = False
    free_hit_active: bool = False
    squad_cost: float = 0.0
    bank: float = 0.0
    transfers_used: int = 0
    transfers_available: int = 1


class TeamManagementService:
    """Manages current team, transfers, and wildcard chips."""

    def __init__(
        self,
        auth_service: FPLAuthService,
        player_repo: PlayerRepository,
    ) -> None:
        self._auth_service = auth_service
        self._player_repo = player_repo

    async def get_current_team(
        self, team_id: int, gameweek: int | None = None
    ) -> CurrentTeam:
        """Get current squad state for a gameweek.

        Args:
            team_id: Manager's team ID
            gameweek: Gameweek number (None = current GW)

        Returns:
            CurrentTeam with all squad details
        """
        if gameweek is None:
            entry = await self._auth_service.get_entry_data(team_id)
            gameweek = entry.get("current_event", 1)

        # Get team picks for gameweek
        picks_data = await self._auth_service.get_team_for_gameweek(team_id, gameweek)
        picks = picks_data.get("picks", [])
        active_chips = picks_data.get("active_chip", [])

        # Resolve players
        players = []
        captain_id = None
        vice_captain_id = None

        for pick in picks:
            player_id = pick.get("element")
            player = await self._player_repo.get_by_id(player_id)
            if player:
                players.append(player)
                if pick.get("is_captain"):
                    captain_id = player_id
                if pick.get("is_vice_captain"):
                    vice_captain_id = player_id

        # Calculate squad cost and bank
        squad_cost = sum(p.price_millions for p in players)
        entry = await self._auth_service.get_entry_data(team_id)
        bank = float(entry.get("bank", 0)) / 10.0  # API returns in tenths of £
        transfers_used = entry.get("transfers_on_gameweek", 0)
        transfers_available = max(1, 1 - transfers_used)

        return CurrentTeam(
            team_id=team_id,
            gameweek=gameweek,
            players=players,
            captain_id=captain_id,
            vice_captain_id=vice_captain_id,
            bench_boost_active="bench_boost" in active_chips,
            triple_captain_active="3xc" in active_chips,
            wildcard_active="wildcard" in active_chips,
            free_hit_active="freehit" in active_chips,
            squad_cost=squad_cost,
            bank=bank,
            transfers_used=transfers_used,
            transfers_available=transfers_available,
        )

    async def get_transfer_history(
        self, team_id: int, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get transfer history for analysis.

        Args:
            team_id: Manager's team ID
            limit: Maximum transfers to return

        Returns:
            List of transfer records with player details
        """
        transfers = await self._auth_service.get_entry_transfers(team_id)
        transfers_with_details = []

        for transfer in transfers[:limit]:
            in_player = await self._player_repo.get_by_id(transfer.get("element_in"))
            out_player = await self._player_repo.get_by_id(transfer.get("element_out"))

            transfers_with_details.append(
                {
                    "gameweek": transfer.get("event"),
                    "transferred_in": {
                        "id": transfer.get("element_in"),
                        "name": in_player.web_name if in_player else "Unknown",
                        "cost": in_player.price_millions if in_player else 0,
                    },
                    "transferred_out": {
                        "id": transfer.get("element_out"),
                        "name": out_player.web_name if out_player else "Unknown",
                        "cost": out_player.price_millions if out_player else 0,
                    },
                    "entry_cost": float(transfer.get("entry_cost", 0)) / 10.0,
                }
            )

        return transfers_with_details

    def get_available_chips(self, current_team: CurrentTeam) -> list[WildcardChip]:
        """Get list of available wildcard chips.

        Args:
            current_team: Current team state

        Returns:
            List of available chips
        """
        chips = [
            WildcardChip(
                name="wildcard",
                remaining=not current_team.wildcard_active,
                description="Unlimited free transfers this gameweek (only 1 per half-season)",
            ),
            WildcardChip(
                name="free_hit",
                remaining=not current_team.free_hit_active,
                description="Unlimited free transfers this gameweek only; reverts next GW",
            ),
            WildcardChip(
                name="triple_captain",
                remaining=not current_team.triple_captain_active,
                description="Captain gets 3x points instead of 2x",
            ),
            WildcardChip(
                name="bench_boost",
                remaining=not current_team.bench_boost_active,
                description="Bench players score full points",
            ),
        ]

        return [c for c in chips if c.remaining]

    def calculate_transfer_impact(
        self,
        current_squad: list[Player],
        new_squad: list[Player],
        captain_id: int | None = None,
    ) -> dict[str, Any]:
        """Calculate cost and impact of proposed transfers.

        Args:
            current_squad: List of current players (15)
            new_squad: List of proposed players (15)
            captain_id: New captain ID

        Returns:
            Dict with transfer details and cost
        """
        current_ids = {p.id for p in current_squad}
        new_ids = {p.id for p in new_squad}

        out_players = [p for p in current_squad if p.id not in new_ids]
        in_players = [p for p in new_squad if p.id not in current_ids]

        # Calculate cost (sell value + cost to buy)
        sell_value = sum(p.price_millions * 0.5 for p in out_players)  # 50% sell value
        buy_cost = sum(p.price_millions for p in in_players)
        net_cost = buy_cost - sell_value

        return {
            "transfers": len(out_players),
            "out": [{"name": p.web_name, "cost": p.price_millions} for p in out_players],
            "in": [{"name": p.web_name, "cost": p.price_millions} for p in in_players],
            "sell_value": round(sell_value, 1),
            "buy_cost": round(buy_cost, 1),
            "net_cost": round(net_cost, 1),
            "new_captain": next(
                (p.web_name for p in new_squad if p.id == captain_id), "Auto-select"
            ),
        }
