"""
MCP (Model Context Protocol) Schema Definition for Football Markets Integration.

Defines all 18 tools and 3 resource types for unified prediction and analysis framework.
Integrates HAIKU-1 (Goal Prediction), HAIKU-2 (Match Outcomes), HAIKU-3 (Player Props),
and HAIKU-4 (Data Services).

Author: SONNET-2 Data Layer Integration Validator
Date: 2026-08-14
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict, Literal
from enum import Enum


# ============================================================================
# TOOL DEFINITIONS (18 TOOLS)
# ============================================================================

class ToolParameter(TypedDict, total=False):
    """Type definition for MCP tool parameters."""
    name: str
    description: str
    type: str
    required: bool
    default: Any
    enum: List[str]
    min: float
    max: float


class ToolDefinition(TypedDict):
    """Complete MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    category: str
    requires_data: List[str]
    rate_limit: Optional[Dict[str, int]]


# ============================================================================
# GOAL PREDICTION TOOLS (3 tools)
# ============================================================================

PREDICT_MATCH_GOALS: ToolDefinition = {
    "name": "predict_match_goals",
    "description": (
        "Predict actual goals for a match using expected goals (xG) with Poisson distribution. "
        "Returns predicted goal counts for both teams with confidence levels."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "home_xg": {
                "type": "number",
                "description": "Expected goals for home team (0.0-5.0)",
                "minimum": 0.0,
                "maximum": 5.0,
            },
            "away_xg": {
                "type": "number",
                "description": "Expected goals for away team (0.0-5.0)",
                "minimum": 0.0,
                "maximum": 5.0,
            },
            "correlation_factor": {
                "type": "number",
                "description": "Strength of correlation (0.0=independent, 1.0=perfect)",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.1,
            },
        },
        "required": ["home_xg", "away_xg"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "home_goals": {"type": "integer", "description": "Predicted home team goals"},
            "away_goals": {"type": "integer", "description": "Predicted away team goals"},
            "probability": {"type": "number", "description": "Probability of exact outcome"},
            "confidence": {"type": "number", "description": "Confidence level (0-1)"},
        },
    },
    "category": "goal_prediction",
    "requires_data": ["team_stats", "opponent_defense"],
    "rate_limit": {"requests_per_second": 100, "burst": 1000},
}

CALCULATE_POISSON_PROBABILITIES: ToolDefinition = {
    "name": "calculate_poisson_probabilities",
    "description": (
        "Calculate probability distribution for goals using Poisson distribution. "
        "Returns probability of each goal count (0 to max_goals)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "lambda_param": {
                "type": "number",
                "description": "Rate parameter (expected goals)",
                "minimum": 0.01,
                "maximum": 10.0,
            },
            "max_goals": {
                "type": "integer",
                "description": "Maximum goals to calculate",
                "minimum": 0,
                "maximum": 20,
                "default": 10,
            },
        },
        "required": ["lambda_param"],
    },
    "output_schema": {
        "type": "object",
        "description": "Goal count -> Probability mapping",
        "additionalProperties": {"type": "number"},
    },
    "category": "goal_prediction",
    "requires_data": ["xg_estimates"],
    "rate_limit": {"requests_per_second": 500, "burst": 5000},
}

ESTIMATE_GOAL_DISTRIBUTION: ToolDefinition = {
    "name": "estimate_goal_distribution",
    "description": (
        "Estimate goal distribution for a team against specific opponent. "
        "Combines team stats, opponent analysis, and contextual factors."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "team_stats": {
                "type": "object",
                "description": "Team statistics (goals_for, goals_against, form_factor, matches_played)",
                "properties": {
                    "goals_for": {"type": "number"},
                    "goals_against": {"type": "number"},
                    "matches_played": {"type": "integer"},
                    "form_factor": {"type": "number"},
                },
                "required": ["goals_for", "goals_against", "matches_played", "form_factor"],
            },
            "opponent_stats": {
                "type": "object",
                "description": "Opponent statistics",
                "properties": {
                    "goals_for": {"type": "number"},
                    "goals_against": {"type": "number"},
                    "defense_rating": {"type": "number"},
                },
                "required": ["goals_for", "goals_against", "defense_rating"],
            },
            "context": {
                "type": "object",
                "description": "Match context (home_away, injury_status, head_to_head)",
                "properties": {
                    "home_away": {"type": "string", "enum": ["home", "away"]},
                    "injury_status": {"type": "string", "enum": ["normal", "minor", "major"]},
                    "head_to_head": {"type": "object"},
                },
                "required": ["home_away", "injury_status", "head_to_head"],
            },
        },
        "required": ["team_stats", "opponent_stats", "context"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "distribution": {
                "type": "object",
                "description": "Goal count -> Probability",
                "additionalProperties": {"type": "number"},
            },
            "confidence": {"type": "number", "description": "Confidence (0-1)"},
        },
    },
    "category": "goal_prediction",
    "requires_data": ["team_data", "fixture_context"],
    "rate_limit": {"requests_per_second": 50, "burst": 500},
}


