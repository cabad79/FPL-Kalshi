# Soccer Analytics: Team Tactics & Strategic Systems

**Source**: Soccer Analytics: A Guide to Performance Analysis for Coaches, Managers, and Analysts (Ian Franks & Mike Hughes)

## Overview

Team tactics represent the coordinated strategic deployment of players to maximize strengths and exploit opponent weaknesses. This document provides frameworks for analyzing, predicting, and evaluating tactical execution.

---

## 1. Tactical System Classification

### System 1: Possession-Dominant Systems

#### Characteristics
- High possession percentage (55%+)
- Short passing triangles
- Control-based attacking
- Defensive transition focus

#### Key Metrics
```python
def analyze_possession_dominant_system(match_events, team_data):
    """Analyze possession-based tactical execution"""
    
    analysis = {
        'possession_control': {
            'possession_percentage': calculate_possession(match_events),
            'passes_per_possession': (
                sum(1 for e in match_events if e['type'] == 'pass') /
                count_possession_phases(match_events)
            ),
            'average_possession_length': measure_avg_possession_duration(match_events),
            'pass_completion_rate': calculate_pass_completion(match_events),
            'passing_patterns': analyze_passing_network(match_events)
        },
        
        'ball_progression': {
            'progressive_pass_rate': (
                sum(1 for e in match_events if is_progressive(e)) /
                sum(1 for e in match_events if e['type'] == 'pass')
            ),
            'average_pass_distance': np.mean([
                e.get('pass_distance', 0) for e in match_events if e['type'] == 'pass'
            ]),
            'forward_vs_lateral_passing': measure_pass_directions(match_events),
            'penetration_efficiency': calculate_penetration_rate(match_events)
        },
        
        'attacking_output': {
            'shots_per_possession': (
                sum(1 for e in match_events if e['type'] == 'shot') /
                count_possession_phases(match_events)
            ),
            'xG_per_possession': (
                sum(e.get('xG', 0) for e in match_events if e['type'] == 'shot') /
                count_possession_phases(match_events)
            ),
            'possession_efficiency': (
                xG_total / possession_percentage
            )
        },
        
        'defensive_shape': {
            'defensive_compactness': calculate_defensive_compactness(team_data),
            'defensive_line_height': measure_defensive_line_position(team_data),
            'defensive_width': measure_defensive_width(team_data),
            'vulnerability_to_counters': assess_counter_exposure(
                defensive_shape, team_data
            )
        }
    }
    
    return analysis
```

**Tactical Strengths:**
- Control of rhythm and tempo
- Dictate match flow
- Reduce opponent's scoring opportunities
- Excellent for dominant teams

**Tactical Weaknesses:**
- Vulnerable to quick transitions
- May struggle against compact defenses
- High possession without shots = inefficient
- Fatigue from constant moving

---

### System 2: Counter-Attacking Systems

#### Characteristics
- Lower possession (35-45%)
- Rapid transitions
- Long passes forward
- Compact defensive shapes

#### Key Metrics
```python
def analyze_counter_attacking_system(match_events, team_data):
    """Analyze counter-attacking tactical execution"""
    
    analysis = {
        'defensive_organization': {
            'defensive_line_depth': measure_defensive_line_position(team_data),
            'defensive_compactness': calculate_defensive_compactness(team_data),
            'pressing_approach': 'Medium to Low Press',
            'defensive_actions_per_possession_lost': (
                (tackles + interceptions + blocks) / possessions_lost
            )
        },
        
        'transition_speed': {
            'avg_transition_time': measure_transition_speed(match_events),
            'ball_progression_speed': calculate_ball_progression_velocity(match_events),
            'passes_to_first_shot': (
                sum(1 for e in counter_sequence if e['type'] == 'pass')
                for counter_sequence in identify_counter_attacks(match_events)
            ),
            'counter_success_rate': (
                sum(1 for c in counters if c['resulted_in_shot']) / len(counters)
            )
        },
        
        'attacking_output': {
            'shots_per_counter': calculate_shots_per_counter(match_events),
            'counter_xG': sum(
                e.get('xG', 0) for e in match_events 
                if identify_as_counter_shot(e)
            ),
            'goal_contribution_from_counters': (
                goals_from_counters / total_goals
            ),
            'counter_efficiency': counter_xG / possessions_lost
        },
        
        'possession_recovery': {
            'possession_recovery_rate': measure_possession_recovery(match_events),
            'recovery_location_distribution': analyze_recovery_locations(match_events),
            'recovery_to_shot_time': measure_recovery_to_shot_timing(match_events)
        }
    }
    
    return analysis
```

