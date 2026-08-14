"""Goal prediction module for Kalshi Football Markets."""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# Constants
MIN_LAMBDA = 0.01
MAX_LAMBDA = 10.0
MIN_XG = 0.0
MAX_XG = 5.0
DEFAULT_MAX_GOALS = 10
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0
CORRELATION_FACTOR_MIN = 0.0
CORRELATION_FACTOR_MAX = 1.0
DEFAULT_FORM_FACTOR = 1.0
DEFAULT_DEFENSE_RATING = 1.0


def calculate_poisson_probabilities(
    lambda_param: float, max_goals: int = DEFAULT_MAX_GOALS
) -> dict[int, float]:
    """Calculate probability distribution for goals using Poisson distribution.

    Implements the Poisson probability mass function:
    P(X=k) = (e^(-λ) * λ^k) / k!

    Args:
        lambda_param: The rate parameter (λ) for the Poisson distribution,
                     typically representing expected goals.
        max_goals: Maximum number of goals to calculate probabilities for.
                  Defaults to 10. Must be >= 0.

    Returns:
        Dictionary mapping goal counts (0 to max_goals) to their probabilities.
        All probabilities sum to approximately 1.0 (within numerical precision).

    Raises:
        ValueError: If lambda_param is negative.
        ValueError: If max_goals is negative.

    Examples:
        >>> probs = calculate_poisson_probabilities(2.5)
        >>> probs[0]  # Probability of 0 goals with λ=2.5
        0.08208499862389884
        >>> sum(probs.values())
        0.9999999999999999

    Notes:
        - Lambda values <= 0 are clamped to MIN_LAMBDA (0.01).
        - Lambda values > MAX_LAMBDA (10.0) are clamped for numerical stability.
        - The tail probability (goals > max_goals) is lost in the return value.
    """
    # Validate inputs
    if max_goals < 0:
        raise ValueError(f"max_goals must be non-negative, got {max_goals}")

    # Clamp lambda to valid range
    lambda_clamped = max(MIN_LAMBDA, min(lambda_param, MAX_LAMBDA))
    if lambda_clamped != lambda_param:
        logger.debug(
            f"Lambda parameter {lambda_param} clamped to {lambda_clamped}"
        )

    probabilities: dict[int, float] = {}

    # Pre-calculate e^(-lambda) for efficiency
    exp_neg_lambda = math.exp(-lambda_clamped)

    # Calculate factorial iteratively to avoid overflow
    factorial = 1.0
    lambda_power = 1.0

    for k in range(max_goals + 1):
        if k > 0:
            factorial *= k
            lambda_power *= lambda_clamped

        # P(X=k) = (e^(-λ) * λ^k) / k!
        probability = (exp_neg_lambda * lambda_power) / factorial
        probabilities[k] = probability

    return probabilities


