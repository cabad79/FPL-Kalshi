# Soccer Analytics: Match Analysis & In-Game Evaluation

**Source**: Soccer Analytics: A Guide to Performance Analysis for Coaches, Managers, and Analysts (Ian Franks & Mike Hughes)

## Overview

Match analysis applies analytical frameworks to evaluate team and individual performance within specific competitive contexts. This document provides systematic approaches to understand what happened in a match, why it happened, and what it means for future performance.

---

## 1. Pre-Match Analysis Framework

### Situational Context Assessment

Before analyzing a match, establish baseline conditions that influence performance.

#### A. Fixture Context Factors

```python
def establish_fixture_context(team_a, team_b, conditions):
    """Define pre-match contextual factors"""
    
    context = {
        'home_away_status': {
            'team_a': 'home',
            'team_b': 'away',
            'home_advantage_factor': 0.15  # Empirical: home teams score 15% more
        },
        
        'recent_form': {
            'team_a_last_5_avg_xG': calculate_average_metric(
                team_a['last_5_matches'], 'xG'
            ),
            'team_a_last_5_avg_xGc': calculate_average_metric(
                team_a['last_5_matches'], 'xG_conceded'
            ),
            'team_b_last_5_avg_xG': calculate_average_metric(
                team_b['last_5_matches'], 'xG'
            ),
            'team_b_last_5_avg_xGc': calculate_average_metric(
                team_b['last_5_matches'], 'xG_conceded'
            ),
            'form_momentum': calculate_form_trajectory(
                team_a['last_10_matches']
            )
        },
        
        'fatigue_factors': {
            'days_since_last_match': conditions['days_rest'],
            'fixture_congestion': count_matches_in_window(
                team_a, days_window=14
            ),
            'accumulated_injuries': estimate_squad_quality_impact(
                team_a['injury_list']
            )
        },
        
        'head_to_head_history': {
            'team_a_avg_goals_vs_b': calculate_h2h_metric(
                team_a, team_b, metric='goals_for'
            ),
            'team_a_avg_conceded_vs_b': calculate_h2h_metric(
                team_a, team_b, metric='goals_conceded'
            ),
            'team_a_win_rate_vs_b': calculate_h2h_win_rate(
                team_a, team_b, at_home=True
            )
        },
        
        'external_conditions': {
            'weather': conditions['weather'],  # Wind, rain impact
            'altitude': conditions['venue_altitude'],
            'crowd_size': conditions['expected_attendance'],
            'crowd_sentiment': determine_crowd_advantage(
                team_a, conditions
            )
        }
    }
    
    return context
```

**Key Context Variables:**
- Home/away advantage: Affects expected goals by 10-20%
- Recent form: Last 5 matches more predictive than season average
- Fatigue: Matches within 72 hours decrease performance 5-15%
- Injuries: Loss of key players impacts specific metrics
- Head-to-head: Historical patterns reveal tactical tendencies

#### B. Expected Performance Baseline

```python
def calculate_baseline_expectations(team_a, team_b, context):
    """Establish performance expectation benchmarks"""
    
    # Base xG calculation (season-to-date)
    team_a_baseline_xG = team_a['season_avg_xG']
    team_b_baseline_xG = team_b['season_avg_xG']
    
    # Adjust for recent form
    form_multiplier_a = (
        context['recent_form']['team_a_last_5_avg_xG'] / 
        team_a_baseline_xG
    )
    form_multiplier_b = (
        context['recent_form']['team_b_last_5_avg_xG'] / 
        team_b_baseline_xG
    )
    
    # Adjust for opponent quality
    opponent_defense_impact_a = (
        1.0 - (team_b['defensive_rating'] * 0.10)
    )
    opponent_defense_impact_b = (
        1.0 - (team_a['defensive_rating'] * 0.10)
    )
    
    # Adjust for fatigue
    fatigue_impact_a = calculate_fatigue_multiplier(
        context['fatigue_factors']['days_since_last_match'],
        context['fatigue_factors']['fixture_congestion']
    )
    
    # Calculate adjusted expectation
    team_a_expected_xG = (
        team_a_baseline_xG * 
        form_multiplier_a * 
        opponent_defense_impact_a * 
        fatigue_impact_a *
        (1 + context['home_away_status'].get('home_advantage_factor', 0))
    )
    
    team_b_expected_xG = (
        team_b_baseline_xG * 
        form_multiplier_b * 
        opponent_defense_impact_b * 
        fatigue_impact_b *
        (1 - context['home_away_status'].get('away_disadvantage_factor', 0))
    )
    
    return {
        'team_a_expected_xG': team_a_expected_xG,
        'team_b_expected_xG': team_b_expected_xG,
        'expected_total_goals': team_a_expected_xG + team_b_expected_xG,
        'expected_winner_prob': calculate_poisson_win_prob(
            team_a_expected_xG, team_b_expected_xG
        )
    }
```