**Tactical Strengths:**
- Exploit defensive vulnerabilities
- Efficient goal-scoring
- Plays to team's specific strengths
- Demoralize dominant opponents

**Tactical Weaknesses:**
- Limited control of match
- Dangerous if transitions fail
- May allow high xG conceded
- Requires disciplined defense

---

### System 3: High-Pressing Systems

#### Characteristics
- Aggressive ball recovery in opponent's half
- High physical intensity
- Disrupt opponent's build-up
- Risk: Exposed backline

#### Key Metrics
```python
def analyze_high_pressing_system(match_events, team_data):
    """Analyze high-press tactical execution"""
    
    analysis = {
        'pressing_intensity': {
            'pressure_events_per_match': sum(
                1 for e in match_events if e['type'] == 'pressure'
            ),
            'pressure_intensity_per_90': (
                pressure_events / (match_duration / 90)
            ),
            'pressing_zones': {
                'attacking_third_presses': sum(
                    1 for e in match_events 
                    if e['type'] == 'pressure' and e['zone'] == 'attacking_third'
                ),
                'middle_third_presses': sum(
                    1 for e in match_events
                    if e['type'] == 'pressure' and e['zone'] == 'middle_third'
                ),
                'defensive_third_presses': sum(
                    1 for e in match_events
                    if e['type'] == 'pressure' and e['zone'] == 'defensive_third'
                )
            }
        },
        
        'pressing_effectiveness': {
            'pressure_success_rate': (
                sum(1 for e in match_events if e['type'] == 'pressure' and e['successful']) /
                sum(1 for e in match_events if e['type'] == 'pressure')
            ),
            'high_press_success': measure_high_press_success(match_events),
            'pressing_fatigue_curve': calculate_fatigue_impact_over_match(
                match_events
            ),
            'recovery_speed': measure_recovery_from_unsuccessful_pressure(
                match_events
            )
        },
        
        'defensive_vulnerability': {
            'xG_conceded': match_events['team_xG_conceded'],
            'counter_attack_frequency': count_counters_against_press(match_events),
            'defensive_line_exposure': measure_backline_vulnerability(team_data),
            'high_press_risk_score': calculate_high_press_risk(
                xG_conceded, counter_frequency
            )
        },
        
        'recovery_and_transition': {
            'ball_recovery_from_press': (
                sum(1 for e in match_events if e['preceded_by_pressure']) /
                sum(1 for e in match_events if e['type'] == 'pressure')
            ),
            'counter_threat_response': measure_counter_response_time(match_events)
        }
    }
    
    return analysis
```

**Tactical Strengths:**
- Control match momentum
- Win ball in attacking positions
- Prevent opponent's build-up
- Create chances from turnovers

**Tactical Weaknesses:**
- Extremely fatiguing
- Risk if unsuccessful (exposed defense)
- Effective opponents exploit space behind
- May concede high-quality chances

---

## 2. Formation-Specific Tactical Approaches

### 4-4-2 Classic Structure
**Typical Strengths:**
- Defensive stability
- Balanced approach
- Classic organization

**Analytics Focus:**
- Midfield compactness (4-5m depth ideal)
- Striker positioning (6-10m spacing)
- Wing influence (crosses vs. cuts)

```python
def analyze_442_tactical_execution(match_events, team_data):
    """4-4-2 specific analysis"""
    
    return {
        'defensive_structure': {
            'back_line_compactness': measure_back_four_spread(team_data),
            'midfield_depth': measure_distance_defenders_to_midfield(team_data),
            'vulnerability_to_wide_play': assess_wing_back_coverage(team_data)
        },
        'midfield_control': {
            'midfield_density': measure_central_midfield_density(match_events),
            'pass_circulation': analyze_midfield_passing_patterns(match_events),
            'defensive_midfield_effectiveness': measure_defensive_midfielder_performance(
                match_events
            )
        },
        'striking_partnership': {
            'striker_spacing': measure_striker_distance(team_data),
            'combination_play_frequency': count_striker_combinations(match_events),
            'aerial_threat_combined': (
                combined_headers_won / combined_aerial_duels
            )
        }
    }
```