# ============================================================================
# MATCH OUTCOME TOOLS (4 tools)
# ============================================================================

PREDICT_MATCH_OUTCOME: ToolDefinition = {
    "name": "predict_match_outcome",
    "description": (
        "Predict match result probabilities using ensemble of models "
        "(Elo, form-based, xG). Returns win/draw/loss probabilities."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "home_team": {"type": "string", "description": "Home team identifier"},
            "away_team": {"type": "string", "description": "Away team identifier"},
            "home_rating": {
                "type": "number",
                "description": "Home team Elo rating",
                "minimum": 500,
                "maximum": 3000,
            },
            "away_rating": {
                "type": "number",
                "description": "Away team Elo rating",
                "minimum": 500,
                "maximum": 3000,
            },
            "home_goals_for": {"type": "number", "description": "Home goals/match"},
            "home_goals_against": {"type": "number", "description": "Home goals conceded/match"},
            "away_goals_for": {"type": "number", "description": "Away goals/match"},
            "away_goals_against": {"type": "number", "description": "Away goals conceded/match"},
            "model_type": {
                "type": "string",
                "enum": ["ensemble", "elo", "form"],
                "description": "Prediction model type",
                "default": "ensemble",
            },
        },
        "required": ["home_team", "away_team", "home_rating", "away_rating"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "home_win": {"type": "number", "description": "Home win probability"},
            "draw": {"type": "number", "description": "Draw probability"},
            "away_win": {"type": "number", "description": "Away win probability"},
            "confidence": {"type": "number", "description": "Prediction confidence"},
        },
    },
    "category": "match_outcomes",
    "requires_data": ["team_ratings", "recent_form"],
    "rate_limit": {"requests_per_second": 50, "burst": 500},
}

ESTIMATE_HOME_ADVANTAGE: ToolDefinition = {
    "name": "estimate_home_advantage",
    "description": (
        "Calculate home advantage multiplier for given league and season. "
        "Returns multiplier (1.15 = 15% advantage)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "league": {
                "type": "string",
                "enum": ["PL", "CHAMPIONSHIP", "EFL", "BUNDESLIGA", "LIGUE1", "SERIE_A", "LA_LIGA", "EREDIVISIE"],
                "description": "League identifier",
            },
            "season": {
                "type": "integer",
                "description": "Season year",
                "minimum": 1995,
                "maximum": 2100,
            },
            "crowd_factor": {
                "type": "number",
                "description": "Crowd intensity multiplier",
                "minimum": 0.9,
                "maximum": 1.2,
                "default": 1.0,
            },
        },
        "required": ["league", "season"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "multiplier": {"type": "number", "description": "Home advantage multiplier"},
            "league": {"type": "string"},
            "season": {"type": "integer"},
        },
    },
    "category": "match_outcomes",
    "requires_data": ["league_data"],
    "rate_limit": {"requests_per_second": 1000, "burst": 10000},
}

CALCULATE_ELO_RATING: ToolDefinition = {
    "name": "calculate_elo_rating",
    "description": (
        "Calculate updated Elo rating after match result. "
        "Uses standard chess Elo formula with football-specific K-factors."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "current_elo": {
                "type": "number",
                "description": "Team current Elo",
                "minimum": 0,
            },
            "opponent_elo": {
                "type": "number",
                "description": "Opponent Elo",
                "minimum": 0,
            },
            "result": {
                "type": "string",
                "enum": ["win", "draw", "loss"],
                "description": "Match result",
            },
            "k_factor": {
                "type": "number",
                "description": "Volatility factor (16/32/48)",
                "default": 32.0,
            },
        },
        "required": ["current_elo", "opponent_elo", "result"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "new_elo": {"type": "number", "description": "Updated Elo rating"},
            "change": {"type": "number", "description": "Elo change"},
            "interpretation": {"type": "string"},
        },
    },
    "category": "match_outcomes",
    "requires_data": ["team_ratings"],
    "rate_limit": {"requests_per_second": 500, "burst": 5000},
}