---

## 2. Real-Time Match Monitoring

### Live Analytics Dashboard Framework

Coaches and analysts can monitor performance against expected baselines during match.

#### A. Possession Phase Analysis (Live)

```python
def monitor_possession_efficiency_live(match_events, expected_baseline):
    """Real-time possession quality assessment"""
    
    cumulative_metrics = {
        'elapsed_time': 0,
        'team_a_passes': 0,
        'team_a_pass_completion': 0,
        'team_a_progressive_passes': 0,
        'team_a_xG': 0,
        'team_b_passes': 0,
        'team_b_pass_completion': 0,
        'team_b_xG': 0,
        'possession_transitions': 0,
        'possession_lost_in_final_third': 0
    }
    
    for event in match_events:
        if event['type'] == 'pass':
            team = event['team']
            
            if event['successful']:
                cumulative_metrics[f'{team}_passes'] += 1
                cumulative_metrics[f'{team}_pass_completion'] += 1
                
                if is_progressive_pass(event):
                    cumulative_metrics[f'{team}_progressive_passes'] += 1
            else:
                cumulative_metrics[f'{team}_passes'] += 1
                cumulative_metrics['possession_transitions'] += 1
                
                if event['location_zone'] == 'attacking_third':
                    cumulative_metrics['possession_lost_in_final_third'] += 1
        
        elif event['type'] == 'shot':
            cumulative_metrics[f'{event["team"]}_xG'] += event['xG_value']
        
        cumulative_metrics['elapsed_time'] = event['timestamp']
    
    # Calculate efficiency metrics
    team_a_efficiency = (
        cumulative_metrics['team_a_xG'] / 
        cumulative_metrics['team_a_passes']
        if cumulative_metrics['team_a_passes'] > 0 else 0
    )
    
    team_b_efficiency = (
        cumulative_metrics['team_b_xG'] / 
        cumulative_metrics['team_b_passes']
        if cumulative_metrics['team_b_passes'] > 0 else 0
    )
    
    # Compare to baseline
    team_a_vs_baseline = team_a_efficiency / expected_baseline['team_a_xG_rate']
    team_b_vs_baseline = team_b_efficiency / expected_baseline['team_b_xG_rate']
    
    return {
        'current_metrics': cumulative_metrics,
        'efficiency_vs_baseline': {
            'team_a': team_a_vs_baseline,
            'team_b': team_b_vs_baseline,
            'analysis': (
                'Team A outperforming' if team_a_vs_baseline > 1.1
                else 'Team A underperforming' if team_a_vs_baseline < 0.9
                else 'Team A on track'
            )
        },
        'risk_assessment': assess_match_direction(cumulative_metrics)
    }
```

#### B. Defensive Pressure Monitoring