### 3-5-2 Attacking Structure
**Typical Strengths:**
- Central overload
- Wing-back width
- Attacking flexibility

**Analytics Focus:**
- CB communication (wider line)
- Wing-back positioning (offensive vs. defensive balance)
- Central midfield density

### 5-3-2 Defensive Structure
**Typical Strengths:**
- Defensive solidity
- Extra defender in box
- Set-piece organization

**Analytics Focus:**
- Defensive line height (deeper positioning)
- CB coordination (5-player line)
- Attacking transition efficiency

---

## 3. Positional Play & Rotational Movement

### Positional Rotation (Pep Guardiola-style)

**Definition:** Players moving between positions during play to create numerical advantages and confuse opponents

```python
def analyze_positional_rotation(match_events, team_data):
    """Measure positional flexibility and rotation"""
    
    analysis = {
        'position_changes': {
            'players_changing_positions': count_players_changing_positions(
                team_data['player_tracking']
            ),
            'position_changes_per_possession': (
                position_changes / count_possessions(match_events)
            ),
            'average_position_delta': calculate_average_position_movement(team_data),
            'formation_mutability_score': measure_formation_flexibility(team_data)
        },
        
        'numerical_advantages': {
            'overload_frequency': count_overload_situations(match_events),
            'overload_success_rate': (
                successful_overloads / total_overloads
            ),
            'overload_zones': analyze_overload_locations(match_events),
            'passing_options_created': measure_passing_availability_increase(
                match_events, team_data
            )
        },
        
        'opponent_disorientation': {
            'pressing_confusion_events': count_pressing_confusion(match_events),
            'defensive_line_instability': measure_defensive_response_time(
                opponent_events
            ),
            'defensive_efficiency_impact': compare_defensive_metrics_with_standard(
                opponent_events, league_baseline
            )
        }
    }
    
    return analysis
```

---

## 4. Set-Piece Tactical Organization

### Attacking Set-Pieces

#### Corner Kick Strategies

```python
def analyze_corner_kick_tactics(set_piece_events):
    """Analyze corner kick execution and organization"""
    
    analysis = {
        'corner_types': {
            'near_post_corners': sum(1 for sp in set_piece_events if sp['variation'] == 'near_post'),
            'far_post_corners': sum(1 for sp in set_piece_events if sp['variation'] == 'far_post'),
            'short_corners': sum(1 for sp in set_piece_events if sp['variation'] == 'short'),
            'variation_frequency': measure_tactical_variety(set_piece_events)
        },
        
        'delivery_quality': {
            'accuracy': (
                sum(1 for sp in set_piece_events if sp['on_target']) /
                len(set_piece_events)
            ),
            'delivery_zones': analyze_delivery_distribution(set_piece_events),
            'timing_and_pace': measure_delivery_timing(set_piece_events)
        },
        
        'set_piece_organization': {
            'box_occupancy': measure_attacking_players_in_box(set_piece_events),
            'marker_assignments': analyze_defensive_marking(set_piece_events),
            'positioning_efficiency': assess_attacking_positioning_quality(
                set_piece_events
            ),
            'tall_player_utilization': measure_aerial_threat_deployment(
                set_piece_events
            )
        },
        
        'set_piece_efficiency': {
            'conversion_rate': (
                goals_from_set_pieces / set_piece_attempts
            ),
            'expected_goals_from_set_pieces': sum(
                sp.get('xG', 0) for sp in set_piece_events
            ),
            'actual_vs_expected': (
                goals_from_set_pieces / xG_from_set_pieces
            )
        }
    }
    
    return analysis
```

### Defensive Set-Pieces

```python
def analyze_defensive_set_piece_organization(set_piece_events):
    """Analyze defensive organization for opponent set-pieces"""
    
    analysis = {
        'defensive_organization': {
            'first_defender_positioning': measure_first_defender_placement(
                set_piece_events
            ),
            'wall_organization': analyze_wall_structure(set_piece_events),
            'goalkeeper_positioning': assess_goalkeeper_positioning(
                set_piece_events
            ),
            'zonal_vs_man_marking': classify_marking_approach(set_piece_events)
        },
        
        'set_piece_vulnerability': {
            'xG_conceded_from_set_pieces': sum(
                sp.get('xG', 0) for sp in set_piece_events
            ),
            'set_piece_goal_frequency': (
                goals_conceded_from_set_pieces / opponent_set_pieces
            ),
            'defensive_efficiency': calculate_defensive_efficiency(
                xG_conceded, actual_goals_conceded
            )
        }
    }
    
    return analysis
```

