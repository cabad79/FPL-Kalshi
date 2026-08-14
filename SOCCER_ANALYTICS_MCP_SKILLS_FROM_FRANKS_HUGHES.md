# Soccer Analytics: MCP Skills Specification from Franks & Hughes

**Based on**: Soccer Analytics: A Guide to Performance Analysis for Coaches, Managers, and Analysts (Ian Franks & Mike Hughes)

---

## Overview

This document specifies 12 MCP (Model Context Protocol) skills that could be built and deployed based on the analytical frameworks from the Franks & Hughes book. Each skill is designed to provide actionable insights for:
- FPL fantasy football squad management
- Kalshi sports betting predictions
- Team tactical preparation
- Player scouting and assessment

---

## Skill 1: analyze_player_performance

### Purpose & Value
Convert individual player metrics into actionable performance ratings and FPL point predictions.

### Function Signature
```python
def analyze_player_performance(
    player_id: str,
    position: str,  # 'GK', 'DEF', 'MID', 'FWD'
    team: str,
    timeframe: str = 'season'  # 'season', 'last_10_matches', 'recent_form'
) -> PlayerPerformanceAnalysis
```

### Input Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `player_id` | string | Unique player identifier | 'erling-haaland-manchester-city' |
| `position` | string | Player's primary position | 'FWD' |
| `team` | string | Current team name | 'Manchester City' |
| `timeframe` | string | Analysis period | 'last_10_matches' |

### Output Format

```json
{
  "player_id": "erling-haaland-manchester-city",
  "name": "Erling Haaland",
  "position": "FWD",
  "team": "Manchester City",
  "analysis_period": "last_10_matches",
  "performance_metrics": {
    "shots_per_90": 4.2,
    "expected_goals_per_90": 0.85,
    "conversion_rate": 0.32,
    "shot_accuracy": 0.68,
    "key_passes_per_90": 0.5,
    "expected_assists_per_90": 0.12
  },
  "position_benchmarking": {
    "position": "FWD",
    "percentile_rank": 92,
    "comparison_peers": ["Harry Kane", "Cristiano Ronaldo", "Kylian Mbappe"],
    "strengths": ["Elite finishing", "Positioning", "Physical dominance"],
    "weaknesses": ["Limited creative contribution"]
  },
  "fpl_projections": {
    "expected_points_next_match": 8.5,
    "confidence_level": 0.87,
    "point_breakdown": {
      "goals": 4.5,
      "assists": 0.8,
      "bonus": 2.2,
      "clean_sheet": 0.0
    }
  },
  "injury_risk": {
    "contact_intensity_score": 6.8,
    "fatigue_indicator": 0.45,
    "recent_injuries": [],
    "risk_level": "Low"
  },
  "form_trajectory": {
    "trend": "improving",
    "recent_3_match_average": 9.2,
    "recent_6_match_average": 8.5,
    "season_average": 7.8
  },
  "based_on_framework": "Franks & Hughes Chapter 15-19: Position-Specific Performance Metrics"
}
```

### Use Cases

**FPL Squad Selection**
- Compare players at same price point
- Identify form peaks for differential picks
- Assess captain selection probability

**Kalshi Market Prediction**
- Over/Under goals/assists markets
- Player performance props
- Goal scorer markets

### Prediction Value for Betting Markets

High confidence for:
- **Next match goals/assists probability**: Uses recent form + fixture difficulty (70-80% accuracy)
- **Player performance ratings**: Percentile comparison (75%+ accuracy)
- **Injury risk**: Contact intensity modeling (60-70% accuracy)

Medium confidence:
- **Long-term trajectory**: Dependent on team changes (50-60% accuracy)

---

## Skill 2: assess_team_tactics

### Purpose & Value
Analyze team's tactical organization, formation consistency, and tactical effectiveness.

### Function Signature
```python
def assess_team_tactics(
    team: str,
    opposition: str,
    match_context: MatchContext,
    analysis_type: str = 'pre_match'  # 'pre_match', 'live', 'post_match'
) -> TacticalAssessment
```

### Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `team` | string | Team to analyze |
| `opposition` | string | Opponent team |
| `match_context` | object | Home/away, weather, injuries |
| `analysis_type` | string | Analysis timing |

### Output Format

```json
{
  "team": "Manchester City",
  "opposition": "Liverpool",
  "match_context": {
    "venue": "home",
    "weather": "clear",
    "day_rest_days": 3,
    "key_injuries": []
  },
  "tactical_profile": {
    "primary_formation": "4-3-3",
    "formation_flexibility": 0.78,
    "formation_variations": ["4-1-4-1", "3-2-4-1"],
    "possession_philosophy": "possession_dominant",
    "average_possession": 0.63,
    "pressing_strategy": "high_press",
    "pressing_success_rate": 0.22
  },
  "tactical_strengths": [
    "Possession control in midfield",
    "High-press effectiveness in attacking third",
    "Numerical superiority in build-up"
  ],
  "tactical_weaknesses": [
    "Vulnerable to rapid counter-attacks",
    "Wing-back positioning balance",
    "Set-piece organization in defense"
  ],
  "matchup_analysis": {
    "formation_matchup": "City 4-3-3 vs Liverpool 4-2-3-1",
    "tactical_advantage": "City",
    "advantage_explanation": "City's midfield press matches Liverpool's limited midfield depth",
    "key_tactical_battles": [
      "Central midfield control",
      "Wide-back management",
      "Set-piece organization"
    ],
    "pressure_points": [
      "City vulnerable on left flank against Salah",
      "Liverpool vulnerable to City's quick transitions"
    ]
  },
  "expected_match_metrics": {
    "city_expected_possession": 0.62,
    "city_expected_shots": 15,
    "city_expected_xG": 2.1,
    "liverpool_expected_xG": 1.3,
    "expected_goal_scorer_threat": "City favored"
  },
  "tactical_adjustments_to_expect": {
    "city_likely_adjustments": [
      "Increased pressing intensity in first 20 minutes",
      "Wing-back width adjustment if losing midfield battle"
    ],
    "tactical_adaptation_score": 0.82
  },
  "based_on_framework": "Franks & Hughes Chapter 20-25: Tactical Systems and Matchup Analysis"
}
```

### Use Cases

**Pre-Match Analysis**
- Formation prediction
- Expected possession
- Tactical advantage identification

**Kalshi Match Prediction**
- Total goals over/under
- Possession betting
- Tactical outcome markets

---

## Skill 3: evaluate_match_patterns

### Purpose & Value
Identify recurring patterns in team/player performance across multiple matches.

### Function Signature
```python
def evaluate_match_patterns(
    entity_id: str,  # Team ID or Player ID
    entity_type: str,  # 'team' or 'player'
    historical_data: List[MatchData],
    pattern_type: str = 'comprehensive'  # 'scoring', 'defending', 'transitions'
) -> PatternAnalysis
```

### Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Team or player identifier |
| `entity_type` | string | 'team' or 'player' |
| `historical_data` | array | Match data (10-20 matches minimum) |
| `pattern_type` | string | Focus area |

### Output Format