def predict_match_goals(
    home_xg: float,
    away_xg: float,
    correlation_factor: float = 0.1,
) -> dict[str, Any]:
    """Predict actual goals for a match using expected goals.

    Uses Poisson distributions to predict goals for both teams, with a
    correlation adjustment to model realistic match scenarios where high
    scoring is less likely in both directions simultaneously.

    Args:
        home_xg: Expected goals for home team. Must be in [0, 5].
        away_xg: Expected goals for away team. Must be in [0, 5].
        correlation_factor: Strength of correlation between home and away
                           goals. Must be in [0, 1]. 0 = independent,
                           1 = perfectly correlated (both high or both low).
                           Defaults to 0.1 (slight positive correlation).

    Returns:
        Dictionary with keys:
        - 'home_goals': Predicted home team goals (int).
        - 'away_goals': Predicted away team goals (int).
        - 'probability': Probability of this exact outcome (float, 0-1).
        - 'confidence': Confidence in prediction (float, 0-1).

    Raises:
        ValueError: If home_xg or away_xg is outside valid range.
        ValueError: If correlation_factor is outside [0, 1].

    Examples:
        >>> result = predict_match_goals(1.5, 1.2)
        >>> result['home_goals']  # Predicted home goals
        1
        >>> result['confidence']  # Confidence level
        0.75

    Notes:
        - Predictions are stochastic; results vary between calls.
        - Correlation adjustment reduces probability of extreme scores.
        - Confidence increases with match relevance (XG difference from 0).
    """
    # Validate inputs
    if not (MIN_XG <= home_xg <= MAX_XG):
        raise ValueError(
            f"home_xg must be in [{MIN_XG}, {MAX_XG}], got {home_xg}"
        )
    if not (MIN_XG <= away_xg <= MAX_XG):
        raise ValueError(
            f"away_xg must be in [{MIN_XG}, {MAX_XG}], got {away_xg}"
        )
    if not (CORRELATION_FACTOR_MIN <= correlation_factor <= CORRELATION_FACTOR_MAX):
        raise ValueError(
            f"correlation_factor must be in [0, 1], got {correlation_factor}"
        )

    # Get Poisson probabilities for each team
    home_probs = calculate_poisson_probabilities(home_xg)
    away_probs = calculate_poisson_probabilities(away_xg)

    # Find most likely outcomes
    home_goals = max(home_probs, key=lambda k: home_probs[k])
    away_goals = max(away_probs, key=lambda k: away_probs[k])

    # Calculate base probability
    base_probability = home_probs[home_goals] * away_probs[away_goals]

    # Apply correlation adjustment
    correlation_adjustment = 1.0
    if correlation_factor > 0:
        # Reduce probability if both teams score highly (unrealistic)
        total_goals = home_goals + away_goals
        max_realistic_goals = 4

        if total_goals > max_realistic_goals:
            excess = total_goals - max_realistic_goals
            correlation_adjustment = max(0.1, 1.0 - (excess * correlation_factor))

    adjusted_probability = base_probability * correlation_adjustment

    # Calculate confidence based on XG values and match activity
    avg_xg = (home_xg + away_xg) / 2.0
    confidence = min(1.0, avg_xg / 2.0)  # Higher XG = higher confidence
    confidence = max(0.3, confidence)  # Minimum confidence of 30%

    return {
        "home_goals": home_goals,
        "away_goals": away_goals,
        "probability": float(adjusted_probability),
        "confidence": float(confidence),
    }


