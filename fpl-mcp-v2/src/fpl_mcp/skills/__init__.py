"""MCP Skills for Kalshi football market predictions."""

from __future__ import annotations

from .goal_prediction import (
    calculate_poisson_probabilities,
    estimate_goal_distribution,
    estimate_xg_for_match,
    predict_match_goals,
)
from .match_outcomes import (
    calculate_elo_rating,
    calculate_pythagorean_points,
    estimate_home_advantage,
    predict_match_outcome,
)

__version__ = "0.1.0"

__all__ = [
    "calculate_poisson_probabilities",
    "estimate_goal_distribution",
    "estimate_xg_for_match",
    "predict_match_goals",
    "calculate_elo_rating",
    "calculate_pythagorean_points",
    "estimate_home_advantage",
    "predict_match_outcome",
]