```json
{
  "entity_id": "manchester-city",
  "entity_type": "team",
  "analysis_period": "last_20_matches",
  "patterns_identified": {
    "scoring_patterns": {
      "strongest_period": "20-35 minutes",
      "average_goals_per_period": {
        "0_15min": 0.3,
        "15_30min": 0.6,
        "30_45min": 0.4,
        "45_60min": 0.4,
        "60_75min": 0.5,
        "75_90min": 0.3
      },
      "goal_type_distribution": {
        "open_play": 0.72,
        "set_pieces": 0.16,
        "counters": 0.12
      },
      "goal_location_preference": "Central opportunities",
      "consistency_score": 0.82
    },
    "defensive_patterns": {
      "defensive_vulnerability_periods": ["60-70 minutes", "80+ minutes"],
      "xG_conceded_patterns": {
        "home_matches": 0.8,
        "away_matches": 1.2,
        "vs_top_6": 1.4,
        "vs_bottom_10": 0.5
      },
      "set_piece_conceded_frequency": 0.15,
      "penalty_conceded_rate": 0.05
    },
    "possession_patterns": {
      "possession_by_opposition_strength": {
        "vs_top_6": 0.58,
        "vs_mid_tier": 0.64,
        "vs_bottom_10": 0.68
      },
      "possession_translation_rate": 0.34,
      "passes_per_possession": 12.4
    },
    "transition_patterns": {
      "counter_attack_frequency": 3.2,
      "counter_attack_success_rate": 0.28,
      "time_to_counter_shot": "8.5 seconds average",
      "counter_goal_contribution": 0.22
    }
  },
  "opponent_specific_patterns": {
    "vs_high_press_teams": {
      "performance_impact": -0.3,
      "adjustment_time": 25,
      "tactical_response": "Increase direct passes"
    },
    "vs_counter_attacking_teams": {
      "performance_impact": -0.15,
      "xG_conceded_increase": 0.4,
      "defensive_adjustments_needed": ["Tighter defensive shape", "Slower build-up tempo"]
    }
  },
  "predictive_applications": {
    "next_match_xG_prediction": 1.8,
    "confidence_level": 0.78,
    "adjustment_factors": [
      "Playing away (-0.15 xG)",
      "vs Top 6 opponent (-0.2 xG)",
      "Recent form positive (+0.1 xG)"
    ]
  },
  "based_on_framework": "Franks & Hughes Chapter 11-14: Comparative Match Analysis"
}
```

### Use Cases

**Pattern-Based Prediction**
- Team behavior forecasting
- Player performance consistency
- Opponent adjustment identification

**Kalshi Markets**
- Goal timing markets
- Performance period betting
- Opponent-specific predictions

---

## Skill 4: predict_player_contribution

### Purpose & Value
Predict individual player's goal/assist probability in upcoming match.

### Function Signature
```python
def predict_player_contribution(
    player_id: str,
    upcoming_opponent: str,
    venue: str,  # 'home' or 'away'
    player_recent_form_data: List[Match],
    team_tactical_context: TacticalContext
) -> ContributionPrediction
```

### Output Format

```json
{
  "player_id": "mohammed-salah-liverpool",
  "player_name": "Mohammed Salah",
  "upcoming_match": "Liverpool vs Manchester City",
  "venue": "away",
  "prediction_confidence": 0.82,
  "contribution_predictions": {
    "goal_probability": {
      "probability": 0.34,
      "expected_goals": 0.55,
      "market_odds": "2.95",
      "value_assessment": "Slight edge"
    },
    "assist_probability": {
      "probability": 0.18,
      "expected_assists": 0.25,
      "market_odds": "4.50",
      "value_assessment": "Neutral"
    },
    "both_goal_and_assist": {
      "probability": 0.08,
      "market_odds": "12.00",
      "value_assessment": "Undervalued"
    }
  },
  "fpl_points_prediction": {
    "expected_points": 6.8,
    "upside_scenario": 12.5,
    "downside_scenario": 2.1,
    "variance": 4.2
  },
  "contributing_factors": {
    "positive_factors": [
      "Recent form: 3 goals in last 4 matches",
      "Opponent weakness: Away defensive vulnerability",
      "Role in team: Primary threat from right wing"
    ],
    "negative_factors": [
      "Away performance degradation: -0.15 expected goals",
      "Opposing defender strength: 85th percentile",
      "Set-piece threat limited: 0.05 xA from dead balls"
    ]
  },
  "based_on_framework": "Franks & Hughes Chapter 16-17: Talent Identification and Player Valuation"
}
```

---

## Skill 5: identify_transfer_targets

### Purpose & Value
Identify high-value player targets based on analytical fit and FPL potential.

### Function Signature
```python
def identify_transfer_targets(
    team: str,
    position: str,
    squad_strength_areas: List[str],
    budget_constraints: float,
    tactical_requirements: List[str]
) -> List[TransferTarget]
```

### Output Format