```python
def monitor_defensive_pressure_live(match_events):
    """Track pressing intensity and effectiveness in real-time"""
    
    pressure_events = []
    
    for event in match_events:
        if event['type'] == 'defensive_action':
            # Time to pressure application (from losing ball)
            response_time = event['response_time']
            
            # Pressure location
            location_zone = event['location_zone']
            
            # Pressure success
            success = event['resulted_in_ball_recovery']
            
            pressure_events.append({
                'timestamp': event['timestamp'],
                'response_time': response_time,
                'location': location_zone,
                'success': success
            })
    
    # Calculate metrics
    pressure_success_rate = (
        sum(1 for p in pressure_events if p['success']) / len(pressure_events)
        if pressure_events else 0
    )
    
    avg_response_time = np.mean([p['response_time'] for p in pressure_events])
    
    # Zone-specific effectiveness
    high_press_success = sum(
        1 for p in pressure_events 
        if p['success'] and p['location'] == 'attacking_third'
    ) / sum(
        1 for p in pressure_events if p['location'] == 'attacking_third'
    ) if any(p['location'] == 'attacking_third' for p in pressure_events) else 0
    
    return {
        'pressure_success_rate': pressure_success_rate,
        'avg_response_time': avg_response_time,
        'high_press_success': high_press_success,
        'pressure_intensity_fatigue': assess_fatigue_buildup(pressure_events),
        'tactical_recommendation': (
            'Increase pressing intensity' if pressure_success_rate > 0.25
            else 'Adjust pressing strategy' if pressure_success_rate < 0.10
            else 'Maintain current pressing'
        )
    }
```

#### C. Formation Stability Tracking

```python
def track_formation_stability_live(player_positions_over_time):
    """Monitor whether team maintains intended formation"""
    
    stability_scores = []
    
    for timestamp, positions in player_positions_over_time.items():
        # Calculate distance of each player from ideal formation position
        deviations = []
        
        for player in positions:
            ideal_position = get_ideal_position(
                player['position_role'],
                current_formation
            )
            
            actual_position = (player['x'], player['y'])
            
            deviation = calculate_distance(actual_position, ideal_position)
            deviations.append(deviation)
        
        # Formation stability score
        avg_deviation = np.mean(deviations)
        max_deviation = np.max(deviations)
        
        stability_score = (
            1.0 - (avg_deviation / 5.0)  # Normalize: 5m = max deviation
        )
        
        stability_scores.append({
            'timestamp': timestamp,
            'stability': max(0, min(1, stability_score)),
            'avg_deviation': avg_deviation,
            'concern_players': [
                p for p, dev in zip(positions, deviations) if dev > 4.0
            ]
        })
    
    return {
        'avg_stability_score': np.mean([s['stability'] for s in stability_scores]),
        'stability_trend': calculate_trend(stability_scores),
        'formation_breakdown_risk': (
            'High' if np.mean([s['stability'] for s in stability_scores[-10:]]) < 0.6
            else 'Normal'
        )
    }
```

---

## 3. Post-Match Analysis

### Complete Match Evaluation Framework

#### A. Result vs. Expected Value Analysis