CALCULATE_PYTHAGOREAN_POINTS: ToolDefinition = {
    "name": "calculate_pythagorean_points",
    "description": (
        "Calculate expected league points from goal differential using Pythagorean formula. "
        "Returns expected points per match (0-3 scale)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "goals_for": {
                "type": "number",
                "description": "Goals scored",
                "minimum": 0,
            },
            "goals_against": {
                "type": "number",
                "description": "Goals conceded",
                "minimum": 0,
            },
            "exponent": {
                "type": "number",
                "description": "Pythagorean exponent (1.8 default)",
                "minimum": 0.1,
                "maximum": 3.0,
                "default": 1.8,
            },
        },
        "required": ["goals_for", "goals_against"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "expected_points_per_match": {"type": "number"},
            "interpretation": {"type": "string"},
        },
    },
    "category": "match_outcomes",
    "requires_data": ["goal_statistics"],
    "rate_limit": {"requests_per_second": 500, "burst": 5000},
}


# ============================================================================
# PLAYER PROPS TOOLS (4 tools)
# ============================================================================

PREDICT_GOAL_SCORER_LIKELIHOOD: ToolDefinition = {
    "name": "predict_goal_scorer_likelihood",
    "description": (
        "Predict probability a player scores in next match. "
        "Uses xG model with form analysis and opponent defense assessment."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "player_id": {"type": "string", "description": "Player identifier"},
            "player_name": {"type": "string", "description": "Player full name"},
            "position": {
                "type": "string",
                "enum": ["FWD", "MID", "DEF", "GK"],
            },
            "goals_last_5": {"type": "number", "minimum": 0, "maximum": 5},
            "minutes_last_5": {"type": "integer", "minimum": 0, "maximum": 450},
            "opponent_xga": {"type": "number", "description": "Opponent xGA/match"},
            "opponent_ga_per_match": {"type": "number"},
            "recent_streak": {
                "type": "array",
                "items": {"type": "integer", "enum": [0, 1]},
                "minItems": 5,
                "maxItems": 5,
                "description": "Last 5 matches (1=scored, 0=didn't)",
            },
        },
        "required": [
            "player_id", "player_name", "position", "goals_last_5",
            "minutes_last_5", "opponent_xga", "opponent_ga_per_match", "recent_streak"
        ],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "probability_scores": {"type": "number"},
            "expected_goals": {"type": "number"},
            "confidence": {"type": "number"},
            "form_rating": {"type": "number"},
            "vs_this_defense": {"type": "string", "enum": ["Weak", "Medium", "Strong"]},
            "odds_estimate": {"type": "integer", "description": "Kalshi cents (0-100)"},
            "recommendation": {"type": "string"},
        },
    },
    "category": "player_props",
    "requires_data": ["player_stats", "opponent_defense"],
    "rate_limit": {"requests_per_second": 100, "burst": 1000},
}

PREDICT_ASSIST_PROBABILITY: ToolDefinition = {
    "name": "predict_assist_probability",
    "description": (
        "Predict probability a player provides assist in next match. "
        "Position-specific analysis with form adjustment."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "player_id": {"type": "string"},
            "player_name": {"type": "string"},
            "position": {"type": "string", "enum": ["FWD", "MID", "DEF", "GK"]},
            "assists_last_5": {"type": "number", "minimum": 0, "maximum": 5},
            "minutes_last_5": {"type": "integer", "minimum": 0, "maximum": 450},
            "opponent_xga": {"type": "number"},
            "recent_streak": {
                "type": "array",
                "items": {"type": "integer", "enum": [0, 1]},
                "minItems": 5,
                "maxItems": 5,
            },
        },
        "required": [
            "player_id", "player_name", "position",
            "assists_last_5", "minutes_last_5", "opponent_xga", "recent_streak"
        ],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "probability_assists": {"type": "number"},
            "expected_assists": {"type": "number"},
            "confidence": {"type": "number"},
            "form_rating": {"type": "number"},
            "vs_this_defense": {"type": "string"},
            "odds_estimate": {"type": "integer"},
            "recommendation": {"type": "string"},
        },
    },
    "category": "player_props",
    "requires_data": ["player_stats", "opponent_defense"],
    "rate_limit": {"requests_per_second": 100, "burst": 1000},
}