---

## 5. Tactical Adjustments & In-Game Changes

### Real-Time Tactical Modifications

```python
def analyze_tactical_adjustments(match_events, coaching_decisions):
    """Evaluate timing and effectiveness of tactical changes"""
    
    adjustments_analysis = {
        'formation_changes': {
            'changes_made': len([e for e in match_events if e['type'] == 'formation_change']),
            'timing_of_changes': [
                e['timestamp'] for e in match_events if e['type'] == 'formation_change'
            ],
            'before_to_after_metrics': {
                'shots_before_change': count_shots_in_window(
                    match_events, start=0, end=first_change_time
                ),
                'shots_after_change': count_shots_in_window(
                    match_events, start=first_change_time, end=match_end
                ),
                'defensive_efficiency_change': calculate_efficiency_change(
                    match_events, first_change_time
                ),
                'possession_change': measure_possession_change(
                    match_events, first_change_time
                )
            }
        },
        
        'pressing_strategy_changes': {
            'pressing_level_changes': identify_pressing_level_changes(match_events),
            'effectiveness_before_after': compare_pressing_effectiveness(
                match_events
            )
        },
        
        'substitution_impact': {
            'substitutions_made': len([e for e in match_events if e['type'] == 'substitution']),
            'substitution_timing': [
                e['timestamp'] for e in match_events if e['type'] == 'substitution'
            ],
            'player_impact': measure_substitution_impact(match_events),
            'tactical_intent': identify_tactical_intent_from_subs(
                coaching_decisions, match_context
            )
        }
    }
    
    return adjustments_analysis
```

---

## 6. Tactical Matchup Analysis

### Tactical Compatibility Assessment

```python
def analyze_tactical_matchup(team_a_tactics, team_b_tactics):
    """Evaluate how tactics interact"""
    
    matchup = {
        'formation_interaction': {
            'team_a_formation': team_a_tactics['formation'],
            'team_b_formation': team_b_tactics['formation'],
            'tactical_compatibility': assess_formation_compatibility(
                team_a_tactics['formation'],
                team_b_tactics['formation']
            )
        },
        
        'possession_battle': {
            'team_a_possession_expectation': team_a_tactics['expected_possession'],
            'team_b_possession_expectation': team_b_tactics['expected_possession'],
            'possession_winner': (
                'Team A' if team_a_tactics['possession_strength'] > team_b_tactics['possession_defense']
                else 'Team B'
            ),
            'expected_possession_distribution': calculate_possession_expectation(
                team_a_tactics, team_b_tactics
            )
        },
        
        'attacking_vs_defensive': {
            'team_a_attacking_efficiency': team_a_tactics['attacking_efficiency'],
            'team_b_defensive_solidity': team_b_tactics['defensive_rating'],
            'attacking_advantage': (
                team_a_tactics['attacking_efficiency'] /
                team_b_tactics['defensive_rating']
            ),
            'expected_goals_team_a': calculate_expected_goals_from_matchup(
                team_a_tactics, team_b_tactics
            )
        },
        
        'transition_advantage': {
            'team_a_transition_speed': team_a_tactics['transition_speed'],
            'team_b_counter_vulnerability': team_b_tactics['counter_vulnerability'],
            'counter_attack_advantage': assess_counter_advantage(
                team_a_tactics, team_b_tactics
            )
        },
        
        'set_piece_advantage': {
            'team_a_set_piece_quality': team_a_tactics['set_piece_efficiency'],
            'team_b_set_piece_defense': team_b_tactics['set_piece_defense'],
            'set_piece_advantage': (
                'Team A' if team_a_tactics['set_piece_efficiency'] > team_b_tactics['set_piece_defense']
                else 'Team B'
            )
        },
        
        'overall_tactical_assessment': {
            'team_a_tactical_advantage': calculate_overall_tactical_advantage(matchup),
            'key_tactical_battlegrounds': identify_key_battles(
                team_a_tactics, team_b_tactics
            ),
            'prediction_based_on_tactics': predict_outcome_from_tactics(matchup)
        }
    }
    
    return matchup
```