```python
def analyze_result_vs_expectations(match_data, pre_match_baseline):
    """Determine if result matches, exceeds, or underperforms expectations"""
    
    team_a_expected_xG = pre_match_baseline['team_a_expected_xG']
    team_b_expected_xG = pre_match_baseline['team_b_expected_xG']
    
    team_a_actual_goals = match_data['team_a_goals']
    team_b_actual_goals = match_data['team_b_goals']
    
    team_a_actual_xG = match_data['team_a_xG']
    team_b_actual_xG = match_data['team_b_xG']
    
    # Variance analysis
    analysis = {
        'team_a': {
            'expected_goals': team_a_expected_xG,
            'actual_goals': team_a_actual_goals,
            'expected_xG': team_a_actual_xG,
            'goal_variance': team_a_actual_goals - team_a_expected_xG,
            'conversion_efficiency': (
                team_a_actual_goals / team_a_actual_xG 
                if team_a_actual_xG > 0 else 0
            ),
            'outperformance': (
                'Overperformed' if team_a_actual_goals > team_a_expected_xG + 0.5
                else 'Underperformed' if team_a_actual_goals < team_a_expected_xG - 0.5
                else 'As Expected'
            ),
            'key_finding': (
                'Better finishing than season average' 
                if (team_a_actual_goals / team_a_actual_xG) > (team_a['season_conversion_rate'])
                else 'Worse finishing than season average'
                if (team_a_actual_goals / team_a_actual_xG) < (team_a['season_conversion_rate'])
                else 'Normal finishing'
            )
        },
        'team_b': {
            'expected_goals': team_b_expected_xG,
            'actual_goals': team_b_actual_goals,
            'expected_xG': team_b_actual_xG,
            'goal_variance': team_b_actual_goals - team_b_expected_xG,
            'conversion_efficiency': (
                team_b_actual_goals / team_b_actual_xG 
                if team_b_actual_xG > 0 else 0
            ),
            'outperformance': (
                'Overperformed' if team_b_actual_goals > team_b_expected_xG + 0.5
                else 'Underperformed' if team_b_actual_goals < team_b_expected_xG - 0.5
                else 'As Expected'
            )
        }
    }
    
    # Match result prediction accuracy
    expected_winner = (
        'Team A' if team_a_expected_xG > team_b_expected_xG
        else 'Team B' if team_b_expected_xG > team_a_expected_xG
        else 'Draw'
    )
    
    actual_winner = (
        'Team A' if team_a_actual_goals > team_b_actual_goals
        else 'Team B' if team_b_actual_goals > team_a_actual_goals
        else 'Draw'
    )
    
    analysis['prediction_accuracy'] = {
        'expected_winner': expected_winner,
        'actual_winner': actual_winner,
        'prediction_correct': expected_winner == actual_winner,
        'surprise_factor': abs(
            (team_a_actual_goals - team_a_expected_xG) + 
            (team_b_actual_goals - team_b_expected_xG)
        ) / 2
    }
    
    return analysis
```

#### B. Tactical Execution Evaluation

```python
def evaluate_tactical_execution(match_data, pre_match_plan):
    """Assess how well each team executed their tactical plan"""
    
    evaluation = {
        'formation_adherence': {
            'intended_formation': pre_match_plan['formation'],
            'average_actual_formation': calculate_formation_from_positions(
                match_data['player_positions']
            ),
            'formation_drift': (
                'Significant deviation' 
                if formation_distance > 0.3
                else 'Minor adjustment'
                if formation_distance > 0.1
                else 'Excellent adherence'
            ),
            'formation_distance': formation_distance
        },
        
        'pressing_strategy_execution': {
            'intended_strategy': pre_match_plan['pressing_strategy'],
            'actual_success_rate': match_data['pressure_success_rate'],
            'expected_success_rate': get_position_baseline(
                pre_match_plan['pressing_strategy']
            ),
            'strategy_effective': (
                'Very effective' if match_data['pressure_success_rate'] > 0.25
                else 'Moderately effective' if match_data['pressure_success_rate'] > 0.15
                else 'Ineffective'
            )
        },
        
        'possession_approach': {
            'intended_possession_target': pre_match_plan['possession_target'],
            'actual_possession': match_data['possession_percentage'],
            'possession_vs_plan': (
                match_data['possession_percentage'] - 
                pre_match_plan['possession_target']
            ),
            'assessment': (
                'Exceeded target' 
                if match_data['possession_percentage'] > pre_match_plan['possession_target'] + 5
                else 'Below target' if match_data['possession_percentage'] < pre_match_plan['possession_target'] - 5
                else 'On target'
            )
        },
        
        'attacking_approach': {
            'intended_approach': pre_match_plan['attacking_approach'],
            'actual_shot_volume': match_data['shots_total'],
            'actual_xG': match_data['team_xG'],
            'shot_conversion': match_data['goals'] / match_data['shots_total'] if match_data['shots_total'] > 0 else 0,
            'approach_effectiveness': assess_approach_fit(
                pre_match_plan['attacking_approach'],
                match_data
            )
        }
    }
    
    return evaluation
```

#### C. Player Performance Evaluation