ESTIMATE_SHOTS_ON_TARGET: ToolDefinition = {
    "name": "estimate_shots_on_target",
    "description": (
        "Estimate shots and accuracy for player in next match. "
        "Position-specific base rates with opponent adjustment."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "player_id": {"type": "string"},
            "player_name": {"type": "string"},
            "position": {"type": "string", "enum": ["FWD", "MID", "DEF", "GK"]},
            "shots_last_5": {"type": "number", "minimum": 0},
            "shots_on_target_last_5": {"type": "number", "minimum": 0},
            "minutes_last_5": {"type": "integer", "minimum": 0},
            "opponent_xga": {"type": "number"},
        },
        "required": [
            "player_id", "player_name", "position",
            "shots_last_5", "shots_on_target_last_5", "minutes_last_5", "opponent_xga"
        ],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "expected_shots": {"type": "number"},
            "expected_shots_on_target": {"type": "number"},
            "shot_accuracy": {"type": "number"},
            "confidence": {"type": "number"},
            "form_rating": {"type": "number"},
            "vs_this_defense": {"type": "string"},
        },
    },
    "category": "player_props",
    "requires_data": ["player_stats", "opponent_defense"],
    "rate_limit": {"requests_per_second": 100, "burst": 1000},
}

ANALYZE_PLAYER_PERFORMANCE: ToolDefinition = {
    "name": "analyze_player_performance",
    "description": (
        "Comprehensive player performance analysis with position benchmarking. "
        "Includes FPL projections, injury risk, and form trajectory."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "player_id": {"type": "string"},
            "player_name": {"type": "string"},
            "position": {"type": "string", "enum": ["GK", "DEF", "MID", "FWD"]},
            "team": {"type": "string"},
            "timeframe": {"type": "string", "enum": ["season", "last_10_matches", "recent_form"]},
            "shots_per_90": {"type": "number"},
            "xg_per_90": {"type": "number"},
            "conversion_rate": {"type": "number", "minimum": 0, "maximum": 1},
            "shot_accuracy": {"type": "number", "minimum": 0, "maximum": 1},
            "key_passes_per_90": {"type": "number"},
            "xa_per_90": {"type": "number"},
            "recent_3_avg": {"type": "number"},
            "recent_6_avg": {"type": "number"},
            "season_avg": {"type": "number"},
            "contact_intensity": {"type": "number", "minimum": 0, "maximum": 10},
            "fatigue_level": {"type": "number", "minimum": 0, "maximum": 1},
            "recent_injuries": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "player_id", "player_name", "position", "team", "timeframe",
            "shots_per_90", "xg_per_90", "conversion_rate", "shot_accuracy",
            "key_passes_per_90", "xa_per_90", "recent_3_avg", "recent_6_avg",
            "season_avg", "contact_intensity", "fatigue_level", "recent_injuries"
        ],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "performance_metrics": {"type": "object"},
            "position_benchmarking": {"type": "object"},
            "fpl_projections": {"type": "object"},
            "injury_risk": {"type": "object"},
            "form_trajectory": {"type": "object"},
        },
    },
    "category": "player_props",
    "requires_data": ["player_data", "benchmarks"],
    "rate_limit": {"requests_per_second": 50, "burst": 500},
}


# ============================================================================
# DATA SERVICE TOOLS (4 tools)
# ============================================================================

