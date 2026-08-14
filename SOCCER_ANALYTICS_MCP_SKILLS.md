# Soccer Analytics MCP Skills Specification

## Overview

This document defines Model Context Protocol (MCP) skills based on ML models from "Soccer Analytics with Machine Learning". These skills enable real-time predictions for sports analytics and betting markets.

---

## 1. Match Prediction Skills

### `predict_match_outcome`

**Purpose**: Predict Home Win / Draw / Away Win probability for upcoming match

**Parameters**:
```python
{
    "home_team": str,              # Team name or ID
    "away_team": str,              # Team name or ID
    "match_date": str,             # ISO format: YYYY-MM-DD
    "league": str,                 # "Premier League", "LaLiga", etc.
    "model_type": str,             # "xgboost", "random_forest", "ensemble"
    "include_probabilities": bool  # Return P(W), P(D), P(L)?
}
```

**Returns**:
```python
{
    "home_team": str,
    "away_team": str,
    "prediction": "W" | "D" | "L",  # Most likely outcome
    "probabilities": {
        "home_win": float,  # 0.0 to 1.0
        "draw": float,
        "away_win": float
    },
    "confidence": float,  # Max probability (0.33 to 1.0)
    "elo_ratings": {
        "home": float,
        "away": float,
        "difference": float
    },
    "home_advantage_estimate": float,  # Expected goals
    "model_accuracy_historical": float,  # e.g., 0.62
    "uncertainty": float,  # Standard deviation of prediction
    "timestamp": str
}
```

**ML Model Used**: XGBoost Classifier (Multiclass)
**Accuracy**: 58-62% on balanced test set
**Features Used**:
- Elo ratings (current)
- Form (last 5 matches)
- Rest days
- Goal difference (last 5)
- Home advantage constant
- Tactical metrics (possession, pressing)

**Use Cases**:
- Match outcome betting (1X2 bets)
- Tournament simulation
- Season projections

**Confidence Intervals**:
- High confidence (P > 0.65): 85-90% accuracy
- Medium confidence (P 0.40-0.65): 50-60% accuracy
- Low confidence (P < 0.40): 35-45% accuracy

---

### `predict_match_goals`

**Purpose**: Predict total goals (Over/Under) and specific team goals

**Parameters**:
```python
{
    "home_team": str,
    "away_team": str,
    "match_date": str,
    "prediction_type": "total" | "home_only" | "away_only" | "both",
    "threshold": float  # e.g., 2.5 for O/U 2.5
}
```

**Returns**:
```python
{
    "match_id": str,
    "predicted_total_goals": float,  # e.g., 2.7
    "predicted_home_goals": float,   # e.g., 1.5
    "predicted_away_goals": float,   # e.g., 1.2
    "over_under_2_5": {
        "prediction": "over" | "under",
        "probability": float,
        "confidence": float
    },
    "over_under_1_5": {...},
    "over_under_3_5": {...},
    "goal_distribution": {
        "0_goals": 0.05,
        "1_goals": 0.15,
        "2_goals": 0.25,
        "3_goals": 0.20,
        "4_goals": 0.15,
        "5plus_goals": 0.20
    }
}
```

**ML Model Used**: XGBoost Poisson Regressor
**Accuracy**:
- O/U 2.5: 56-62%
- O/U 1.5: 60-68%
- O/U 3.5: 72-78%
- MAE: 0.9-1.2 goals

**Features**:
- xG / xGA last 5 matches
- Scoring rate (goals per match)
- Defensive rate (goals conceded)
- Head-to-head historical goals
- Form volatility

---

### `predict_xg_match`

**Purpose**: Predict Expected Goals for teams in upcoming match

**Parameters**:
```python
{
    "home_team": str,
    "away_team": str,
    "match_date": str,
    "include_distribution": bool
}
```

**Returns**:
```python
{
    "home_team": {
        "predicted_xg": float,     # e.g., 1.8
        "xg_percentile": float,    # Rank vs league average
        "xg_volatility": float,    # Standard deviation
        "expected_shot_count": int,
        "expected_shot_quality": float  # Avg xG per shot
    },
    "away_team": {...},
    "match_expected_xg": float,
    "likelihood_high_scoring": float  # P(>2.5 goals)
}
```

**ML Model Used**: Feature engineering + regression
**Accuracy**: Correlates 0.65-0.75 with actual goals

---

## 2. Player Prediction Skills

### `predict_player_performance`

**Purpose**: Predict fantasy points / performance in upcoming match

**Parameters**:
```python
{
    "player_id": str,
    "player_name": str,
    "match_date": str,
    "league": str,
    "prediction_metric": "fantasy_points" | "goals" | "assists" | "minutes",
    "position": str  # "Forward", "Midfielder", "Defender", "Goalkeeper"
}
```

