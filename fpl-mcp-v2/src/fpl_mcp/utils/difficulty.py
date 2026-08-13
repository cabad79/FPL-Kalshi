"""Fixture difficulty scoring formulas.

These are the de-facto standard formulas used across the FPL ecosystem.
"""

from typing import Any


def fixture_score(fixtures: list[dict[str, Any]], key: str = "difficulty") -> float:
    """Calculate a fixture score from a list of fixtures.

    The formula is: (6 - avg_difficulty) * 2
    Higher is better (easier fixtures).

    Args:
        fixtures: List of fixture dicts, each containing a difficulty key.
        key: The key to read difficulty from. Defaults to "difficulty".

    Returns:
        Fixture score rounded to 1 decimal place. Returns 0.0 for empty fixtures.
    """
    if not fixtures:
        return 0.0
    avg_difficulty = sum(f[key] for f in fixtures) / len(fixtures)
    return round((6 - avg_difficulty) * 2, 1)


def score_from_average(avg_difficulty: float) -> float:
    """Convert an average difficulty to a fixture score.

    Args:
        avg_difficulty: Average difficulty value (typically 1-5).

    Returns:
        Fixture score rounded to 1 decimal place.
    """
    return round((6 - avg_difficulty) * 2, 1)


def assess_fixtures(score: float) -> str:
    """Assess fixture difficulty based on a fixture score.

    Args:
        score: Fixture score from fixture_score().

    Returns:
        Human-readable assessment string.
    """
    if score >= 8:
        return "Excellent fixtures"
    if score >= 6:
        return "Good fixtures"
    if score >= 4:
        return "Average fixtures"
    return "Difficult fixtures"