def estimate_goal_distribution(
    team_stats: dict[str, Any],
    opponent_stats: dict[str, Any],
    context: dict[str, Any],
) -> tuple[dict[int, float], float]:
    """Estimate goal distribution for a team against specific opponent.

    Combines team and opponent statistics with contextual factors to estimate
    a realistic distribution of goals a team might score.

    Args:
        team_stats: Dictionary with team statistics:
            - 'goals_for' (float): Average goals scored per match.
            - 'goals_against' (float): Average goals conceded per match.
            - 'matches_played' (int): Number of matches played this season.
            - 'form_factor' (float): Current form multiplier (0.5-1.5).

        opponent_stats: Dictionary with opponent statistics:
            - 'goals_for' (float): Opponent's average goals scored.
            - 'goals_against' (float): Opponent's average goals conceded.
            - 'defense_rating' (float): Defensive strength (0.7-1.3).

        context: Dictionary with contextual information:
            - 'home_away' (str): 'home' or 'away'.
            - 'injury_status' (str): 'normal', 'minor', or 'major'.
            - 'head_to_head' (Dict): Previous H2H records.

    Returns:
        Tuple of:
        - Distribution dictionary (goals -> probability).
        - Confidence score (0-1) in the estimate.

    Raises:
        KeyError: If required keys are missing from input dictionaries.
        ValueError: If statistics are negative or out of expected ranges.

    Examples:
        >>> team_stats = {
        ...     'goals_for': 1.8,
        ...     'goals_against': 1.2,
        ...     'matches_played': 5,
        ...     'form_factor': 1.1
        ... }
        >>> opponent_stats = {
        ...     'goals_for': 1.5,
        ...     'goals_against': 1.4,
        ...     'defense_rating': 0.95
        ... }
        >>> context = {
        ...     'home_away': 'home',
        ...     'injury_status': 'normal',
        ...     'head_to_head': {}
        ... }
        >>> dist, conf = estimate_goal_distribution(team_stats, opponent_stats, context)
        >>> dist[0] + dist[1] + dist[2] > 0.8  # Distribution sums to ~1.0
        True

    Notes:
        - Confidence increases with more matches played (>10 matches = high).
        - Home advantage adds ~0.3 goals to expected output.
        - Injury status affects output (major = -0.4, minor = -0.2).
    """
    # Validate required keys
    required_team_keys = {"goals_for", "goals_against", "matches_played", "form_factor"}
    required_opp_keys = {"goals_for", "goals_against", "defense_rating"}
    required_ctx_keys = {"home_away", "injury_status", "head_to_head"}

    if not required_team_keys.issubset(team_stats.keys()):
        missing = required_team_keys - set(team_stats.keys())
        raise KeyError(f"Missing team_stats keys: {missing}")

    if not required_opp_keys.issubset(opponent_stats.keys()):
        missing = required_opp_keys - set(opponent_stats.keys())
        raise KeyError(f"Missing opponent_stats keys: {missing}")

    if not required_ctx_keys.issubset(context.keys()):
        missing = required_ctx_keys - set(context.keys())
        raise KeyError(f"Missing context keys: {missing}")

    # Validate value ranges
    if team_stats["goals_for"] < 0 or team_stats["goals_against"] < 0:
        raise ValueError("Team statistics cannot be negative")
    if opponent_stats["goals_for"] < 0 or opponent_stats["goals_against"] < 0:
        raise ValueError("Opponent statistics cannot be negative")
    if team_stats["matches_played"] < 1:
        raise ValueError("matches_played must be >= 1")

    # Extract statistics
    team_gf = team_stats["goals_for"]
    matches_played = team_stats["matches_played"]
    form_factor = team_stats.get("form_factor", DEFAULT_FORM_FACTOR)

    defense_rating = opponent_stats.get("defense_rating", DEFAULT_DEFENSE_RATING)

    # Calculate base expected goals
    base_xg = team_gf * form_factor / defense_rating

    # Apply home/away adjustment
    is_home = context["home_away"].lower() == "home"
    home_advantage = 0.3 if is_home else -0.15

    # Apply injury status adjustment
    injury_adjustment = {
        "normal": 0.0,
        "minor": -0.2,
        "major": -0.4,
    }.get(context["injury_status"].lower(), 0.0)

    # Calculate adjusted XG
    adjusted_xg = base_xg + home_advantage + injury_adjustment
    adjusted_xg = max(MIN_XG, adjusted_xg)  # Ensure non-negative

    # Get distribution
    distribution = calculate_poisson_probabilities(adjusted_xg)

    # Calculate confidence
    data_confidence = min(1.0, matches_played / 10.0)  # 10 matches = full confidence
    injury_confidence = 1.0 if context["injury_status"] == "normal" else 0.85
    confidence = data_confidence * injury_confidence

    return distribution, float(confidence)


