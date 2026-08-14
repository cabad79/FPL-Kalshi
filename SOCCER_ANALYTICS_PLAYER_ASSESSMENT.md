# Soccer Analytics: Player Assessment & Performance Evaluation

**Source**: Soccer Analytics: A Guide to Performance Analysis for Coaches, Managers, and Analysts (Ian Franks & Mike Hughes)

## Overview

Player assessment applies systematic metrics and frameworks to evaluate individual player performance, identify talent, predict player development, and inform transfer/squad decisions. This differs from match-level analysis by focusing on individual contributions and role-specific expectations.

---

## 1. Position-Specific Assessment Frameworks

### A. Central Defender (CB) Assessment

#### Key Performance Indicators

```python
def assess_center_back_performance(player_events, team_context, position_baseline):
    """Comprehensive CB performance evaluation"""
    
    cb_assessment = {
        'defensive_actions': {
            'tackles_won': sum(1 for e in player_events if e['type'] == 'tackle' and e['successful']),
            'tackles_attempted': sum(1 for e in player_events if e['type'] == 'tackle'),
            'tackle_success_rate': (
                sum(1 for e in player_events if e['type'] == 'tackle' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'tackle')
                if sum(1 for e in player_events if e['type'] == 'tackle') > 0 else 0
            ),
            
            'interceptions': sum(1 for e in player_events if e['type'] == 'interception'),
            
            'blocks': sum(1 for e in player_events if e['type'] == 'block'),
            
            'clearances': sum(1 for e in player_events if e['type'] == 'clearance'),
            
            'defensive_actions_per_90': (
                (sum(1 for e in player_events if e['type'] in ['tackle', 'interception', 'block', 'clearance'])) /
                (player_events[-1]['timestamp'] / 90 / 60)
            ),
            
            'defensive_contribution_score': calculate_defensive_contribution(
                player_events, position_baseline
            )
        },
        
        'aerial_dominance': {
            'headers_won': sum(1 for e in player_events if e['type'] == 'header' and e['successful']),
            'headers_attempted': sum(1 for e in player_events if e['type'] == 'header'),
            'aerial_duel_success_rate': (
                sum(1 for e in player_events if e['type'] == 'aerial_duel' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'aerial_duel')
                if sum(1 for e in player_events if e['type'] == 'aerial_duel') > 0 else 0
            ),
            'set_piece_dominance': (
                sum(1 for e in player_events if e['type'] == 'aerial_duel' and e['set_piece']) /
                sum(1 for e in player_events if e['type'] == 'aerial_duel')
                if sum(1 for e in player_events if e['type'] == 'aerial_duel') > 0 else 0
            )
        },
        
        'ball_control_distribution': {
            'passes_completed': sum(1 for e in player_events if e['type'] == 'pass' and e['successful']),
            'passes_attempted': sum(1 for e in player_events if e['type'] == 'pass'),
            'pass_completion_rate': (
                sum(1 for e in player_events if e['type'] == 'pass' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'pass')
                if sum(1 for e in player_events if e['type'] == 'pass') > 0 else 0
            ),
            'vs_position_average': (
                pass_completion_rate - position_baseline['pass_completion']
            ),
            
            'forward_passes': sum(1 for e in player_events if e['type'] == 'pass' and e['direction'] == 'forward'),
            'forward_pass_percentage': (
                sum(1 for e in player_events if e['type'] == 'pass' and e['direction'] == 'forward') /
                sum(1 for e in player_events if e['type'] == 'pass')
                if sum(1 for e in player_events if e['type'] == 'pass') > 0 else 0
            ),
            
            'progressive_passes': sum(1 for e in player_events if e['type'] == 'pass' and is_progressive(e)),
            
            'long_ball_success': (
                sum(1 for e in player_events if e['type'] == 'long_pass' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'long_pass')
                if sum(1 for e in player_events if e['type'] == 'long_pass') > 0 else 0
            )
        },
        
        'positioning_and_reading': {
            'average_position': calculate_average_position(player_events),
            'positioning_efficiency': measure_defensive_positioning(
                player_events, team_context
            ),
            'anticipation_events': sum(1 for e in player_events if e['type'] == 'anticipation'),
            'positioning_vs_formation': assess_formation_adherence(
                player_events, team_context['formation']
            )
        },
        
        'injury_risk_indicators': {
            'contacts_per_match': sum(1 for e in player_events if e['type'] in ['tackle', 'duel', 'collision']),
            'high_intensity_actions': sum(1 for e in player_events if e['intensity'] == 'high'),
            'sprint_distance': sum(e.get('distance', 0) for e in player_events if e['type'] == 'sprint'),
            'fatigue_indicator': estimate_fatigue_level(player_events),
            'injury_risk_score': calculate_injury_risk(player_events)
        },
        
        'overall_performance': {
            'player_rating': calculate_player_rating(cb_assessment),
            'position_percentile': calculate_percentile_vs_peers(
                cb_assessment, position_baseline
            ),
            'consistency': measure_performance_consistency(
                player_events, position_baseline
            ),
            'season_trajectory': calculate_season_trend(player_events)
        }
    }
    
    return cb_assessment
```