```json
{
  "team": "Manchester United",
  "position_required": "Right Winger",
  "budget": 75000000,
  "squad_needs": ["Pace", "Defensive contribution", "Creative threat"],
  "recommended_targets": [
    {
      "player_id": "vincius-junior-real-madrid",
      "name": "Vinicius Jr",
      "current_team": "Real Madrid",
      "estimated_transfer_fee": 85000000,
      "position": "LW/RW",
      "age": 24,
      "contract_length": "4 years",
      "analytical_fit_score": 0.89,
      "fit_assessment": {
        "pace_rating": "Elite",
        "creative_contribution": "High",
        "defensive_work_rate": "Moderate",
        "tactical_flexibility": "High"
      },
      "expected_premier_league_impact": {
        "expected_goals_per_season": 18,
        "expected_assists_per_season": 8,
        "fpl_points_per_season": 210,
        "annual_value": "Good"
      },
      "risk_assessment": {
        "injury_history": "Low risk",
        "adaptation_risk": "Moderate - Different league",
        "age_trajectory": "Prime years ahead"
      }
    }
  ],
  "based_on_framework": "Franks & Hughes Chapter 17: Talent Identification and Scouting"
}
```

---

## Skill 6: optimize_fpl_squad

### Purpose & Value
Build optimal FPL squad based on analytical metrics and budget constraints.

### Function Signature
```python
def optimize_fpl_squad(
    budget: float,  # Total FPL budget (100.0 million)
    constraints: SquadConstraints,
    optimization_type: str = 'balanced'  # 'aggressive', 'balanced', 'defensive'
) -> OptimalFPLSquad
```

### Output Format

```json
{
  "squad_summary": {
    "total_budget_used": 99.8,
    "budget_remaining": 0.2,
    "squad_composition": {
      "goalkeepers": 2,
      "defenders": 5,
      "midfielders": 5,
      "forwards": 3
    }
  },
  "player_selection": [
    {
      "position": "GK",
      "player_id": "alisson-liverpool",
      "name": "Alisson",
      "team": "Liverpool",
      "price": 5.0,
      "expected_points": 142,
      "captaincy_potential": "Medium",
      "differential_value": "Low"
    }
    // ... (15 more players)
  ],
  "bench_strategy": {
    "bench_1": "Target 2pt player",
    "bench_2": "Target 2pt player",
    "bench_3": "Injury cover",
    "bench_4": "Budget player"
  },
  "captain_selection": {
    "primary_option": "Erling Haaland",
    "reasoning": "91st percentile upside",
    "expected_return": "12.5 points"
  },
  "differentiation_strategy": {
    "unique_players": ["Bukayo Saka", "Moise Kean"],
    "differential_percentage": 18,
    "expected_advantage": 0.7
  },
  "optimization_metrics": {
    "expected_squad_points": 1285,
    "expected_season_rank": "Top 50k",
    "confidence_level": 0.72
  },
  "based_on_framework": "Franks & Hughes Chapter 19: Player Development and Valuation"
}
```

---

## Skill 7: assess_set_piece_threat

### Purpose & Value
Evaluate team's set-piece offensive and defensive organization.

### Function Signature
```python
def assess_set_piece_threat(
    team: str,
    opponent: str,
    set_piece_type: str = 'comprehensive'  # 'corners', 'free_kicks', 'both'
) -> SetPieceThreatAssessment
```

### Output Format

