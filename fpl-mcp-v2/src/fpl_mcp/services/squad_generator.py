"""Squad generation with constraint satisfaction."""

from __future__ import annotations

import logging
import random
from typing import Any

from fpl_mcp.domain.player import Player
from fpl_mcp.services.squad_validator import SquadValidator

logger = logging.getLogger(__name__)


class SquadGenerator:
    """Generate valid FPL squads using constraint satisfaction."""

    def __init__(
        self,
        all_players: list[Player],
        seed: int | None = None,
        contrarian_mode: bool = False,
        special_gameweeks: dict[int, str] | None = None,
    ):
        self._all_players = [p for p in all_players if p.status == "a"]
        self._contrarian_mode = contrarian_mode
        self._special_gameweeks = special_gameweeks or {}
        self._players_by_position = self._organize_by_position()
        if seed is not None:
            random.seed(seed)

    def _organize_by_position(self) -> dict[int, list[Player]]:
        """Organize players by position (element_type)."""
        by_pos = {1: [], 2: [], 3: [], 4: []}
        for p in self._all_players:
            by_pos[p.element_type].append(p)

        # Sort each position by expected points (descending)
        for pos in by_pos:
            by_pos[pos].sort(
                key=lambda p: self._score_player_for_sort(p),
                reverse=True
            )

        return by_pos

    def _score_player_for_sort(self, player: Player) -> float:
        """Score player for squad generation considering all factors."""
        ep = float(player.ep_next or 0)

        # DGW bonus
        team_status = self._special_gameweeks.get(player.team_id, "normal")
        if team_status == "dgw":
            ep *= 1.5
        elif team_status == "bgw":
            ep *= 0.0

        # Contrarian ownership fading
        if self._contrarian_mode:
            ownership = float(player.selected_by_percent or 0)
            ownership_factor = 1.0 - ((ownership / 100) * 0.3)
            ep *= max(ownership_factor, 0.5)

        return ep

    def generate_squad(self, strategy: str = "balanced") -> list[Player]:
        """Generate a single valid squad.

        Args:
            strategy: 'high_value' (premium players), 'balanced', or 'budget' (enablers).

        Returns:
            List of 15 valid Player objects.
        """
        if strategy == "high_value":
            return self._generate_premium_squad()
        elif strategy == "budget":
            return self._generate_budget_squad()
        else:
            return self._generate_balanced_squad()

    def _generate_premium_squad(self) -> list[Player]:
        """Generate squad with premium players (top 3-4 stars)."""
        squad = []
        budget = 100.0
        clubs_used = {}

        # Pick top GKP
        for gkp in self._players_by_position[1][:3]:
            if self._can_add(gkp, squad, clubs_used, budget):
                squad.append(gkp)
                budget -= gkp.price_millions
                clubs_used[gkp.team_id] = clubs_used.get(gkp.team_id, 0) + 1
                break

        # Pick top 5 DEF
        for def_p in self._players_by_position[2][:15]:
            if len([p for p in squad if p.element_type == 2]) >= 5:
                break
            if self._can_add(def_p, squad, clubs_used, budget):
                squad.append(def_p)
                budget -= def_p.price_millions
                clubs_used[def_p.team_id] = clubs_used.get(def_p.team_id, 0) + 1

        # Pick top 5 MID (take top 1-2, rest from middle tier for balance)
        mids_selected = 0
        for mid in self._players_by_position[3]:
            if mids_selected >= 5:
                break
            if self._can_add(mid, squad, clubs_used, budget):
                squad.append(mid)
                budget -= mid.price_millions
                clubs_used[mid.team_id] = clubs_used.get(mid.team_id, 0) + 1
                mids_selected += 1
            if mids_selected >= 2 and mid.price_millions > 8.0:  # Skip pricey ones after top 2
                continue

        # Pick top 3 FWD
        for fwd in self._players_by_position[4][:10]:
            if len([p for p in squad if p.element_type == 4]) >= 3:
                break
            if self._can_add(fwd, squad, clubs_used, budget):
                squad.append(fwd)
                budget -= fwd.price_millions
                clubs_used[fwd.team_id] = clubs_used.get(fwd.team_id, 0) + 1

        # Fill remaining with budget players
        return self._fill_remaining(squad, budget, clubs_used)

    def _generate_budget_squad(self) -> list[Player]:
        """Generate squad with budget enablers (max 2-3 premiums)."""
        squad = []
        budget = 100.0
        clubs_used = {}

        # Pick cheapest GKP
        for gkp in reversed(self._players_by_position[1]):
            if self._can_add(gkp, squad, clubs_used, budget):
                squad.append(gkp)
                budget -= gkp.price_millions
                clubs_used[gkp.team_id] = clubs_used.get(gkp.team_id, 0) + 1
                break

        # Pick budget DEF
        for def_p in reversed(self._players_by_position[2]):
            if len([p for p in squad if p.element_type == 2]) >= 5:
                break
            if self._can_add(def_p, squad, clubs_used, budget):
                squad.append(def_p)
                budget -= def_p.price_millions
                clubs_used[def_p.team_id] = clubs_used.get(def_p.team_id, 0) + 1

        # Pick some budget MID, some quality
        for mid in self._players_by_position[3]:
            if len([p for p in squad if p.element_type == 3]) >= 5:
                break
            # Alternate: pick budget, pick quality
            if len([p for p in squad if p.element_type == 3]) < 2:
                # Quality MID
                if mid.price_millions >= 7.0 and self._can_add(mid, squad, clubs_used, budget):
                    squad.append(mid)
                    budget -= mid.price_millions
                    clubs_used[mid.team_id] = clubs_used.get(mid.team_id, 0) + 1
            else:
                # Budget MID
                if mid.price_millions <= 5.5 and self._can_add(mid, squad, clubs_used, budget):
                    squad.append(mid)
                    budget -= mid.price_millions
                    clubs_used[mid.team_id] = clubs_used.get(mid.team_id, 0) + 1

        # Pick budget FWD
        for fwd in reversed(self._players_by_position[4]):
            if len([p for p in squad if p.element_type == 4]) >= 3:
                break
            if self._can_add(fwd, squad, clubs_used, budget):
                squad.append(fwd)
                budget -= fwd.price_millions
                clubs_used[fwd.team_id] = clubs_used.get(fwd.team_id, 0) + 1

        return self._fill_remaining(squad, budget, clubs_used)

    def _generate_balanced_squad(self) -> list[Player]:
        """Generate balanced squad."""
        squad = []
        budget = 100.0
        clubs_used = {}

        # GKP: pick from top 5
        gkp_choice = random.choice(self._players_by_position[1][:5])
        squad.append(gkp_choice)
        budget -= gkp_choice.price_millions
        clubs_used[gkp_choice.team_id] = 1

        # DEF: pick 5 from top 20
        for def_p in random.sample(self._players_by_position[2][:20], min(5, len(self._players_by_position[2]))):
            if self._can_add(def_p, squad, clubs_used, budget):
                squad.append(def_p)
                budget -= def_p.price_millions
                clubs_used[def_p.team_id] = clubs_used.get(def_p.team_id, 0) + 1

        # MID: pick 5 from top 25
        for mid in random.sample(self._players_by_position[3][:25], min(5, len(self._players_by_position[3]))):
            if self._can_add(mid, squad, clubs_used, budget):
                squad.append(mid)
                budget -= mid.price_millions
                clubs_used[mid.team_id] = clubs_used.get(mid.team_id, 0) + 1

        # FWD: pick 3 from top 12
        for fwd in random.sample(self._players_by_position[4][:12], min(3, len(self._players_by_position[4]))):
            if self._can_add(fwd, squad, clubs_used, budget):
                squad.append(fwd)
                budget -= fwd.price_millions
                clubs_used[fwd.team_id] = clubs_used.get(fwd.team_id, 0) + 1

        return self._fill_remaining(squad, budget, clubs_used)

    def _can_add(
        self, player: Player, current_squad: list[Player], clubs_used: dict, budget: float
    ) -> bool:
        """Check if a player can be added to the squad."""
        if player.price_millions > budget:
            return False
        if player in current_squad:
            return False
        if clubs_used.get(player.team_id, 0) >= 3:
            return False
        pos_count = len([p for p in current_squad if p.element_type == player.element_type])
        max_for_pos = {1: 2, 2: 5, 3: 5, 4: 3}[player.element_type]
        if pos_count >= max_for_pos:
            return False
        return True

    def _fill_remaining(
        self, partial_squad: list[Player], budget: float, clubs_used: dict
    ) -> list[Player]:
        """Fill remaining spots in the squad greedily."""
        squad = partial_squad[:]

        while len(squad) < 15:
            # Find the best available player that fits
            best_player = None
            for player in self._all_players:
                if player not in squad and self._can_add(player, squad, clubs_used, budget):
                    if best_player is None or player.ep_next > best_player.ep_next:
                        best_player = player

            if best_player is None:
                break

            squad.append(best_player)
            budget -= best_player.price_millions
            clubs_used[best_player.team_id] = clubs_used.get(best_player.team_id, 0) + 1

        if len(squad) != 15:
            logger.warning(f"Could only generate {len(squad)}/15 player squad")

        return squad

    def generate_multiple_squads(self, count: int = 1000) -> list[list[Player]]:
        """Generate multiple diverse squads.

        Args:
            count: Number of squads to generate.

        Returns:
            List of valid squads.
        """
        squads = []
        strategies = ["high_value", "balanced", "budget"]

        for i in range(count):
            strategy = strategies[i % len(strategies)]
            try:
                squad = self.generate_squad(strategy=strategy)
                SquadValidator.validate_squad(squad)
                squads.append(squad)
            except Exception as e:
                logger.warning(f"Failed to generate squad {i}: {e}")

        return squads