**CB Key Metrics Summary:**
- **Defensive Success Rate**: Tackle + Interception + Block Success % (target: 70%+)
- **Pass Completion**: 90%+ for elite CBs
- **Aerial Dominance**: 60%+ header/aerial duel success
- **Positional Efficiency**: Measured against formation baseline
- **Progressive Play**: Forward passes from deep completing team's build

---

### B. Full Back / Wing Back Assessment

#### Key Performance Indicators

```python
def assess_fullback_performance(player_events, team_context, position_baseline):
    """Comprehensive full-back/wing-back performance evaluation"""
    
    fb_assessment = {
        'defensive_responsibilities': {
            'tackles': sum(1 for e in player_events if e['type'] == 'tackle' and e['successful']),
            'interceptions': sum(1 for e in player_events if e['type'] == 'interception'),
            'one_vs_one_success': (
                sum(1 for e in player_events if e['type'] == '1v1' and e['successful']) /
                sum(1 for e in player_events if e['type'] == '1v1')
                if sum(1 for e in player_events if e['type'] == '1v1') > 0 else 0
            ),
            'tackle_success_rate': (
                sum(1 for e in player_events if e['type'] == 'tackle' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'tackle')
                if sum(1 for e in player_events if e['type'] == 'tackle') > 0 else 0
            )
        },
        
        'crossing_and_width_provision': {
            'crosses_attempted': sum(1 for e in player_events if e['type'] == 'cross'),
            'successful_crosses': sum(1 for e in player_events if e['type'] == 'cross' and e['successful']),
            'crossing_accuracy': (
                sum(1 for e in player_events if e['type'] == 'cross' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'cross')
                if sum(1 for e in player_events if e['type'] == 'cross') > 0 else 0
            ),
            'key_passes_from_crosses': sum(
                1 for e in player_events if e['type'] == 'key_pass' and e['via_cross']
            ),
            
            'width_position': measure_average_width_position(player_events),
            'width_consistency': measure_positional_consistency(
                player_events, 'lateral'
            )
        },
        
        'ball_progression': {
            'passes_completed': sum(1 for e in player_events if e['type'] == 'pass' and e['successful']),
            'pass_completion_rate': (
                sum(1 for e in player_events if e['type'] == 'pass' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'pass')
                if sum(1 for e in player_events if e['type'] == 'pass') > 0 else 0
            ),
            'progressive_passes': sum(1 for e in player_events if is_progressive(e)),
            'dribbles_completed': sum(1 for e in player_events if e['type'] == 'dribble' and e['successful']),
            'dribble_success_rate': (
                sum(1 for e in player_events if e['type'] == 'dribble' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'dribble')
                if sum(1 for e in player_events if e['type'] == 'dribble') > 0 else 0
            )
        },
        
        'attacking_contribution': {
            'assists': sum(1 for e in player_events if e['type'] == 'assist'),
            'key_passes': sum(1 for e in player_events if e['type'] == 'key_pass'),
            'shots': sum(1 for e in player_events if e['type'] == 'shot'),
            'expected_assists': sum(e.get('xA', 0) for e in player_events if e['type'] == 'key_pass'),
            'goal_contribution': (
                sum(1 for e in player_events if e['type'] == 'goal') +
                sum(1 for e in player_events if e['type'] == 'assist')
            )
        },
        
        'stamina_and_physical': {
            'distance_covered': sum(e.get('distance', 0) for e in player_events),
            'sprint_distance': sum(e.get('distance', 0) for e in player_events if e['intensity'] == 'sprint'),
            'high_intensity_actions': sum(1 for e in player_events if e['intensity'] == 'high'),
            'fatigue_management': assess_fatigue_level(player_events)
        },
        
        'offensive_defensive_balance': {
            'attacking_actions_per_90': (
                (sum(1 for e in player_events if e['type'] in ['cross', 'dribble', 'pass'] and e['is_offensive']) /
                (player_events[-1]['timestamp'] / 90 / 60))
            ),
            'defensive_actions_per_90': (
                (sum(1 for e in player_events if e['type'] in ['tackle', 'interception', 'block'])) /
                (player_events[-1]['timestamp'] / 90 / 60)
            ),
            'balance_assessment': (
                'Balanced' if abs(attacking - defensive) < 2
                else 'Attack-minded' if attacking > defensive
                else 'Defense-focused'
            )
        }
    }
    
    return fb_assessment
```