CALCULATE_BTTS_PROBABILITY: ToolDefinition = {
    "name": "calculate_btts_probability",
    "description": (
        "Calculate Both Teams To Score (BTTS) probability using Poisson distribution. "
        "Returns BTTS and individual team scoring probabilities."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "home_lambda": {
                "type": "number",
                "description": "Expected goals for home team",
                "minimum": 0.3,
                "maximum": 4.5,
            },
            "away_lambda": {
                "type": "number",
                "description": "Expected goals for away team",
                "minimum": 0.3,
                "maximum": 4.5,
            },
            "max_goals": {
                "type": "integer",
                "description": "Max goals in calculation",
                "default": 6,
            },
        },
        "required": ["home_lambda", "away_lambda"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "btts_yes": {"type": "number"},
            "btts_no": {"type": "number"},
            "p_home_scores": {"type": "number"},
            "p_away_scores": {"type": "number"},
            "expected_home_goals": {"type": "number"},
            "expected_away_goals": {"type": "number"},
        },
    },
    "category": "data_services",
    "requires_data": ["xg_estimates"],
    "rate_limit": {"requests_per_second": 500, "burst": 5000},
}

CONFIDENCE_INTERVAL_PREDICTION: ToolDefinition = {
    "name": "confidence_interval_prediction",
    "description": (
        "Calculate confidence interval around a prediction. "
        "Uses t-distribution accounting for sample uncertainty."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "prediction_point": {
                "type": "number",
                "description": "Point estimate value",
            },
            "sample_data": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 2,
                "description": "Historical observations",
            },
            "confidence_level": {
                "type": "number",
                "enum": [0.90, 0.95, 0.99],
                "default": 0.95,
            },
            "prediction_type": {
                "type": "string",
                "enum": ["confidence", "prediction"],
                "default": "confidence",
            },
        },
        "required": ["prediction_point", "sample_data"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "point_estimate": {"type": "number"},
            "lower_bound": {"type": "number"},
            "upper_bound": {"type": "number"},
            "margin_of_error": {"type": "number"},
            "interval_width": {"type": "number"},
            "confidence_level": {"type": "number"},
            "interpretation": {"type": "string"},
        },
    },
    "category": "data_services",
    "requires_data": ["predictions", "historical_data"],
    "rate_limit": {"requests_per_second": 100, "burst": 1000},
}

APPLY_KELLY_CRITERION: ToolDefinition = {
    "name": "apply_kelly_criterion",
    "description": (
        "Calculate optimal bet size using Kelly criterion. "
        "Returns recommended stake with fractional Kelly safety constraints."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "probability_win": {
                "type": "number",
                "description": "Predicted win probability",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "odds": {
                "type": "number",
                "description": "Decimal odds",
                "minimum": 1.0,
            },
            "bankroll": {
                "type": "number",
                "description": "Total bankroll",
                "default": 1000,
            },
            "kelly_fraction": {
                "type": "number",
                "description": "Fractional Kelly (0.25 = quarter Kelly)",
                "default": 0.25,
            },
        },
        "required": ["probability_win", "odds"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "kelly_fraction": {"type": "number"},
            "recommended_stake": {"type": "number"},
            "fractional_kelly": {"type": "number"},
            "max_stake": {"type": "number"},
            "expected_value": {"type": "number"},
            "interpretation": {"type": "string"},
        },
    },
    "category": "data_services",
    "requires_data": ["odds_probabilities"],
    "rate_limit": {"requests_per_second": 200, "burst": 2000},
}

GET_FPL_TEAM_DATA: ToolDefinition = {
    "name": "get_fpl_team_data",
    "description": (
        "Fetch team data from FPL API with caching. "
        "Returns team statistics, form, and fixture info."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "team_id": {"type": "string", "description": "Team identifier"},
            "use_cache": {"type": "boolean", "default": True},
        },
        "required": ["team_id"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "team_id": {"type": "string"},
            "name": {"type": "string"},
            "goals_for": {"type": "number"},
            "goals_against": {"type": "number"},
            "points": {"type": "integer"},
            "position": {"type": "integer"},
            "form_rating": {"type": "number"},
            "attack_strength": {"type": "number"},
            "defense_strength": {"type": "number"},
            "updated_at": {"type": "string"},
        },
    },
    "category": "data_services",
    "requires_data": ["fpl_api"],
    "rate_limit": {"requests_per_second": 10, "burst": 100},
}

GET_FOOTBALL_DATA_MATCH_INFO: ToolDefinition = {
    "name": "get_football_data_match_info",
    "description": (
        "Fetch combined match data from both teams. "
        "Returns xGA, defensive strength, and head-to-head info."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "home_team": {"type": "string", "description": "Home team identifier"},
            "away_team": {"type": "string", "description": "Away team identifier"},
            "use_cache": {"type": "boolean", "default": True},
        },
        "required": ["home_team", "away_team"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "home_team": {"type": "string"},
            "away_team": {"type": "string"},
            "home_data": {"type": "object"},
            "away_data": {"type": "object"},
            "head_to_head": {"type": "object"},
            "updated_at": {"type": "string"},
        },
    },
    "category": "data_services",
    "requires_data": ["football_data_api"],
    "rate_limit": {"requests_per_second": 10, "burst": 100},
}

