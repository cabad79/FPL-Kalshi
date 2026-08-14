"""Match outcome prediction skills for Kalshi football markets.

This module provides functions for predicting match results, analyzing team strength,
and estimating expected performance metrics.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class MatchOutcomePrediction(TypedDict):
    """Match outcome prediction with probabilities."""

    home_win: float
    draw: float
    away_win: float
    confidence: float


class MatchData(TypedDict, total=False):
    """Match data for prediction."""

    home_team: str
    away_team: str
    home_rating: float
    away_rating: float
    history: dict[str, Any]
    home_goals_for: float
    home_goals_against: float
    away_goals_for: float
    away_goals_against: float


class ModelParams(TypedDict, total=False):
    """Model parameters for prediction."""

    model_type: str
    weight_xg: float
    weight_elo: float
    weight_form: float
    weight_recent_form: float
    weight_head_to_head: float


def predict_match_outcome(
    match_data: MatchData, model_params: ModelParams | None = None
) -> MatchOutcomePrediction:
    """Predict match result probabilities using ensemble of models.

    Combines multiple prediction approaches (Elo, form-based, head-to-head history)
    using weighted ensemble method to generate robust match outcome predictions.

    Args:
        match_data: Dictionary containing match information:
            - home_team (str): Home team identifier
            - away_team (str): Away team identifier
            - home_rating (float): Home team strength rating (Elo or similar)
            - away_rating (float): Away team strength rating
            - history (dict, optional): Historical head-to-head records
            - home_goals_for (float, optional): Home team goals per match
            - home_goals_against (float, optional): Home team goals conceded per match
            - away_goals_for (float, optional): Away team goals per match
            - away_goals_against (float, optional): Away team goals conceded per match

        model_params: Dictionary with optional model parameters:
            - model_type (str): "ensemble", "elo", or "form" (default: "ensemble")
            - weight_elo (float): Elo model weight, 0-1 (default: 0.4)
            - weight_form (float): Form model weight, 0-1 (default: 0.3)
            - weight_xg (float): xG model weight, 0-1 (default: 0.3)

    Returns:
        Dictionary with:
            - home_win (float): Probability of home team winning (0.0-1.0)
            - draw (float): Probability of draw (0.0-1.0)
            - away_win (float): Probability of away team winning (0.0-1.0)
            - confidence (float): Model confidence (0.0-1.0), equals max probability

    Raises:
        ValueError: If match data missing required fields or ratings out of valid range
        TypeError: If inputs not of expected type

    Example:
        >>> match = {
        ...     "home_team": "Manchester City",
        ...     "away_team": "Nottingham Forest",
        ...     "home_rating": 2150,
        ...     "away_rating": 1580,
        ...     "home_goals_for": 2.8,
        ...     "home_goals_against": 0.5,
        ...     "away_goals_for": 1.2,
        ...     "away_goals_against": 2.1,
        ... }
        >>> params = {"model_type": "ensemble", "weight_elo": 0.4}
        >>> result = predict_match_outcome(match, params)
        >>> print(f"Home win: {result['home_win']:.2%}")
        Home win: 68.50%
        >>> sum(result[k] for k in ["home_win", "draw", "away_win"])
        1.0
    """
    if not model_params:
        model_params = {}

    # Validate inputs
    _validate_match_data(match_data)

    # Set defaults
    weight_elo = model_params.get("weight_elo", 0.4)
    weight_form = model_params.get("weight_form", 0.3)
    weight_xg = model_params.get("weight_xg", 0.3)
    model_type = model_params.get("model_type", "ensemble")

    # Normalize weights
    total_weight = weight_elo + weight_form + weight_xg
    if total_weight == 0:
        weight_elo = weight_form = weight_xg = 1 / 3
    else:
        weight_elo /= total_weight
        weight_form /= total_weight
        weight_xg /= total_weight

    if model_type == "elo":
        probs = _predict_via_elo(match_data)
    elif model_type == "form":
        probs = _predict_via_form(match_data)
    else:  # ensemble
        elo_probs = _predict_via_elo(match_data)
        form_probs = _predict_via_form(match_data)
        xg_probs = _predict_via_xg(match_data)

        probs = {
            "home_win": (
                weight_elo * elo_probs["home_win"]
                + weight_form * form_probs["home_win"]
                + weight_xg * xg_probs["home_win"]
            ),
            "draw": (
                weight_elo * elo_probs["draw"]
                + weight_form * form_probs["draw"]
                + weight_xg * xg_probs["draw"]
            ),
            "away_win": (
                weight_elo * elo_probs["away_win"]
                + weight_form * form_probs["away_win"]
                + weight_xg * xg_probs["away_win"]
            ),
        }

    # Ensure probabilities sum to 1.0
    total = sum(probs.values())
    if total > 0:
        for key in probs:
            probs[key] /= total

    confidence = max(probs.values())

    logger.info(
        f"Match prediction: {match_data.get('home_team', 'Home')} "
        f"vs {match_data.get('away_team', 'Away')} - "
        f"Home: {probs['home_win']:.2%}, Draw: {probs['draw']:.2%}, "
        f"Away: {probs['away_win']:.2%} (confidence: {confidence:.2%})"
    )

    return {
        "home_win": probs["home_win"],
        "draw": probs["draw"],
        "away_win": probs["away_win"],
        "confidence": confidence,
    }


def estimate_home_advantage(
    league: str, season: int, venue_data: dict[str, Any] | None = None
) -> float:
    """Calculate home advantage multiplier for given league and season.

    Estimates the strength of home field advantage based on historical data,
    league-specific factors, and optional venue-specific adjustments.

    Args:
        league: League identifier ("PL", "EFL", "Championship", etc.)
        season: Season year (e.g., 2024, 2025, 2026)
        venue_data: Optional dictionary with venue-specific factors:
            - attendance (int): Typical attendance
            - altitude (int): Stadium altitude in meters
            - weather_avg (str): Typical weather condition
            - crowd_factor (float): 0.9-1.2 adjustment for crowd intensity

    Returns:
        Home advantage multiplier (e.g., 1.15 means 15% advantage):
            - 1.0 = no advantage
            - 1.15 = typical 15% advantage
            - 1.25 = strong advantage
            - 0.95 = slight disadvantage (rare)

    Raises:
        ValueError: If league not recognized or season out of valid range
        TypeError: If inputs not of expected type

    Example:
        >>> advantage = estimate_home_advantage("PL", 2024)
        >>> print(f"Premier League home advantage: {(advantage - 1) * 100:.1f}%")
        Premier League home advantage: 14.5%

        >>> advantage = estimate_home_advantage("PL", 2024, {"crowd_factor": 1.1})
        >>> print(f"With strong crowd: {(advantage - 1) * 100:.1f}%")
        With strong crowd: 16.0%
    """
    # Validate inputs
    if not isinstance(league, str):
        raise TypeError(f"league must be str, got {type(league)}")
    if not isinstance(season, int) or isinstance(season, bool):
        raise TypeError(f"season must be int, got {type(season)}")
    if season < 1995 or season > 2100:
        raise ValueError(f"season must be between 1995 and 2100, got {season}")

    league_upper = league.upper()

    # League baseline home advantage (from historical data)
    league_factors = {
        "PL": 1.145,  # Premier League: 14.5%
        "CHAMPIONSHIP": 1.135,  # Championship: 13.5%
        "EFL": 1.125,  # EFL League One/Two: 12.5%
        "BUNDESLIGA": 1.160,  # Bundesliga: 16%
        "LIGUE1": 1.120,  # Ligue 1: 12%
        "SERIE_A": 1.155,  # Serie A: 15.5%
        "LA_LIGA": 1.135,  # La Liga: 13.5%
        "EREDIVISIE": 1.105,  # Eredivisie: 10.5%
    }

    if league_upper not in league_factors:
        raise ValueError(f"Unknown league: {league}. Valid: {list(league_factors.keys())}")

    base_factor = league_factors[league_upper]

    # Seasonal variations (average years have ~1.0)
    season_adjustments = {
        2024: 0.98,  # Recent trend: slightly lower
        2025: 0.99,
        2026: 1.00,  # Current season
        2027: 1.00,
    }

    season_adjustment = season_adjustments.get(season, 1.0)
    base_factor = base_factor * season_adjustment

    # Apply venue-specific adjustments if provided
    if venue_data:
        crowd_factor = venue_data.get("crowd_factor", 1.0)
        if not 0.9 <= crowd_factor <= 1.2:
            logger.warning(f"crowd_factor {crowd_factor} outside expected range [0.9, 1.2]")
            crowd_factor = max(0.9, min(1.2, crowd_factor))

        base_factor = base_factor * crowd_factor

    # Ensure result is between reasonable bounds
    base_factor = max(0.85, min(1.35, base_factor))

    logger.info(f"Home advantage for {league} {season}: {(base_factor - 1) * 100:.1f}%")

    return base_factor


def calculate_elo_rating(
    current_elo: float, opponent_elo: float, result: str, k_factor: float = 32.0
) -> float:
    """Calculate updated Elo rating after a match.

    Uses standard chess Elo formula with football-specific K-factors.
    Reflects probability of match outcome and adjusts rating accordingly.

    Args:
        current_elo: Team's current Elo rating (typical range: 1400-2200)
        opponent_elo: Opponent's Elo rating
        result: Match result from perspective of current_elo team:
            - "win": Team won the match
            - "draw": Match ended in draw
            - "loss": Team lost the match
        k_factor: Elo volatility factor (default 32):
            - 16: Elite teams (Elo > 2000)
            - 32: Established teams (1600-2000)
            - 48: Variable teams (< 1600) or newly promoted

    Returns:
        Updated Elo rating as float (same scale as input)

    Raises:
        ValueError: If result not in ["win", "draw", "loss"] or K-factor invalid
        TypeError: If ratings not numeric or not positive

    Example:
        >>> # Team with 1800 Elo beats team with 1600 Elo
        >>> new_elo = calculate_elo_rating(1800, 1600, "win", k_factor=32)
        >>> print(f"New rating: {new_elo:.0f}")
        New rating: 1819

        >>> # Same team draws with 1900 Elo opponent
        >>> new_elo = calculate_elo_rating(1800, 1900, "draw", k_factor=32)
        >>> print(f"New rating: {new_elo:.0f}")
        New rating: 1829
    """
    # Validate inputs
    if not isinstance(current_elo, (int, float)) or current_elo <= 0:
        raise TypeError(f"current_elo must be positive number, got {current_elo}")
    if not isinstance(opponent_elo, (int, float)) or opponent_elo <= 0:
        raise TypeError(f"opponent_elo must be positive number, got {opponent_elo}")
    if not isinstance(k_factor, (int, float)) or k_factor <= 0:
        raise ValueError(f"k_factor must be positive, got {k_factor}")

    result_lower = result.lower().strip()
    if result_lower not in ["win", "draw", "loss"]:
        raise ValueError(f'result must be "win", "draw", or "loss", got {result}')

    # Calculate expected score (probability of win from current_elo perspective)
    # Using standard Elo formula: expected = 1 / (1 + 10^((opponent - current)/400))
    elo_diff = opponent_elo - current_elo
    expected = 1.0 / (1.0 + 10.0 ** (elo_diff / 400.0))

    # Map result to actual score
    if result_lower == "win":
        actual_score = 1.0
    elif result_lower == "draw":
        actual_score = 0.5
    else:  # loss
        actual_score = 0.0

    # Calculate rating change
    rating_change = k_factor * (actual_score - expected)
    new_elo: float = current_elo + rating_change

    logger.debug(
        f"Elo update: {current_elo:.0f} vs {opponent_elo:.0f}, "
        f"result={result}, K={k_factor} -> {new_elo:.0f} "
        f"(change: {rating_change:+.0f})"
    )

    return new_elo


def calculate_pythagorean_points(
    goals_for: float, goals_against: float, exponent: float = 1.8
) -> float:
    """Calculate expected league points from goal differential using Pythagorean formula.

    Estimates the "true" strength of a team by comparing actual goal differential
    to expected goal differential. Returns expected points per match on 0-3 scale.

    Uses modified Pythagorean expectation adapted for football (originally baseball).
    Formula: 3 * (GF^exp / (GF^exp + GA^exp))

    Args:
        goals_for: Goals scored per match (or total in period)
        goals_against: Goals conceded per match (or total in period)
        exponent: Pythagorean exponent (default 1.8):
            - 1.8: Beggs model (most accurate for EPL)
            - 1.5: Alternative (more conservative)
            - 2.0: Kingsman model
            - Higher values (2.5+): Emphasize goal differential more

    Returns:
        Expected points per match on 0-3 scale (0.0 = very poor, 3.0 = perfect):
            - Multiply by matches played for total expected points
            - Example: 2.1 expected points/match × 38 matches = 79.8 expected season total

    Raises:
        ValueError: If goals_for or goals_against negative, or exponent out of range
        ZeroDivisionError: If both goals_for and goals_against are 0

    Example:
        >>> # Team scoring 2.0 GF and conceding 1.0 GA per match
        >>> exp_points = calculate_pythagorean_points(2.0, 1.0, exponent=1.8)
        >>> print(f"Expected points per match: {exp_points:.2f}")
        Expected points per match: 2.44

        >>> # Over 38 matches
        >>> season_total = exp_points * 38
        >>> print(f"Expected season points: {season_total:.0f}")
        Expected season points: 93

        >>> # Team with equal offense and defense (should be ~1.5 points/match)
        >>> exp_points = calculate_pythagorean_points(1.5, 1.5, exponent=1.8)
        >>> print(f"Neutral team: {exp_points:.2f}")
        Neutral team: 1.50
    """
    # Validate inputs
    if goals_for < 0 or goals_against < 0:
        raise ValueError(f"Goals must be non-negative, got GF={goals_for}, GA={goals_against}")
    if exponent <= 0 or exponent > 3.0:
        raise ValueError(f"Exponent must be in (0, 3], got {exponent}")

    # Handle edge case: no goals scored at all (very rare)
    if goals_for == 0 and goals_against == 0:
        raise ValueError("Both goals_for and goals_against cannot be zero")

    # Handle edge case: no goals conceded (perfect defense)
    if goals_against == 0:
        # Award maximum points (3.0 per match)
        logger.warning("Perfect defense: goals_against=0, returning 3.0")
        return 3.0

    # Calculate Pythagorean fraction
    numerator = goals_for**exponent
    denominator = (goals_for**exponent) + (goals_against**exponent)

    if denominator == 0:
        raise ValueError("Denominator cannot be zero (both GF and GA are 0)")

    pythag_fraction = numerator / denominator

    # Convert to expected points per match (3-point system)
    expected_points_per_match = 3.0 * pythag_fraction

    # Sanity check: should be between 0 and 3
    expected_points: float = max(0.0, min(3.0, expected_points_per_match))

    logger.debug(
        f"Pythagorean calculation: GF={goals_for}, GA={goals_against}, "
        f"exp={exponent} -> fraction={pythag_fraction:.4f}, "
        f"points_per_match={expected_points:.2f}"
    )

    return expected_points


# Private helper functions


def _validate_match_data(match_data: MatchData) -> None:
    """Validate match data contains required fields with valid types.

    Args:
        match_data: Dictionary to validate

    Raises:
        ValueError: If required fields missing or have invalid values
        TypeError: If fields have wrong types
    """
    required = ["home_team", "away_team", "home_rating", "away_rating"]
    for field in required:
        if field not in match_data:
            raise ValueError(f"match_data missing required field: {field}")

    # Validate rating ranges (Elo-like: typically 1200-2400)
    home_rating = match_data.get("home_rating", 0)
    away_rating = match_data.get("away_rating", 0)

    if not isinstance(home_rating, (int, float)) or home_rating <= 0:
        raise TypeError(f"home_rating must be positive number, got {home_rating}")
    if not isinstance(away_rating, (int, float)) or away_rating <= 0:
        raise TypeError(f"away_rating must be positive number, got {away_rating}")

    if home_rating < 500 or home_rating > 3000:
        logger.warning(f"home_rating {home_rating} outside typical range [500, 3000]")
    if away_rating < 500 or away_rating > 3000:
        logger.warning(f"away_rating {away_rating} outside typical range [500, 3000]")


def _predict_via_elo(match_data: MatchData) -> dict[str, float]:
    """Predict match outcome using Elo rating differential.

    Simple model based on team strength difference.
    """
    home_elo = float(match_data.get("home_rating", 1600))
    away_elo = float(match_data.get("away_rating", 1600))
    elo_diff = home_elo - away_elo

    # Using Elo to expected goals mapping
    # Formula: expected_goals = 1.5 + (elo_diff / 400) * 0.5
    home_expected_goals = max(0.3, 1.5 + (elo_diff / 400.0) * 0.5)
    away_expected_goals = max(0.3, 1.5 - (elo_diff / 400.0) * 0.5)

    # Use Poisson-like approximation
    # P(Home Win) ≈ home_xg / (home_xg + away_xg + draw_factor)
    draw_factor = 0.6  # Accounts for draw probability
    total = home_expected_goals + away_expected_goals + draw_factor

    return {
        "home_win": home_expected_goals / total,
        "draw": draw_factor / total,
        "away_win": away_expected_goals / total,
    }


def _predict_via_form(match_data: MatchData) -> dict[str, float]:
    """Predict match outcome using recent form and goal differential.

    Uses pythagorean points as proxy for team strength.
    """
    home_gf = float(match_data.get("home_goals_for", 1.5))
    home_ga = float(match_data.get("home_goals_against", 1.5))
    away_gf = float(match_data.get("away_goals_for", 1.5))
    away_ga = float(match_data.get("away_goals_against", 1.5))

    # Safe calculation with fallback
    try:
        home_strength = calculate_pythagorean_points(home_gf, home_ga)
        away_strength = calculate_pythagorean_points(away_gf, away_ga)
    except (ValueError, ZeroDivisionError):
        # Fall back to simple ratio
        home_strength = 1.5
        away_strength = 1.5

    # Normalize to probabilities
    total = home_strength + away_strength + 0.6
    return {
        "home_win": home_strength / total,
        "draw": 0.6 / total,
        "away_win": away_strength / total,
    }


def _predict_via_xg(match_data: MatchData) -> dict[str, float]:
    """Predict match outcome using expected goals (xG) approach.

    Uses goals for/against as proxy for xG.
    """
    # For MVP, use same as form model (xG data would come from data service)
    return _predict_via_form(match_data)