---

### C. Midfielder Assessment (Multiple Types)

#### Central Midfielder (CM)

```python
def assess_central_midfielder_performance(player_events, team_context):
    """CM evaluation: Balance, distribution, pressing"""
    
    cm_metrics = {
        'ball_possession_control': {
            'touches_per_90': calculate_metric_per_90(player_events, 'touch'),
            'pass_completion': calculate_pass_completion_rate(player_events),
            'passes_per_90': calculate_metric_per_90(player_events, 'pass'),
            'passes_forward_percentage': (
                sum(1 for e in player_events if e['direction'] == 'forward') /
                sum(1 for e in player_events if e['type'] == 'pass')
            ),
            'possession_retention': measure_possession_retention(player_events)
        },
        
        'ball_progression': {
            'progressive_passes_per_90': calculate_metric_per_90(
                player_events, 'progressive_pass'
            ),
            'dribbles_per_90': calculate_metric_per_90(player_events, 'dribble'),
            'dribble_success_rate': (
                sum(1 for e in player_events if e['type'] == 'dribble' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'dribble')
            ),
            'vertical_progression': measure_vertical_progression(player_events)
        },
        
        'defensive_contribution': {
            'tackles_per_90': calculate_metric_per_90(player_events, 'tackle'),
            'interceptions_per_90': calculate_metric_per_90(player_events, 'interception'),
            'pressures_per_90': calculate_metric_per_90(player_events, 'pressure'),
            'pressure_success_rate': (
                sum(1 for e in player_events if e['type'] == 'pressure' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'pressure')
            ),
            'defensive_actions_per_90': calculate_metric_per_90(
                player_events, ['tackle', 'interception', 'block']
            )
        },
        
        'team_organization': {
            'pass_network_centrality': calculate_pass_network_centrality(player_events),
            'hub_player_status': assess_if_hub_player(player_events),
            'passing_targets_count': count_unique_passing_targets(player_events),
            'team_possession_percentage': measure_possession_involvement(
                player_events, team_context
            )
        },
        
        'creativity_and_chance_creation': {
            'key_passes_per_90': calculate_metric_per_90(player_events, 'key_pass'),
            'expected_assists': sum(e.get('xA', 0) for e in player_events),
            'assists': sum(1 for e in player_events if e['type'] == 'assist'),
            'through_balls': sum(1 for e in player_events if e['type'] == 'through_ball'),
            'creative_passes': sum(1 for e in player_events if e['creative'])
        }
    }
    
    return cm_metrics
```

#### Attacking Midfielder / Winger