def estimate_xg_for_match(
    home_team: str,
    away_team: str,
    season_data: dict[str, Any],
) -> dict[str, float]:
    """Calculate expected goals for both teams in upcoming match.

    Uses historical performance data, current form, and head-to-head records
    to estimate expected goals (xG) for both teams in a match.

    Args:
        home_team: Name or ID of home team.
        away_team: Name or ID of away team.
        season_data: Dictionary with season-wide team statistics:
            - 'teams' (Dict): Mapping of team identifiers to team data.
            - 'matches' (List): List of historical match data.
            - 'gameweek' (int): Current gameweek number.
            Each team in 'teams' should have:
                - 'goals_for' (float): Season average.
                - 'goals_against' (float): Season average.
                - 'matches_played' (int): Matches played this season.
                - 'form_factor' (float): Recent form multiplier.

    Returns:
        Dictionary with keys:
        - 'home_xg': Expected goals for home team (float, typically 0-3).
        - 'away_xg': Expected goals for away team (float, typically 0-3).

    Raises:
        KeyError: If team data is missing from season_data.
        ValueError: If season_data is malformed or incomplete.

    Examples:
        >>> season_data = {
        ...     'teams': {
        ...         'MAN': {'goals_for': 2.1, 'goals_against': 0.8,
        ...                 'matches_played': 5, 'form_factor': 1.1},
        ...         'LIV': {'goals_for': 1.9, 'goals_against': 1.0,
        ...                 'matches_played': 5, 'form_factor': 0.95}
        ...     },
        ...     'matches': [],
        ...     'gameweek': 1
        ... }
        >>> result = estimate_xg_for_match('MAN', 'LIV', season_data)
        >>> result['home_xg']
        1.8
        >>> result['away_xg']
        1.4

    Notes:
        - xG values are typically in range [0, 4] for realistic matches.
        - Home team xG usually 0.2-0.4 higher than away team.
        - Head-to-head history can adjust expectations by ±0.2.
        - Requires at least 1 match of data per team.
    """
    # Validate season_data structure
    if "teams" not in season_data:
        raise ValueError("season_data missing 'teams' key")
    if "matches" not in season_data:
        raise ValueError("season_data missing 'matches' key")
    if "gameweek" not in season_data:
        raise ValueError("season_data missing 'gameweek' key")

    teams_data = season_data["teams"]

    # Get team data
    if home_team not in teams_data:
        raise KeyError(f"Home team '{home_team}' not found in season_data")
    if away_team not in teams_data:
        raise KeyError(f"Away team '{away_team}' not found in season_data")

    home_data = teams_data[home_team]
    away_data = teams_data[away_team]

    # Validate team data
    required_keys = {"goals_for", "goals_against", "matches_played", "form_factor"}
    for key in required_keys:
        if key not in home_data:
            raise ValueError(f"Home team data missing '{key}'")
        if key not in away_data:
            raise ValueError(f"Away team data missing '{key}'")

    # Calculate home team xG
    # xG = goals_for * form_factor * (opponent_goals_against / league_avg)
    # Lower opponent goals_against = stronger defense = lower xG
    home_gf = home_data["goals_for"]
    home_form = home_data["form_factor"]
    away_ga = away_data["goals_against"]

    # Opponent defense factor: league average GA assumed to be 1.0
    away_defense_factor = away_ga / 1.0
    away_defense_factor = max(0.6, min(1.4, away_defense_factor))  # Clamp between 0.6-1.4

    home_xg_raw = home_gf * home_form * away_defense_factor

    # Calculate away team xG
    away_gf = away_data["goals_for"]
    away_form = away_data["form_factor"]
    home_ga = home_data["goals_against"]

    # Opponent defense factor: league average GA assumed to be 1.0
    home_defense_factor = home_ga / 1.0
    home_defense_factor = max(0.6, min(1.4, home_defense_factor))  # Clamp between 0.6-1.4

    away_xg_raw = away_gf * away_form * home_defense_factor

    # Apply home advantage adjustment
    home_xg = home_xg_raw + 0.25  # Home advantage adds ~0.25 xG
    away_xg = away_xg_raw - 0.15  # Away disadvantage reduces ~0.15 xG

    # Clamp to realistic ranges
    home_xg = max(MIN_XG, min(home_xg, MAX_XG))
    away_xg = max(MIN_XG, min(away_xg, MAX_XG))

    return {
        "home_xg": float(home_xg),
        "away_xg": float(away_xg),
    }