**Returns**:
```python
{
    "player_id": str,
    "player_name": str,
    "team": str,
    "position": str,
    "match": str,  # Opponent
    "prediction": {
        "fantasy_points": float,  # e.g., 5.2
        "goals_probability": float,  # P(score >= 1)
        "assists_probability": float,
        "minutes_expected": float,
        "expected_shots": float
    },
    "confidence": float,
    "form_status": "hot" | "normal" | "cold",
    "injury_risk": float,
    "playing_time_risk": float,  # Substitution risk
    "opponent_difficulty": float  # Defensive strength (1-10)
}
```

**ML Model Used**: XGBoost Regressor per position
**Accuracy by Position**:
| Position | MAE | Accuracy |
|----------|-----|----------|
| Forward | 1.5-2.0 | 40-45% |
| Midfielder | 1.8-2.2 | 38-42% |
| Defender | 1.2-1.6 | 45-50% |
| Goalkeeper | 1.0-1.4 | 50-55% |

**Features**:
- Last 5 match performance (rolling avg)
- Playing time (minutes last 5)
- Position-normalized stats
- Opponent strength (Elo)
- Injury/suspension status
- Form trend (improving/declining)

---

### `predict_goal_probability`

**Purpose**: Binary prediction - will player score in match?

**Parameters**:
```python
{
    "player_id": str,
    "match_date": str,
    "position": str
}
```

**Returns**:
```python
{
    "player_id": str,
    "goal_probability": float,  # 0.0 to 1.0
    "confidence": float,
    "comparable_players": [
        {"player": str, "goal_prob": float, "similarity": float}
    ],
    "historical_rate": float,  # Player's goal rate %
    "opponent_defense_ranking": int  # 1-20 in league
}
```

**ML Model Used**: XGBoost Binary Classifier
**Accuracy**: 10-15% relative improvement over baseline rates

---

### `cluster_similar_players`

**Purpose**: Find comparable players for valuation or recommendation

**Parameters**:
```python
{
    "player_id": str,
    "position": str,
    "league": str,
    "metric_weights": {
        "goals_per_90": 0.3,
        "pass_completion": 0.2,
        "defensive_actions": 0.2,
        "market_value": 0.3
    },
    "n_similar": int  # Return top N similar players
}
```

**Returns**:
```python
{
    "player_id": str,
    "comparable_players": [
        {
            "player_id": str,
            "name": str,
            "similarity_score": float,  # 0.0-1.0
            "stats": {
                "goals_per_90": float,
                "market_value": float,
                "age": int,
                "form": float
            }
        }
    ]
}
```

**ML Model Used**: KNN with custom distance metric
**Distance Metric**: Weighted Euclidean on normalized stats
**Clustering Method**: K-Means for position-specific clusters (3-5 clusters per position)

---

## 3. Betting Market Skills

### `predict_betting_odds`

**Purpose**: Generate fair odds from predicted probabilities

**Parameters**:
```python
{
    "event_type": "match_outcome" | "over_under" | "player_goal",
    "prediction": dict,  # Output from prediction skill
    "market_efficiency": float  # 0.0-1.0, bookmaker margin
}
```

**Returns**:
```python
{
    "fair_odds": {
        "home_win": float,
        "draw": float,
        "away_win": float
    },
    "implied_probability": {
        "home_win": float,
        "draw": float,
        "away_win": float
    },
    "bookmaker_margin": float,
    "recommended_odds": dict  # For fair odds betting exchange
}
```

**Calculation**:
```python
fair_prob = predicted_prob / (1 + bookmaker_margin)
fair_odds = 1 / fair_prob
```

---

### `calculate_expected_value`

**Purpose**: Evaluate bet profitability

**Parameters**:
```python
{
    "predicted_probability": float,  # From model
    "betting_odds": float,            # From bookmaker
    "confidence": float,              # Model confidence
    "bet_type": "win" | "place" | "each_way"
}
```

**Returns**:
```python
{
    "expected_value": float,          # Can be negative
    "expected_value_pct": float,      # EV as percentage
    "kelly_fraction": float,           # Recommended bet size (fraction of bankroll)
    "kelly_fraction_safe": float,     # Half-Kelly (less aggressive)
    "confidence_adjusted_value": float,
    "recommended_action": "strong_buy" | "buy" | "skip" | "avoid",
    "breakeven_probability": float    # P(win) needed for 0 EV
}
```

**Kelly Criterion**:
```
f = (p * odds - 1) / (odds - 1)
Capped at 5% for safety
```

---

### `identify_mispriced_bets`

**Purpose**: Scan multiple matches for edge opportunities

**Parameters**:
```python
{
    "matches": [
        {"home_team": str, "away_team": str, "match_date": str},
        ...
    ],
    "min_ev": float,  # e.g., 0.05 (5% EV threshold)
    "confidence_threshold": float,  # 0.5+
    "bet_type": "match_outcome" | "goals" | "player"
}
```