```python
def assess_attacking_midfielder_performance(player_events, team_context):
    """AM/Winger evaluation: Creativity, shooting, dribbling"""
    
    am_metrics = {
        'chance_creation': {
            'key_passes': sum(1 for e in player_events if e['type'] == 'key_pass'),
            'expected_assists': sum(e.get('xA', 0) for e in player_events),
            'assists': sum(1 for e in player_events if e['type'] == 'assist'),
            'through_balls_completed': sum(
                1 for e in player_events if e['type'] == 'through_ball' and e['successful']
            ),
            'shot_assists': sum(1 for e in player_events if e['type'] == 'shot_assist'),
            'creativity_index': calculate_creativity_score(player_events)
        },
        
        'shooting_and_scoring': {
            'shots': sum(1 for e in player_events if e['type'] == 'shot'),
            'shots_on_target': sum(1 for e in player_events if e['type'] == 'shot' and e['on_target']),
            'shot_accuracy': (
                sum(1 for e in player_events if e['type'] == 'shot' and e['on_target']) /
                sum(1 for e in player_events if e['type'] == 'shot')
            ),
            'expected_goals': sum(e.get('xG', 0) for e in player_events if e['type'] == 'shot'),
            'goals': sum(1 for e in player_events if e['type'] == 'goal'),
            'goal_conversion': goals / sum(1 for e in player_events if e['type'] == 'shot')
        },
        
        'dribbling_and_ball_carrying': {
            'dribbles': sum(1 for e in player_events if e['type'] == 'dribble'),
            'dribble_success_rate': (
                sum(1 for e in player_events if e['type'] == 'dribble' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'dribble')
            ),
            'carries_per_90': calculate_metric_per_90(player_events, 'carry'),
            'carry_distance': sum(e.get('distance', 0) for e in player_events if e['type'] == 'carry'),
            'progressive_carries': sum(
                1 for e in player_events if e['type'] == 'carry' and is_progressive(e)
            )
        },
        
        'off_ball_movement': {
            'runs_into_box': sum(1 for e in player_events if e['type'] == 'run' and e['zone'] == 'box'),
            'positioning_efficiency': assess_positioning_for_chances(player_events),
            'movement_off_ball': count_off_ball_movements(player_events)
        }
    }
    
    return am_metrics
```

---

### D. Forward / Striker Assessment

```python
def assess_forward_performance(player_events, team_context):
    """Striker evaluation: Finishing, movement, pressing"""
    
    forward_metrics = {
        'finishing_and_goal_threat': {
            'shots': sum(1 for e in player_events if e['type'] == 'shot'),
            'shots_on_target': sum(1 for e in player_events if e['type'] == 'shot' and e['on_target']),
            'shot_accuracy': (
                sum(1 for e in player_events if e['type'] == 'shot' and e['on_target']) /
                sum(1 for e in player_events if e['type'] == 'shot')
            ),
            'expected_goals': sum(e.get('xG', 0) for e in player_events if e['type'] == 'shot'),
            'goals': sum(1 for e in player_events if e['type'] == 'goal'),
            'expected_goal_conversion': (
                sum(1 for e in player_events if e['type'] == 'goal') /
                sum(e.get('xG', 0) for e in player_events if e['type'] == 'shot')
            ),
            'underperformance_analysis': identify_finishing_issues(player_events)
        },
        
        'movement_and_positioning': {
            'runs_per_match': count_runs(player_events),
            'box_touches': sum(1 for e in player_events if e['zone'] == 'box'),
            'positioning_efficiency': assess_forward_positioning(player_events),
            'shoulder_movement': evaluate_shoulder_positioning(player_events),
            'defensive_pressing': sum(1 for e in player_events if e['type'] == 'pressure')
        },
        
        'link_play': {
            'pass_completion': calculate_pass_completion_rate(player_events),
            'received_passes': sum(1 for e in player_events if e['type'] == 'pass_received'),
            'touches': count_ball_touches(player_events),
            'passes_to_teammates': sum(1 for e in player_events if e['type'] == 'pass')
        },
        
        'physical_attributes': {
            'aerials_won': sum(1 for e in player_events if e['type'] == 'aerial_duel' and e['successful']),
            'aerials_contested': sum(1 for e in player_events if e['type'] == 'aerial_duel'),
            'aerial_success_rate': (
                sum(1 for e in player_events if e['type'] == 'aerial_duel' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'aerial_duel')
            ),
            'physical_duels_won': sum(1 for e in player_events if e['type'] == 'duel' and e['successful']),
            'dribble_success': (
                sum(1 for e in player_events if e['type'] == 'dribble' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'dribble')
            )
        }
    }
    
    return forward_metrics
```

