"""Squad validation against FPL rules."""

from __future__ import annotations

import logging
from typing import Any

from fpl_mcp.domain.player import Player

logger = logging.getLogger(__name__)


class SquadValidationError(ValueError):
    """Raised when a squad violates FPL rules."""


class SquadValidator:
    """Validates squads against all FPL rules for 2026-27."""

    # FPL Rules
    TOTAL_PLAYERS = 15
    TOTAL_BUDGET = 100.0  # £m
    GKP_COUNT = 2
    DEF_COUNT = 5
    MID_COUNT = 5
    FWD_COUNT = 3
    MAX_PLAYERS_PER_CLUB = 3
    XI_SIZE = 11  # 1 GKP + 3/4/5 DEF + 4/3/2 MID + 1/2/3 FWD

    # Position mapping
    POSITION_MAP = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    POSITION_TO_TYPE = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}

    @staticmethod
    def validate_squad(squad: list[Player], xi_indices: list[int] | None = None) -> dict[str, Any]:
        """Validate a complete squad against FPL rules.

        Args:
            squad: List of 15 Player objects (full squad).
            xi_indices: Indices of the 11 players in the starting XI (optional).

        Returns:
            Dict with 'valid': bool and 'errors': list[str].

        Raises:
            SquadValidationError: If squad violates any rule.
        """
        errors = []

        # Rule 1: Total players
        if len(squad) != SquadValidator.TOTAL_PLAYERS:
            errors.append(f"Squad must have {SquadValidator.TOTAL_PLAYERS} players, got {len(squad)}")

        # Rule 2: Budget
        total_price = sum(p.price_millions for p in squad)
        if total_price > SquadValidator.TOTAL_BUDGET:
            errors.append(
                f"Squad budget exceeded: £{total_price:.1f}m > £{SquadValidator.TOTAL_BUDGET:.1f}m"
            )

        # Rule 3: Position counts
        positions = [p.element_type for p in squad]
        gkp_count = positions.count(1)
        def_count = positions.count(2)
        mid_count = positions.count(3)
        fwd_count = positions.count(4)

        if gkp_count != SquadValidator.GKP_COUNT:
            errors.append(f"Need {SquadValidator.GKP_COUNT} GKP, got {gkp_count}")
        if def_count != SquadValidator.DEF_COUNT:
            errors.append(f"Need {SquadValidator.DEF_COUNT} DEF, got {def_count}")
        if mid_count != SquadValidator.MID_COUNT:
            errors.append(f"Need {SquadValidator.MID_COUNT} MID, got {mid_count}")
        if fwd_count != SquadValidator.FWD_COUNT:
            errors.append(f"Need {SquadValidator.FWD_COUNT} FWD, got {fwd_count}")

        # Rule 4: Max players per club
        clubs = {}
        for p in squad:
            clubs[p.team_id] = clubs.get(p.team_id, 0) + 1
            if clubs[p.team_id] > SquadValidator.MAX_PLAYERS_PER_CLUB:
                errors.append(
                    f"Club {p.team_id} has {clubs[p.team_id]} players "
                    f"(max {SquadValidator.MAX_PLAYERS_PER_CLUB})"
                )

        # Rule 5: Player availability
        for i, p in enumerate(squad):
            if p.status != "a":
                errors.append(f"Player {p.web_name} ({p.status}) is not available")

        # Rule 6: XI composition (if provided)
        if xi_indices is not None:
            if len(xi_indices) != SquadValidator.XI_SIZE:
                errors.append(
                    f"XI must have {SquadValidator.XI_SIZE} players, got {len(xi_indices)}"
                )
            else:
                xi_positions = [squad[i].element_type for i in xi_indices]
                xi_gkp = xi_positions.count(1)
                xi_def = xi_positions.count(2)
                xi_mid = xi_positions.count(3)
                xi_fwd = xi_positions.count(4)

                if xi_gkp != 1:
                    errors.append(f"XI needs 1 GKP, got {xi_gkp}")
                if xi_def < 3 or xi_def > 5:
                    errors.append(f"XI needs 3-5 DEF, got {xi_def}")
                if xi_mid < 2 or xi_mid > 5:
                    errors.append(f"XI needs 2-5 MID, got {xi_mid}")
                if xi_fwd < 1 or xi_fwd > 3:
                    errors.append(f"XI needs 1-3 FWD, got {xi_fwd}")

        if errors:
            raise SquadValidationError("; ".join(errors))

        return {"valid": True, "budget_remaining": SquadValidator.TOTAL_BUDGET - total_price}