```python
def evaluate_individual_player_performance(
    player_events, 
    player_expected_contribution,
    position_baseline
):
    """Comprehensive single-player performance analysis"""
    
    performance = {
        'playing_time': sum(e['duration'] for e in player_events if e['type'] == 'on_pitch'),
        
        'passing_contribution': {
            'passes_completed': sum(1 for e in player_events if e['type'] == 'pass' and e['successful']),
            'passes_attempted': sum(1 for e in player_events if e['type'] == 'pass'),
            'completion_rate': calculate_metric(player_events, 'pass_completion'),
            'progressive_passes': sum(1 for e in player_events if is_progressive(e)),
            'vs_position_average': (
                calculate_metric(player_events, 'pass_completion') - 
                position_baseline['pass_completion']
            )
        },
        
        'offensive_contribution': {
            'shots': sum(1 for e in player_events if e['type'] == 'shot'),
            'xG': sum(e.get('xG', 0) for e in player_events if e['type'] == 'shot'),
            'key_passes': sum(1 for e in player_events if e['type'] == 'key_pass'),
            'expected_contribution': player_expected_contribution['xG'] + player_expected_contribution['xA']
        },
        
        'defensive_contribution': {
            'tackles': sum(1 for e in player_events if e['type'] == 'tackle' and e['successful']),
            'interceptions': sum(1 for e in player_events if e['type'] == 'interception'),
            'blocks': sum(1 for e in player_events if e['type'] == 'block'),
            'total_defensive_actions': (
                sum(1 for e in player_events if e['type'] in ['tackle', 'interception', 'block'])
            ),
            'duel_success_rate': (
                sum(1 for e in player_events if e['type'] == 'duel' and e['successful']) /
                sum(1 for e in player_events if e['type'] == 'duel')
                if sum(1 for e in player_events if e['type'] == 'duel') > 0 else 0
            )
        },
        
        'overall_rating': calculate_player_rating(player_events, position_baseline),
        
        'performance_vs_baseline': {
            'expected_performance': player_expected_contribution,
            'actual_performance': calculate_actual_contribution(player_events),
            'overperformance': (
                calculate_actual_contribution(player_events) - 
                player_expected_contribution
            ),
            'performance_class': (
                'Elite' if player_rating > position_baseline * 1.3
                else 'Above Average' if player_rating > position_baseline * 1.1
                else 'Average' if abs(player_rating - position_baseline) <= position_baseline * 0.1
                else 'Below Average'
            )
        }
    }
    
    return performance
```

---

## 4. Comparative Match Analysis

### Match-to-Match Trend Analysis

```python
def analyze_season_trends(match_results_history):
    """Identify patterns across multiple matches"""
    
    trends = {
        'attacking_efficiency_trend': calculate_rolling_average(
            [m['xG_conversion'] for m in match_results_history],
            window=5
        ),
        
        'defensive_vulnerability_trend': calculate_rolling_average(
            [m['xG_conceded'] for m in match_results_history],
            window=5
        ),
        
        'possession_trend': calculate_rolling_average(
            [m['possession_percentage'] for m in match_results_history],
            window=5
        ),
        
        'pressing_effectiveness_trend': calculate_rolling_average(
            [m['pressure_success_rate'] for m in match_results_history],
            window=5
        ),
        
        'home_vs_away_performance': {
            'home_avg_xG': np.mean([
                m['xG'] for m in match_results_history if m['is_home']
            ]),
            'away_avg_xG': np.mean([
                m['xG'] for m in match_results_history if not m['is_home']
            ]),
            'home_advantage_factor': (
                np.mean([m['xG'] for m in match_results_history if m['is_home']]) /
                np.mean([m['xG'] for m in match_results_history if not m['is_home']])
            )
        },
        
        'opponent_adjusted_metrics': {
            'xG_vs_top_teams': np.mean([
                m['xG'] for m in match_results_history 
                if m['opponent_rank'] <= 5
            ]),
            'xG_vs_bottom_teams': np.mean([
                m['xG'] for m in match_results_history 
                if m['opponent_rank'] >= 15
            ]),
            'adaptability': (
                'High' if abs(top_vs_bottom_diff) < 0.3
                else 'Low'
            )
        }
    }
    
    return trends
```

---

## 5. Application: FPL & Kalshi Integration

### Using Match Analysis for Prediction Markets