SCHEDULE_CACHE_UPDATE: ToolDefinition = {
    "name": "schedule_cache_update",
    "description": (
        "Schedule periodic cache updates for data service. "
        "Manages async refresh cycles at specified frequencies."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "cache_key": {"type": "string", "description": "Cache key to update"},
            "frequency": {
                "type": "string",
                "enum": ["EVERY_10_MINUTES", "HOURLY", "DAILY"],
            },
            "start_now": {"type": "boolean", "default": False},
        },
        "required": ["cache_key", "frequency"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "cache_key": {"type": "string"},
            "scheduled": {"type": "boolean"},
            "frequency": {"type": "string"},
            "next_update": {"type": "string"},
        },
    },
    "category": "data_services",
    "requires_data": ["scheduler"],
    "rate_limit": {"requests_per_second": 50, "burst": 500},
}


# ============================================================================
# RESOURCE DEFINITIONS (3 RESOURCE TYPES)
# ============================================================================

@dataclass
class ResourceDefinition:
    """MCP Resource Definition."""
    name: str
    uri_template: str
    description: str
    schema: Dict[str, Any]
    examples: List[Dict[str, Any]]


MATCH_PREDICTIONS_RESOURCE = ResourceDefinition(
    name="match_predictions",
    uri_template="kalshi://match_predictions/{match_id}",
    description=(
        "Real-time match prediction resource with all model outputs. "
        "Includes goal predictions, outcome probabilities, confidence intervals, and recommendations."
    ),
    schema={
        "type": "object",
        "properties": {
            "match_id": {"type": "string"},
            "home_team": {"type": "string"},
            "away_team": {"type": "string"},
            "kickoff_time": {"type": "string", "format": "date-time"},
            "predictions": {
                "type": "object",
                "properties": {
                    "goal_prediction": {
                        "type": "object",
                        "properties": {
                            "home_goals": {"type": "integer"},
                            "away_goals": {"type": "integer"},
                            "probability": {"type": "number"},
                            "confidence": {"type": "number"},
                        },
                    },
                    "match_outcome": {
                        "type": "object",
                        "properties": {
                            "home_win": {"type": "number"},
                            "draw": {"type": "number"},
                            "away_win": {"type": "number"},
                            "confidence": {"type": "number"},
                        },
                    },
                    "btts": {
                        "type": "object",
                        "properties": {
                            "btts_yes": {"type": "number"},
                            "btts_no": {"type": "number"},
                        },
                    },
                    "confidence_intervals": {
                        "type": "object",
                        "properties": {
                            "goals": {
                                "type": "object",
                                "properties": {
                                    "lower": {"type": "number"},
                                    "upper": {"type": "number"},
                                    "confidence_level": {"type": "number"},
                                },
                            },
                            "outcome": {
                                "type": "object",
                                "properties": {
                                    "lower": {"type": "number"},
                                    "upper": {"type": "number"},
                                },
                            },
                        },
                    },
                },
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "updated_at": {"type": "string", "format": "date-time"},
                    "next_update": {"type": "string", "format": "date-time"},
                    "data_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
    },
    examples=[
        {
            "match_id": "PL_20260815_MAN_LIV",
            "home_team": "Manchester City",
            "away_team": "Liverpool",
            "kickoff_time": "2026-08-15T15:00:00Z",
            "predictions": {
                "goal_prediction": {
                    "home_goals": 2,
                    "away_goals": 1,
                    "probability": 0.18,
                    "confidence": 0.75,
                },
                "match_outcome": {
                    "home_win": 0.68,
                    "draw": 0.18,
                    "away_win": 0.14,
                    "confidence": 0.68,
                },
                "btts": {
                    "btts_yes": 0.52,
                    "btts_no": 0.48,
                },
            },
        }
    ],
)

PLAYER_ANALYSIS_RESOURCE = ResourceDefinition(
    name="player_analysis",
    uri_template="kalshi://player_analysis/{player_id}",
    description=(
        "Comprehensive player analysis with next-match predictions. "
        "Includes goal probability, assists, shots, form analysis, and injury risk."
    ),
    schema={
        "type": "object",
        "properties": {
            "player_id": {"type": "string"},
            "name": {"type": "string"},
            "team": {"type": "string"},
            "position": {"type": "string"},
            "next_fixture": {
                "type": "object",
                "properties": {
                    "opponent": {"type": "string"},
                    "venue": {"type": "string", "enum": ["home", "away"]},
                    "kickoff": {"type": "string", "format": "date-time"},
                },
            },
            "predictions": {
                "type": "object",
                "properties": {
                    "goal_probability": {
                        "type": "object",
                        "properties": {
                            "probability": {"type": "number"},
                            "expected_goals": {"type": "number"},
                            "confidence": {"type": "number"},
                            "odds_estimate": {"type": "integer"},
                            "recommendation": {"type": "string"},
                        },
                    },
                    "assist_probability": {
                        "type": "object",
                        "properties": {
                            "probability": {"type": "number"},
                            "expected_assists": {"type": "number"},
                            "confidence": {"type": "number"},
                        },
                    },
                    "shots_analysis": {
                        "type": "object",
                        "properties": {
                            "expected_shots": {"type": "number"},
                            "expected_on_target": {"type": "number"},
                            "accuracy": {"type": "number"},
                        },
                    },
                    "fpl_points_projection": {
                        "type": "object",
                        "properties": {
                            "expected_points": {"type": "number"},
                            "confidence_level": {"type": "number"},
                        },
                    },
                },
            },
            "form_analysis": {
                "type": "object",
                "properties": {
                    "form_rating": {"type": "number"},
                    "trend": {"type": "string", "enum": ["improving", "stable", "declining"]},
                    "recent_3_match_avg": {"type": "number"},
                    "season_avg": {"type": "number"},
                },
            },
            "injury_risk": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                    "contact_intensity": {"type": "number"},
                    "fatigue_level": {"type": "number"},
                    "recent_injuries": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
    examples=[
        {
            "player_id": "erling-haaland",
            "name": "Erling Haaland",
            "team": "Manchester City",
            "position": "FWD",
            "predictions": {
                "goal_probability": {
                    "probability": 0.52,
                    "expected_goals": 0.72,
                    "confidence": 0.88,
                    "odds_estimate": 52,
                    "recommendation": "BUY at 52¢",
                },
                "assist_probability": {
                    "probability": 0.18,
                    "expected_assists": 0.15,
                },
            },
            "form_analysis": {
                "form_rating": 9.0,
                "trend": "improving",
                "recent_3_match_avg": 8.2,
            },
        }
    ],
)

MARKET_INSIGHTS_RESOURCE = ResourceDefinition(
    name="market_insights",
    uri_template="kalshi://market_insights/{market_type}",
    description=(
        "Market insights combining predictions with odds analysis. "
        "Includes value opportunities, Kelly bet sizing, and risk assessment."
    ),
    schema={
        "type": "object",
        "properties": {
            "market_type": {"type": "string", "enum": ["goals", "outcomes", "btts", "player_props"]},
            "timestamp": {"type": "string", "format": "date-time"},
            "markets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "market_id": {"type": "string"},
                        "event": {"type": "string"},
                        "model_prediction": {"type": "number"},
                        "market_odds": {"type": "number"},
                        "implied_probability": {"type": "number"},
                        "value": {"type": "number"},
                        "kelly_sizing": {
                            "type": "object",
                            "properties": {
                                "kelly_fraction": {"type": "number"},
                                "recommended_stake": {"type": "number"},
                                "expected_value": {"type": "number"},
                            },
                        },
                        "confidence_interval": {
                            "type": "object",
                            "properties": {
                                "lower": {"type": "number"},
                                "upper": {"type": "number"},
                                "confidence_level": {"type": "number"},
                            },
                        },
                        "recommendation": {"type": "string", "enum": ["BUY", "SKIP", "WATCH"]},
                        "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                    },
                },
            },
            "portfolio_summary": {
                "type": "object",
                "properties": {
                    "total_opportunities": {"type": "integer"},
                    "total_recommended_stake": {"type": "number"},
                    "expected_portfolio_value": {"type": "number"},
                    "max_single_position": {"type": "number"},
                },
            },
        },
    },
    examples=[
        {
            "market_type": "goals",
            "timestamp": "2026-08-14T18:00:00Z",
            "markets": [
                {
                    "market_id": "PL_MAN_LIV_goals_2-3",
                    "event": "Manchester City vs Liverpool: 2-3 goals",
                    "model_prediction": 0.22,
                    "market_odds": 4.10,
                    "implied_probability": 0.24,
                    "value": -0.02,
                    "kelly_sizing": {
                        "kelly_fraction": 0.00,
                        "recommended_stake": 0.0,
                    },
                    "recommendation": "SKIP",
                }
            ],
        }
    ],
)


# ============================================================================
# MCP SCHEMA REGISTRY
# ============================================================================

@dataclass
class MCPSchema:
    """Complete MCP schema registry."""
    tools: Dict[str, ToolDefinition]
    resources: Dict[str, ResourceDefinition]
    version: str = "1.0.0"
    description: str = "Football Markets Prediction MCP Schema"

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_resource(self, name: str) -> Optional[ResourceDefinition]:
        """Get resource by name."""
        return self.resources.get(name)

    def list_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """List tools in category."""
        return [t for t in self.tools.values() if t.get("category") == category]

    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all tools."""
        return list(self.tools.values())

    def get_all_resources(self) -> List[ResourceDefinition]:
        """Get all resources."""
        return list(self.resources.values())


# Initialize global schema registry
FOOTBALL_MARKETS_MCP_SCHEMA = MCPSchema(
    tools={
        "predict_match_goals": PREDICT_MATCH_GOALS,
        "calculate_poisson_probabilities": CALCULATE_POISSON_PROBABILITIES,
        "estimate_goal_distribution": ESTIMATE_GOAL_DISTRIBUTION,
        "predict_match_outcome": PREDICT_MATCH_OUTCOME,
        "estimate_home_advantage": ESTIMATE_HOME_ADVANTAGE,
        "calculate_elo_rating": CALCULATE_ELO_RATING,
        "calculate_pythagorean_points": CALCULATE_PYTHAGOREAN_POINTS,
        "predict_goal_scorer_likelihood": PREDICT_GOAL_SCORER_LIKELIHOOD,
        "predict_assist_probability": PREDICT_ASSIST_PROBABILITY,
        "estimate_shots_on_target": ESTIMATE_SHOTS_ON_TARGET,
        "analyze_player_performance": ANALYZE_PLAYER_PERFORMANCE,
        "calculate_btts_probability": CALCULATE_BTTS_PROBABILITY,
        "confidence_interval_prediction": CONFIDENCE_INTERVAL_PREDICTION,
        "apply_kelly_criterion": APPLY_KELLY_CRITERION,
        "get_fpl_team_data": GET_FPL_TEAM_DATA,
        "get_football_data_match_info": GET_FOOTBALL_DATA_MATCH_INFO,
        "schedule_cache_update": SCHEDULE_CACHE_UPDATE,
    },
    resources={
        "match_predictions": MATCH_PREDICTIONS_RESOURCE,
        "player_analysis": PLAYER_ANALYSIS_RESOURCE,
        "market_insights": MARKET_INSIGHTS_RESOURCE,
    },
)


def get_schema() -> MCPSchema:
    """Get the global MCP schema."""
    return FOOTBALL_MARKETS_MCP_SCHEMA


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed tool information."""
    tool = FOOTBALL_MARKETS_MCP_SCHEMA.get_tool(tool_name)
    if not tool:
        return None
    return {
        "name": tool["name"],
        "description": tool["description"],
        "category": tool["category"],
        "inputs": tool["input_schema"],
        "outputs": tool["output_schema"],
        "rate_limit": tool.get("rate_limit"),
    }


if __name__ == "__main__":
    # Print schema information
    schema = get_schema()
    print(f"MCP Schema Version: {schema.version}")
    print(f"Total Tools: {len(schema.tools)}")
    print(f"Total Resources: {len(schema.resources)}")
    print("\nTools by Category:")
    for category in ["goal_prediction", "match_outcomes", "player_props", "data_services"]:
        tools = schema.list_tools_by_category(category)
        print(f"  {category}: {len(tools)} tools")