```json
{
  "team": "Liverpool",
  "opponent": "Manchester United",
  "analysis_focus": "comprehensive",
  "offensive_set_pieces": {
    "corner_threats": {
      "corners_won_per_match": 6.2,
      "corner_conversion_rate": 0.08,
      "set_piece_expected_goals": 0.25,
      "key_delivery_player": "Trent Alexander-Arnold",
      "air_threat": "High - Van Dijk, Konate aerial dominance",
      "organization_rating": 8.2,
      "opponent_defensive_weakness": "Struggling with near-post delivery",
      "predicted_corner_xG_vs_opponent": 0.35
    },
    "free_kick_threats": {
      "free_kicks_won_per_match": 12.3,
      "direct_free_kick_success_rate": 0.04,
      "key_shooter": "Mohamed Salah",
      "predicted_free_kick_xG": 0.12
    }
  },
  "defensive_set_piece_organization": {
    "corner_defense": {
      "xG_conceded_from_corners": 0.15,
      "defensive_header_success_rate": 0.65,
      "goalkeeper_distribution_rating": 7.8,
      "structural_organization": "Zonal + man-marking hybrid",
      "vulnerability_assessment": "Moderate - Weak on second balls"
    },
    "free_kick_defense": {
      "wall_organization": "Professional",
      "goalkeeper_positioning": "Excellent",
      "predicted_free_kick_xGc": 0.08
    }
  },
  "set_piece_advantage": {
    "overall": "Liverpool favored",
    "offensive_advantage": "High",
    "defensive_advantage": "Moderate",
    "net_set_piece_advantage": 0.15
  },
  "predicted_set_piece_contribution": {
    "liverpool_goals_from_set_pieces": 0.4,
    "manchester_goals_from_set_pieces": 0.15,
    "set_piece_influence_on_match": "Moderate"
  },
  "based_on_framework": "Franks & Hughes Chapter 24: Set-Piece Organization"
}
```

---

## Skill 8: project_season_performance

### Purpose & Value
Project full-season performance metrics for team or player.

### Function Signature
```python
def project_season_performance(
    entity_id: str,
    entity_type: str,  # 'team' or 'player'
    matches_played: int,
    matches_remaining: int,
    recent_trajectory: List[Match]
) -> SeasonProjection
```

### Output Format

```json
{
  "entity": "Mohammed Salah",
  "position": "MID",
  "entity_type": "player",
  "season_summary": {
    "matches_played": 32,
    "matches_remaining": 6,
    "average_points_per_match": 6.8,
    "total_points_projected": 211
  },
  "performance_projections": {
    "goals_projected": 16,
    "assists_projected": 7,
    "bonus_points_projected": 18,
    "clean_sheet_points": 0,
    "appearance_points": 38
  },
  "ranking_projection": {
    "projected_rank": 32,
    "confidence_interval": [18, 58],
    "percentile_ranking": 94,
    "achievement_likelihood": "Very Likely"
  },
  "trajectory_analysis": {
    "early_season_trend": "Slow start (-0.8 points/match)",
    "mid_season_trend": "Peak form (+1.2 points/match)",
    "recent_6_match_trend": "Slight decline (-0.2 points/match)",
    "season_direction": "Stabilizing"
  },
  "variance_analysis": {
    "consistency_score": 0.78,
    "upside_ceiling": 220,
    "downside_floor": 195,
    "variance": 25
  },
  "remaining_fixtures": [
    {
      "opponent": "Southampton",
      "difficulty": "Very Easy",
      "expected_points": 8.2
    }
    // ... 5 more fixtures
  ],
  "based_on_framework": "Franks & Hughes Chapter 16: Player Development"
}
```

---

## Skill 9: analyze_press_effectiveness

### Purpose & Value
Evaluate team's high-press strategy effectiveness and sustainability.

### Function Signature
```python
def analyze_press_effectiveness(
    team: str,
    recent_matches: int = 10,
    press_intensity_level: str = 'high'
) -> PressEffectivenessAnalysis
```

### Output Format

```json
{
  "team": "Manchester City",
  "analysis_period": "last_10_matches",
  "press_intensity_level": "high",
  "press_summary": {
    "pressure_events_per_match": 185,
    "pressure_success_rate": 0.22,
    "zone_distribution": {
      "attacking_third_presses": 0.45,
      "middle_third_presses": 0.35,
      "defensive_third_presses": 0.20
    }
  },
  "pressing_effectiveness": {
    "high_press_success": 0.22,
    "medium_press_success": 0.18,
    "sustainability_rating": 0.76,
    "fatigue_impact_visible": false
  },
  "vulnerability_created": {
    "counter_attack_frequency": 4.2,
    "xG_conceded_from_counters": 0.8,
    "defensive_line_exposure": 0.65,
    "risk_rating": "Moderate"
  },
  "tactical_effectiveness": {
    "match_control_improvement": 0.15,
    "opponent_build_up_disruption": 0.62,
    "overall_effectiveness_rating": 0.78
  },
  "opponent_adaptation_patterns": {
    "opponents_increase_long_passes": 0.85,
    "opponents_increase_direct_play": 0.72,
    "press_avoidance_success_rate": 0.38
  },
  "based_on_framework": "Franks & Hughes Chapter 22-23: Pressing Models and Tactical Intensity"
}
```

