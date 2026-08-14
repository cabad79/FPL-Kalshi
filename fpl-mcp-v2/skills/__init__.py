"""Skills package for Kalshi Football Markets."""

from skills.goal_prediction import (
    calculate_poisson_probabilities,
    estimate_goal_distribution,
    estimate_xg_for_match,
    predict_match_goals,
)

__all__ = [
    "calculate_poisson_probabilities",
    "predict_match_goals",
    "estimate_goal_distribution",
    "estimate_xg_for_match",
]
