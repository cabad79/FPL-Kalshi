"""Position normalization utilities."""

from typing import Optional


_POSITION_MAPPINGS: dict[str, str] = {
    # Standard codes
    "GKP": "GKP",
    "DEF": "DEF",
    "MID": "MID",
    "FWD": "FWD",
    # Goalkeeper aliases
    "goalkeeper": "GKP",
    "goalie": "GKP",
    "keeper": "GKP",
    "gk": "GKP",
    "gkp": "GKP",
    "g": "GKP",
    # Defender aliases
    "defender": "DEF",
    "fullback": "DEF",
    "center-back": "DEF",
    "cb": "DEF",
    "centre-back": "DEF",
    "centre back": "DEF",
    "center back": "DEF",
    "wing-back": "DEF",
    "wing back": "DEF",
    "wb": "DEF",
    "lb": "DEF",
    "rb": "DEF",
    "def": "DEF",
    "df": "DEF",
    "d": "DEF",
    "back": "DEF",
    # Midfielder aliases
    "midfielder": "MID",
    "midfield": "MID",
    "mid": "MID",
    "mf": "MID",
    "m": "MID",
    "winger": "MID",
    "cm": "MID",
    "cam": "MID",
    "cdm": "MID",
    "lm": "MID",
    "rm": "MID",
    "attacking midfielder": "MID",
    # Forward aliases
    "forward": "FWD",
    "striker": "FWD",
    "fwd": "FWD",
    "fw": "FWD",
    "f": "FWD",
    "cf": "FWD",
    "st": "FWD",
    "centre forward": "FWD",
    "center forward": "FWD",
    "wing forward": "FWD",
    "attacker": "FWD",
    "att": "FWD",
    "a": "FWD",
}


def normalize_position(position_term: Optional[str]) -> Optional[str]:
    """Normalize a position term to a standard FPL position code.

    Args:
        position_term: Raw position string (e.g., "goalkeeper", "mid", "ST").

    Returns:
        Standardized position code ("GKP", "DEF", "MID", "FWD") or None.
    """
    if not position_term:
        return None
    normalized = position_term.lower().strip()
    # Exact match first
    if normalized in _POSITION_MAPPINGS:
        return _POSITION_MAPPINGS[normalized]
    # Partial match fallback
    for term, code in _POSITION_MAPPINGS.items():
        if normalized in term.lower() or term.lower() in normalized:
            return code
    return None
