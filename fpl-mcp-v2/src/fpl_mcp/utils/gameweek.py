"""Gameweek helpers with dependency injection (no global singletons)."""

from fpl_mcp.domain.gameweek import Gameweek


async def get_current_gameweek_id(gameweeks: list[Gameweek]) -> int | None:
    """Find the current gameweek ID from a list of gameweeks.

    Args:
        gameweeks: List of gameweek objects.

    Returns:
        The current gameweek ID, or None if not found.
    """
    for gw in gameweeks:
        if gw.is_current:
            return gw.id
    # Fallback: infer from next gameweek
    for gw in gameweeks:
        if gw.is_next:
            gw_id = gw.id
            return max(1, gw_id - 1) if gw_id else None
    return None


async def get_next_gameweek_id(gameweeks: list[Gameweek]) -> int | None:
    """Find the next gameweek ID from a list of gameweeks.

    Args:
        gameweeks: List of gameweek objects.

    Returns:
        The next gameweek ID, or None if not found.
    """
    for gw in gameweeks:
        if gw.is_next:
            return gw.id
    return None