---

## 7. Integration with Prediction Markets

### Tactical Prediction of Match Outcomes

```python
def predict_match_from_tactical_analysis(
    team_a_tactical_profile,
    team_b_tactical_profile,
    historical_matchup_data
):
    """Convert tactical analysis into match prediction"""
    
    prediction = {
        'expected_possession': (
            team_a_tactical_profile['possession_strength'] /
            (team_a_tactical_profile['possession_strength'] + 
             team_b_tactical_profile['possession_strength'])
        ),
        
        'expected_goals_team_a': (
            team_a_tactical_profile['attacking_efficiency'] *
            team_a_tactical_profile['attacking_opportunities'] *
            (1 + calculate_tactical_advantage(team_a_tactical_profile, team_b_tactical_profile))
        ),
        
        'expected_goals_conceded_team_a': (
            team_b_tactical_profile['attacking_efficiency'] *
            team_a_tactical_profile['defensive_vulnerability']
        ),
        
        'match_outcome_probabilities': {
            'team_a_win': calculate_win_probability(
                expected_goals_a, expected_goals_b
            ),
            'draw': calculate_draw_probability(
                expected_goals_a, expected_goals_b
            ),
            'team_b_win': calculate_win_probability(
                expected_goals_b, expected_goals_a
            )
        },
        
        'over_under_2_5_goals': calculate_over_under_probability(
            expected_goals_a + expected_goals_b
        ),
        
        'both_teams_to_score': calculate_both_teams_score_probability(
            expected_goals_a, expected_goals_b
        ),
        
        'tactical_factors_influencing_prediction': {
            'formation_advantage': identify_formation_advantage(
                team_a_tactical_profile, team_b_tactical_profile
            ),
            'pressing_effectiveness': assess_pressing_advantage(
                team_a_tactical_profile, team_b_tactical_profile
            ),
            'transition_vulnerability': identify_transition_risks(
                team_a_tactical_profile, team_b_tactical_profile
            ),
            'set_piece_advantage': identify_set_piece_advantage(
                team_a_tactical_profile, team_b_tactical_profile
            )
        }
    }
    
    return prediction
```

---

## 8. Tactical Scouting Report Template

### Team Tactical Profile Assessment

```python
def generate_tactical_profile_report(team_id, season_data):
    """Comprehensive team tactical assessment"""
    
    report = {
        'team_identification': {
            'name': team_data['name'],
            'manager': team_data['manager'],
            'season': season_data['season'],
            'league': team_data['league']
        },
        
        'primary_tactical_system': {
            'formation': identify_primary_formation(season_data),
            'possession_approach': describe_possession_philosophy(season_data),
            'pressing_strategy': describe_pressing_approach(season_data),
            'attacking_style': describe_attacking_approach(season_data),
            'defensive_organization': describe_defensive_shape(season_data)
        },
        
        'tactical_strengths': [],  # List of 3-5 key tactical strengths
        'tactical_weaknesses': [],  # List of 3-5 key tactical weaknesses
        
        'key_players_to_tactical_system': {
            # Link each key player to role in tactical system
        },
        
        'season_tactical_evolution': {
            'early_season_approach': describe_early_season_tactics(season_data),
            'mid_season_adjustments': describe_mid_season_changes(season_data),
            'late_season_approach': describe_late_season_tactics(season_data),
            'overall_trend': assess_tactical_direction(season_data)
        },
        
        'matchup_recommendations': {
            'teams_that_trouble_them': identify_problematic_matchups(team_data),
            'teams_they_trouble': identify_favorable_matchups(team_data),
            'counter_tactical_approaches': suggest_tactical_counters(
                team_data
            )
        }
    }
    
    return report
```

---

## References

**Franks & Hughes Key Chapters:**
- Chapter 20: Formation Analysis and Tactical Systems
- Chapter 21: Possession-Based Tactics
- Chapter 22: Counter-Attacking Systems
- Chapter 23: High-Pressing Approaches
- Chapter 24: Set-Piece Organization
- Chapter 25: Tactical Adjustments and In-Game Management

---

*Last Updated: 2026-08-14*
*Ready for Integration: Kalshi Match Prediction + FPL Formation Selection*