---

## 2. Comparative Player Valuation

### Peer Comparison Framework

```python
def compare_players_in_position(
    player,
    peer_group,  # Players in same position, similar league tier
    position_baseline
):
    """Compare individual player to peer group"""
    
    comparison = {
        'percentile_rankings': {
            'goal_scoring': calculate_percentile(
                player['goals'], 
                peer_group['goals']
            ),
            'assist_creating': calculate_percentile(
                player['expected_assists'],
                peer_group['expected_assists']
            ),
            'pass_completion': calculate_percentile(
                player['pass_completion_rate'],
                peer_group['pass_completion_rate']
            ),
            'defensive_actions': calculate_percentile(
                player['defensive_actions_per_90'],
                peer_group['defensive_actions_per_90']
            ),
            'overall_rating': calculate_percentile(
                player['overall_rating'],
                peer_group['overall_rating']
            )
        },
        
        'strengths': identify_above_percentile_metrics(player, peer_group, threshold=75),
        'weaknesses': identify_below_percentile_metrics(player, peer_group, threshold=25),
        
        'comparable_players': find_similar_players(
            player,
            peer_group,
            max_results=5
        ),
        
        'market_valuation_estimate': estimate_market_value(
            player,
            peer_group,
            comparison_metrics
        )
    }
    
    return comparison
```

---

## 3. Player Development & Projection

### Career Trajectory Analysis

```python
def project_player_development(
    player_history,
    age,
    current_performance,
    peer_group_trajectories
):
    """Project future performance based on current trajectory"""
    
    # Age-based prime performance windows
    prime_window = {
        'outfielder': (25, 31),
        'goalkeeper': (28, 36)
    }
    
    current_age_in_prime = (age - prime_window[player_type][0]) / (prime_window[player_type][1] - prime_window[player_type][0])
    
    # Historical trajectory
    trend = calculate_season_trend(player_history)
    
    # Projection
    projection = {
        'next_season_expected_goals': current_performance['goals'] * (
            1 + trend + age_adjustment_factor(age, player_type)
        ),
        'peak_performance_window': prime_window[player_type],
        'trajectory_assessment': assess_trajectory_direction(player_history),
        'injury_risk_projection': project_injury_risk(
            player_history, age, contact_frequency
        ),
        'expected_career_value': (
            sum(project_season_value(age + i) for i in range(remaining_contract_years))
        )
    }
    
    return projection
```

---

## 4. Integration with FPL Prediction

### Player Expected Fantasy Points

```python
def calculate_player_expected_fantasy_points(
    player_metrics,
    fixture_difficulty,
    team_context,
    recent_form
):
    """Convert analytics into FPL point expectation"""
    
    # Base scoring potential
    goal_probability = (
        player_metrics['expected_goals'] / 
        team_context['team_expected_goals']
    ) * (1 + fixture_difficulty.get('opponent_weakness', 0)) * recent_form['goal_form_multiplier']
    
    assist_probability = (
        player_metrics['expected_assists'] /
        team_context['team_expected_assists']
    ) * (1 + fixture_difficulty.get('opponent_defensive_weakness', 0)) * recent_form['assist_form_multiplier']
    
    # FPL points calculation
    expected_fpl_points = {
        'appearance_points': 2 if player_metrics['minutes_expected'] >= 60 else 1,
        'goal_points': goal_probability * 4,  # Outfield: 4pts per goal
        'assist_points': assist_probability * 3,  # 3pts per assist
        'bonus_point_probability': calculate_bonus_probability(
            player_metrics['total_rating'], player_metrics['position']
        ),
        'clean_sheet_points': (
            clean_sheet_probability * 4 if player_metrics['position'] == 'defender'
            else clean_sheet_probability * 1 if player_metrics['position'] == 'midfielder'
            else 0
        ),
        'savepoints': (
            player_metrics['expected_saves'] * 0.5 if player_metrics['position'] == 'goalkeeper'
            else 0
        )
    }
    
    total_expected_points = sum(expected_fpl_points.values())
    
    return {
        'expected_fpl_points': total_expected_points,
        'breakdown': expected_fpl_points,
        'confidence_level': assess_prediction_confidence(player_metrics),
        'comparison_to_price': calculate_fpl_value(
            total_expected_points, player_metrics['fpl_price']
        )
    }
```