**Returns**:
```python
{
    "opportunities": [
        {
            "match": str,
            "bet": str,
            "model_prob": float,
            "market_prob": float,
            "odds": float,
            "ev": float,
            "roi_pct": float,
            "confidence": float,
            "rank": int
        }
    ],
    "summary": {
        "total_opportunities": int,
        "avg_ev": float,
        "edge_in_bets": float,
        "expected_roi": float
    }
}
```

---

## 4. Advanced Analysis Skills

### `forecast_goal_probability`

**Purpose**: Predict goal probability at specific time intervals

**Parameters**:
```python
{
    "home_team": str,
    "away_team": str,
    "time_interval": "0-45" | "45-90" | "0-90",
    "team_filter": "both" | "home" | "away",
    "context": {
        "current_score": [int, int],  # [home_goals, away_goals]
        "time_elapsed": int,
        "red_cards": int
    }
}
```

**Returns**:
```python
{
    "time_period": str,
    "probability_home_goal": float,
    "probability_away_goal": float,
    "probability_either_goal": float,
    "expected_goals_first_half": float,
    "expected_goals_second_half": float,
    "goal_timing_distribution": {
        "0-15": float,
        "15-30": float,
        "30-45": float,
        "45-60": float,
        "60-75": float,
        "75-90": float
    }
}
```

**ML Model Used**: Temporal Poisson process
**Features**:
- Current score
- Time elapsed
- Both teams' xG rate
- Momentum (recent action intensity)

---

### `identify_undervalued_players`

**Purpose**: Find players trading below predicted performance value

**Parameters**:
```python
{
    "league": str,
    "position": str,
    "price_range": [float, float],  # Min/max price
    "prediction_horizon": "next_match" | "next_5" | "next_10",
    "ranking_metric": "fantasy_points" | "goals" | "roi"
}
```

**Returns**:
```python
{
    "undervalued_players": [
        {
            "player_id": str,
            "name": str,
            "position": str,
            "current_price": float,
            "predicted_points": float,
            "price_per_point": float,
            "expected_roi": float,
            "confidence": float,
            "reason": str
        }
    ],
    "summary": {
        "avg_value_potential": float,
        "best_opportunity": str,
        "market_inefficiency_score": float
    }
}
```

---

## 5. Skill Configuration

### Priority Levels

**High Priority** (Real-time, production):
- predict_match_outcome
- predict_match_goals
- calculate_expected_value

**Medium Priority** (Near real-time):
- predict_player_performance
- predict_goal_probability

**Lower Priority** (Batch/analysis):
- cluster_similar_players
- identify_undervalued_players
- forecast_goal_probability

---

## 6. Performance Benchmarks

| Skill | Latency | Accuracy | QPS |
|-------|---------|----------|-----|
| predict_match_outcome | 50ms | 62% | 1000 |
| predict_match_goals | 40ms | 60% | 1000 |
| predict_xg_match | 30ms | 0.70 corr | 2000 |
| predict_player_performance | 100ms | 43% | 500 |
| calculate_expected_value | 10ms | - | 10000 |
| identify_mispriced_bets | 5s | - | 10 |

---

## 7. Error Handling

```python
{
    "error": str,
    "error_code": str,
    "error_message": str,
    "possible_causes": [str],
    "recovery_suggestion": str
}
```

**Common Errors**:
- `MISSING_DATA`: Player/team not found
- `INSUFFICIENT_HISTORY`: Not enough historical matches
- `MODEL_STALE`: Model needs retraining
- `INVALID_ODDS`: Odds out of reasonable range

---

## 8. Rate Limits & Usage

- Real-time skills: 1000 QPS per skill
- Batch skills: 100 QPS
- Concurrent predictions: 10 per worker
- Monthly API calls: 100M (adjustable)

---

## 9. Accuracy Expectations

Users should understand:
1. **No model is 100% accurate** - soccer has inherent uncertainty
2. **Variance in accuracy** - performance varies by match type
3. **Model degradation** - accuracy decreases over time (concept drift)
4. **Ensemble importance** - single models less reliable than ensemble
5. **Calibration matters** - probabilities should be reliable for betting

---

## Integration Example

```python
from soccer_analytics_mcp import SoccerAnalyticsClient

client = SoccerAnalyticsClient(api_key="your-key")

# Get match prediction
match_pred = client.predict_match_outcome(
    home_team="Manchester City",
    away_team="Liverpool",
    match_date="2024-09-15",
    model_type="ensemble"
)

# Get player prediction
player_pred = client.predict_player_performance(
    player_name="Erling Haaland",
    match_date="2024-09-15",
    position="Forward"
)

# Calculate betting value
ev = client.calculate_expected_value(
    predicted_probability=match_pred['probabilities']['home_win'],
    betting_odds=1.95,
    confidence=match_pred['confidence']
)

if ev['expected_value'] > 0.05:
    print(f"Profitable bet! EV: {ev['expected_value_pct']:.1%}")
```