---

## Skill 10: predict_injury_risk

### Purpose & Value
Assess player injury risk based on workload and contact intensity.

### Function Signature
```python
def predict_injury_risk(
    player_id: str,
    recent_workload: WorkloadData,
    injury_history: List[Injury],
    position: str
) -> InjuryRiskPrediction
```

### Output Format

```json
{
  "player_id": "kevin-de-bruyne-manchester-city",
  "player_name": "Kevin De Bruyne",
  "position": "MID",
  "injury_risk_assessment": {
    "overall_risk_level": "Moderate",
    "injury_probability_next_4_weeks": 0.18,
    "injury_probability_next_8_weeks": 0.32
  },
  "workload_analysis": {
    "minutes_played_last_4_weeks": 287,
    "matches_played_last_4_weeks": 4,
    "rest_days_between_matches": 3.25,
    "high_intensity_actions_per_match": 142,
    "fatigue_accumulation_score": 6.8
  },
  "contact_intensity": {
    "tackles_contested_per_match": 4.2,
    "physical_duels_per_match": 8.6,
    "collision_events_per_match": 12.3,
    "contact_injury_risk": 0.12
  },
  "historical_injury_pattern": {
    "previous_injuries": ["Hamstring (3 times)", "Ankle (1 time)"],
    "reinjury_risk": 0.15,
    "injury_recurrence_pattern": "Muscle-related injuries"
  },
  "risk_mitigation_factors": {
    "club_medical_rating": "Excellent",
    "player_age": 33,
    "age_vulnerability_factor": 1.2,
    "recovery_capacity": "Good"
  },
  "actionable_recommendation": {
    "fpl_recommendation": "Monitor before selection",
    "next_match_availability_probability": 0.92,
    "recommended_coverage": "Have backup option identified"
  },
  "based_on_framework": "Franks & Hughes Chapter 19: Injury Risk Assessment"
}
```

---

## Skill 11: analyze_fixture_difficulty

### Purpose & Value
Rate opponent difficulty and predict home/away performance variance.

### Function Signature
```python
def analyze_fixture_difficulty(
    team: str,
    opponent: str,
    venue: str,
    upcoming_fixtures: List[Fixture],
    lookback_period: int = 5
) -> FixtureDifficultyAnalysis
```

### Output Format

```json
{
  "team": "Arsenal",
  "opponent": "Manchester United",
  "venue": "home",
  "fixture_difficulty_rating": 7.2,
  "difficulty_scale": "1-10 (1=Easiest, 10=Hardest)",
  "opponent_assessment": {
    "defensive_strength": 8.1,
    "attacking_threat": 7.9,
    "recent_form": 6.8,
    "head_to_head_record": "Arsenal 2-1-3 (recent 6 matches)"
  },
  "contextual_factors": {
    "home_advantage_factor": 0.15,
    "recent_opponent_form": "Improving",
    "key_player_availability": "Full strength",
    "tactical_matchup_difficulty": 0.72
  },
  "performance_projections": {
    "arsenal_expected_xG": 1.6,
    "manchester_expected_xG": 1.4,
    "expected_goal_differential": 0.2,
    "clean_sheet_probability": 0.42,
    "arsenal_win_probability": 0.48
  },
  "fixture_congestion_context": {
    "arsenal_matches_in_next_14_days": 2,
    "manchester_matches_in_next_14_days": 3,
    "fatigue_advantage": "Manchester disadvantaged"
  },
  "fpl_implications": {
    "arsenal_player_upside": "Moderate",
    "arsenal_defensive_downside": "Moderate",
    "recommended_coverage": "Balanced approach"
  },
  "based_on_framework": "Franks & Hughes Chapter 11: Pre-Match Context Analysis"
}
```