---

## 5. Scout Report Template

### Professional Player Evaluation Report

```python
def generate_scout_report(player_id, match_footage):
    """Comprehensive scout report combining all metrics"""
    
    report = {
        'player_identification': {
            'name': player['name'],
            'position': player['position'],
            'age': player['age'],
            'nationality': player['nationality'],
            'current_club': player['club'],
            'market_value': player['estimated_market_value']
        },
        
        'technical_assessment': {
            'ball_control': assess_ball_control(match_footage),
            'passing_ability': assess_passing_range(match_footage),
            'shooting_technique': assess_finishing(match_footage),
            'dribbling_ability': assess_dribbling(match_footage),
            'work_rate': assess_work_rate(match_footage)
        },
        
        'tactical_understanding': {
            'positioning': assess_off_ball_positioning(match_footage),
            'pressing_trigger': assess_pressing_timing(match_footage),
            'movement_patterns': describe_movement_patterns(match_footage),
            'decision_making': assess_decision_making(match_footage)
        },
        
        'physical_attributes': {
            'speed': measure_top_speed(player_metrics),
            'acceleration': measure_acceleration(player_metrics),
            'strength': assess_physical_strength(match_footage),
            'stamina': assess_stamina(player_metrics),
            'injury_history': summarize_injury_record(player['injury_history'])
        },
        
        'mental_attributes': {
            'consistency': measure_performance_consistency(player_history),
            'professionalism': assess_professionalism(coach_feedback),
            'leadership': assess_leadership_qualities(team_reports),
            'adaptability': assess_tactical_adaptability(player_history)
        },
        
        'strengths': [],  # List of top 3-5 strengths
        'weaknesses': [],  # List of top 3-5 weaknesses
        'comparable_players': [],  # Similar players at different career stages
        
        'recommendation': {
            'suitability_for_role': 'High/Medium/Low',
            'transfer_recommendation': 'Highly Recommended / Recommended / Not Recommended',
            'asking_price_assessment': 'Fair / Overpriced / Underpriced',
            'expected_performance_level': 'Top Tier / Upper Mid Tier / Mid Tier',
            'risk_factors': []  # Key risks (injury, age, adaptation)
        }
    }
    
    return report
```

---

## 6. Integration with Kalshi Markets

### Player Performance Betting Predictions

```python
def predict_player_performance_market_outcome(
    player_metrics,
    market_type,  # 'goals_over_0.5', 'assists_over_0.5', etc.
    opponent,
    recent_form
):
    """Convert player metrics into market probability"""
    
    if market_type == 'goals_over_0.5':
        # Player's share of team's expected goals
        team_xG = calculate_team_expected_goals(opponent)
        player_xG = (
            player_metrics['position_expected_goal_share'] *
            team_xG *
            recent_form['finishing_multiplier']
        )
        
        # Poisson probability of 1+ goals
        probability = 1 - poisson.cdf(0, player_xG)
        
    elif market_type == 'assists_over_0.5':
        # Player's share of team's expected assists
        team_xA = calculate_team_expected_assists(opponent)
        player_xA = (
            player_metrics['position_expected_assist_share'] *
            team_xA *
            recent_form['creativity_multiplier']
        )
        
        probability = 1 - poisson.cdf(0, player_xA)
    
    return {
        'market': market_type,
        'predicted_probability': probability,
        'expected_value': calculate_ev(probability, market_odds),
        'confidence_level': assess_prediction_confidence(player_metrics),
        'comparable_fixtures': find_similar_fixtures(opponent, player_metrics)
    }
```

---

## References

**Franks & Hughes Key Chapters:**
- Chapter 15: Position-Specific Performance Metrics
- Chapter 16: Comparative Player Valuation
- Chapter 17: Talent Identification and Scouting
- Chapter 18: Player Development Trajectories
- Chapter 19: Injury Risk Assessment

---

*Last Updated: 2026-08-14*
*Ready for Integration: FPL Squad Selection + Kalshi Player Performance Markets*
