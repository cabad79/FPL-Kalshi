"""MCP Skills for Kalshi football market predictions."""

from __future__ import annotations

from .dixon_coles import (
    DixonColesParams,
    fit_and_predict,
    fit_dixon_coles,
    monte_carlo_markets,
    predict_match_outcome_dc,
    score_matrix,
)
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
from .model_validation import BacktestResult, CalibrationBin, backtest_dixon_coles, calibration_check

__version__ = "0.2.0"

__all__ = [
    "calculate_poisson_probabilities",
    "estimate_goal_distribution",
    "estimate_xg_for_match",
    "predict_match_goals",
    "calculate_elo_rating",
    "calculate_pythagorean_points",
    "estimate_home_advantage",
    "predict_match_outcome",
    # Dixon-Coles: validated replacement for predict_match_outcome's heuristic
    # rating conversion (see skills/model_validation.py for the backtest that
    # justifies this). Prefer fit_and_predict for new call sites.
    "DixonColesParams",
    "fit_dixon_coles",
    "predict_match_outcome_dc",
    "score_matrix",
    "fit_and_predict",
    "monte_carlo_markets",
    # Model validation
    "BacktestResult",
    "CalibrationBin",
    "backtest_dixon_coles",
    "calibration_check",
]