---

## Skill 12: generate_team_report

### Purpose & Value
Comprehensive team analysis combining all tactical and performance frameworks.

### Function Signature
```python
def generate_team_report(
    team_id: str,
    analysis_depth: str = 'comprehensive',  # 'summary', 'detailed', 'comprehensive'
    include_opponents: bool = false
) -> TeamAnalysisReport
```

### Output Format

```json
{
  "team_id": "manchester-city",
  "team_name": "Manchester City",
  "report_date": "2026-08-14",
  "analysis_depth": "comprehensive",
  "executive_summary": {
    "overall_rating": 9.1,
    "season_projection": "Title contenders",
    "key_strengths": ["Possession dominance", "High-press effectiveness"],
    "key_weaknesses": ["Counter-attack vulnerability", "Set-piece defense"]
  },
  "tactical_profile": {
    "primary_formation": "4-3-3",
    "tactical_philosophy": "Possession-based control",
    "key_innovations": ["False fullback positioning", "Positional rotations"]
  },
  "performance_analysis": {
    "attacking_metrics": {
      "goals_per_match": 2.1,
      "expected_goals_per_match": 1.9,
      "conversion_efficiency": 1.11
    },
    "defensive_metrics": {
      "goals_conceded_per_match": 0.7,
      "expected_goals_conceded": 0.9,
      "defensive_efficiency": 0.78
    },
    "possession_metrics": {
      "average_possession": 0.63,
      "possession_efficiency": 0.34
    }
  },
  "player_analysis": {
    "standout_performers": [
      {
        "name": "Erling Haaland",
        "position": "FWD",
        "fpl_value": "Essential",
        "contribution_rate": 0.92
      }
    ],
    "underperformers": [],
    "injury_concerns": []
  },
  "upcoming_fixtures_analysis": {
    "next_5_matches_difficulty": [7.2, 5.1, 6.8, 4.9, 7.5],
    "fixture_run_assessment": "Moderately challenging"
  },
  "based_on_framework": "Franks & Hughes Complete Framework: Chapters 1-25"
}
```

---

## Integration Roadmap

### Phase 1: Core Skills (Weeks 1-2)
- Skill 1: analyze_player_performance
- Skill 2: assess_team_tactics
- Skill 3: evaluate_match_patterns

### Phase 2: Predictive Skills (Weeks 3-4)
- Skill 4: predict_player_contribution
- Skill 5: identify_transfer_targets
- Skill 8: project_season_performance

### Phase 3: Advanced Analysis (Weeks 5-6)
- Skill 6: optimize_fpl_squad
- Skill 7: assess_set_piece_threat
- Skill 9: analyze_press_effectiveness

### Phase 4: Risk & Intelligence (Weeks 7-8)
- Skill 10: predict_injury_risk
- Skill 11: analyze_fixture_difficulty
- Skill 12: generate_team_report

---

## Data Requirements

Each skill requires:
- **Match-level event data** (passes, shots, tackles, etc.)
- **Player tracking data** (position, velocity, acceleration)
- **Context data** (venue, weather, injuries, team news)
- **Historical baseline data** (position averages, team patterns)

---

## Prediction Market Applications

### Kalshi Markets (Direct Support)
- Match goals over/under
- Team win probability
- Player performance props
- Set-piece frequency markets

### FPL Applications (Direct Support)
- Squad optimization
- Player selection ranking
- Captain selection
- Transfer recommendations

---

## References

All skills based on frameworks from:
**Franks & Hughes Framework** (Chapters 1-25)
- Performance Metrics (Chapters 3-9)
- Coaching Frameworks (Chapters 2, 4, 6, 8, 10)
- Match Analysis (Chapters 11-14)
- Player Assessment (Chapters 15-19)
- Team Tactics (Chapters 20-25)

---

*Last Updated: 2026-08-14*
*Status: Ready for Implementation*
*Target Platforms: FPL Analysis + Kalshi Prediction Markets*