```python
def integrate_match_analysis_for_fpl(
    match_analysis,
    player_performance,
    fixture_difficulty
):
    """Convert match analysis into FPL fantasy points prediction"""
    
    # Attacking potential
    team_xG = match_analysis['team_xG']
    player_xG = player_performance['xG']
    
    goal_probability = (
        (player_xG / team_xG) *  # Player's share
        (1 + fixture_difficulty.get('opponent_weakness', 0)) *
        player_performance['form_multiplier']
    )
    
    # Assist potential
    team_xA = match_analysis['team_xA']
    player_xA = player_performance['xA']
    
    assist_probability = (
        (player_xA / team_xA) * 
        (1 + fixture_difficulty.get('defensive_weakness', 0))
    )
    
    # Clean sheet potential (defenders/GK)
    team_xGc = match_analysis['team_xGc']
    defensive_strength = match_analysis['team_defensive_rating']
    
    clean_sheet_probability = 1 / (1 + np.exp(0.5 * team_xGc / defensive_strength))
    
    # Expected FPL points
    expected_fpl_points = (
        (goal_probability * 5) +  # 5 pts per goal
        (assist_probability * 3) +  # 3 pts per assist
        (clean_sheet_probability * 4) +  # 4 pts clean sheet (defender)
        calculate_appearance_points(match_analysis)
    )
    
    return {
        'goal_probability': goal_probability,
        'assist_probability': assist_probability,
        'clean_sheet_probability': clean_sheet_probability,
        'expected_fpl_points': expected_fpl_points,
        'confidence_level': assess_prediction_confidence(
            match_analysis,
            player_performance
        )
    }

def integrate_match_analysis_for_kalshi(
    match_analysis,
    market_type
):
    """Convert match analysis into Kalshi betting market probability"""
    
    if market_type == 'total_goals_over_2_5':
        # Probability of 3+ goals
        team_a_xG = match_analysis['team_a_xG']
        team_b_xG = match_analysis['team_b_xG']
        total_xG = team_a_xG + team_b_xG
        
        # Poisson distribution for goal probabilities
        prob_3_plus_goals = 1 - (
            poisson.cdf(2, total_xG)
        )
        
        return {
            'market': 'over_2_5_goals',
            'probability': prob_3_plus_goals,
            'confidence': calculate_confidence_from_sample_size(
                match_analysis['sample_size']
            )
        }
    
    elif market_type == 'home_win':
        team_a_xG = match_analysis['team_a_xG']
        team_b_xG = match_analysis['team_b_xG']
        
        # Poisson-based win probability
        win_prob = sum(
            poisson.pmf(a, team_a_xG) * 
            poisson.cdf(a-1, team_b_xG)
            for a in range(0, 10)
        )
        
        return {
            'market': 'home_win',
            'probability': win_prob,
            'value': assess_odds_value(
                win_prob,
                current_market_odds
            )
        }
```

---

## 6. Match Analysis Checklist

### Complete Match Evaluation Form

**Pre-Match Preparation:**
- [ ] Establish fixture context (home/away, fatigue, injuries)
- [ ] Calculate expected performance baselines (xG, possession, shots)
- [ ] Review opponent tactical tendencies
- [ ] Identify key matchups and vulnerabilities
- [ ] Set tactical plan and player roles

**Live Monitoring:**
- [ ] Track possession efficiency vs. baseline
- [ ] Monitor formation stability
- [ ] Record pressing effectiveness
- [ ] Note key tactical adjustments
- [ ] Track individual player performance trajectory

**Post-Match Analysis:**
- [ ] Calculate actual xG/xA vs. expected
- [ ] Evaluate tactical execution
- [ ] Assess individual player performances
- [ ] Compare result to pre-match predictions
- [ ] Identify key moments and turning points
- [ ] Document lessons for future tactics

---

## References

**Franks & Hughes Framework:**
- Chapter 11: Pre-Match Analysis Systems
- Chapter 12: Live Match Monitoring and Adjustment
- Chapter 13: Post-Match Evaluation Frameworks
- Chapter 14: Comparative Analysis Across Seasons

---

*Last Updated: 2026-08-14*
*Ready for Integration: FPL Manager Selection + Kalshi Match Prediction*
