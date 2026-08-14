# Soccer Analytics: Coaching Frameworks & Tactical Systems

**Source**: Soccer Analytics: A Guide to Performance Analysis for Coaches, Managers, and Analysts (Ian Franks & Mike Hughes)

## Overview

Coaching frameworks provide the strategic architecture for how teams organize, train, and execute their tactical plans. Analytics serves as the feedback mechanism for validating or challenging these frameworks.

---

## 1. Formation Analysis & Tactical Structure

### Definition
Formation refers to the positioning organization of outfield players during play, serving as the template for team structure and role definition.

### Common Formations

#### 4-4-2 (Classic)
```
        GK
    1   2   3   4
        5   6   7   8
            9   10
```

**Characteristics:**
- Traditional defensive structure
- 4 defenders in line (prevents offside traps)
- 4 midfielders (balanced width and depth)
- 2 strikers (direct attacking)
- Zonal defensive approach

**Analytics Insights:**
- Defensive compactness: Measure distance between back line and midfield (ideal: 8-12m)
- Midfield control: Central passing concentration
- Striker spacing: Distance between forwards (ideal: 6-10m for combination play)

**Metrics:**
```python
def analyze_4_4_2_structure(player_positions):
    """Evaluate 4-4-2 formation stability"""
    
    defenders = get_defenders(player_positions)  # Positions 1-4
    midfielders = get_midfielders(player_positions)  # Positions 5-8
    strikers = get_strikers(player_positions)  # Positions 9-10
    
    # Defensive line compactness
    def_line_spread = max(x for _, x, _ in defenders) - min(x for _, x, _ in defenders)
    
    # Defensive depth (distance from midfield)
    avg_def_y = np.mean([y for _, _, y in defenders])
    avg_mid_y = np.mean([y for _, _, y in midfielders])
    def_mid_distance = abs(avg_def_y - avg_mid_y)
    
    # Midfield balance (width vs. central)
    mid_width = max(x for _, x, _ in midfielders) - min(x for _, x, _ in midfielders)
    
    # Striker spacing for combination
    striker_distance = np.linalg.norm(
        np.array([strikers[0][1:3]]) - np.array([strikers[1][1:3]])
    )
    
    return {
        'defensive_compactness': def_line_spread,
        'defensive_depth': def_mid_distance,
        'midfield_width': mid_width,
        'striker_spacing': striker_distance,
        'formation_stability': calculate_stability_score(
            def_line_spread, def_mid_distance
        )
    }
```

#### 3-5-2 (Attacking)
- 3 CBs (width defense)
- 5 midfielders (overload middle)
- 2 strikers (direct threat)

**Analysis Focus:**
- Wing-back positioning (must provide width)
- CB communication (wider defensive line)
- Central midfield density

#### 5-3-2 (Defensive)
- 5 defenders (3 CB + 2 WB)
- 3 midfielders
- 2 strikers

**Defensive Benefit:** Extra defender in box, reduces chances conceded
**Cost:** Less attacking width, requires tactical discipline

### Formation Transition Analysis

**Defensive to Attacking:** 4-4-2 → 4-2-4 (wing-backs push up)
- Measure: Time to return defensive shape after possession loss
- Metric: Defensive line displacement rate

**Attacking to Defensive:** Transitional efficiency
- Count: How many possession transitions before formation collapse
- Risk: Exposed backline during recovery

```python
def measure_formation_transition_speed(match_events):
    """Measure how quickly team returns to defensive shape"""
    
    transitions = []
    
    for event in match_events:
        if event['type'] == 'possession_lost':
            # Find when defensive shape re-established
            for future_event in match_events:
                if (future_event['timestamp'] > event['timestamp'] and
                    future_event['type'] == 'defensive_shape_recovery'):
                    
                    recovery_time = (
                        future_event['timestamp'] - event['timestamp']
                    )
                    
                    transitions.append(recovery_time)
                    break
    
    return {
        'avg_recovery_time': np.mean(transitions),
        'recovery_consistency': np.std(transitions),
        'rapid_recoveries': sum(1 for t in transitions if t < 2)
    }
```

---

## 2. Pressing & Defensive Organization

### Pressing Model (Franks & Hughes Framework)

Defensive pressing represents the proactive recovery of ball possession through aggressive positioning.

#### Three Levels of Pressing Intensity

**Level 1: High Press**
- Apply immediate pressure on ball carrier
- Win ball in opponent's half
- Risky: leaves space behind

**Metrics:**
- Pressure success rate: (Ball recovered) / (Pressures applied) × 100
- Typical target: 15-25% success rate
- Timing: < 1 second from losing ball to pressure

```python
def analyze_high_press(match_events):
    """Quantify high-press effectiveness"""
    
    high_press_events = [
        e for e in match_events 
        if e['type'] == 'pressure' and 
           e['location_zone'] == 'opponent_half'
    ]
    
    successful_pressures = sum(
        1 for e in high_press_events 
        if e['resulted_in_ball_recovery']
    )
    
    high_press_success = (
        successful_pressures / len(high_press_events) 
        if high_press_events else 0
    )
    
    # Calculate pressure timing (speed of response)
    pressure_response_times = [
        e['response_time'] for e in high_press_events 
        if e['response_time']
    ]
    
    return {
        'success_rate': high_press_success,
        'avg_response_time': np.mean(pressure_response_times),
        'pressure_intensity': len(high_press_events) / match_duration,
        'fatigue_indicator': calculate_fatigue_decay(high_press_events)
    }
```

**Level 2: Medium Press**
- Controlled pressure in midfield
- Reduce opponent's passing options
- Force plays into wider areas

**Success Metric:** (Passes forced wide / Total passes made by opponent) × 100

**Level 3: Deep Defense**
- Defensive shape protection (often 4-4-2 or 5-3-2)
- Allow possession but prevent penetration
- Focus: Block central passing lanes

**Effectiveness:** xG conceded per shot

---

### Defensive Shape & Spatial Organization

#### Defensive Compactness
Measure of how tightly organized a team's defensive unit is.

**Calculation:**
```python
def calculate_defensive_compactness(player_positions, ball_position):
    """
    Compactness = Width / Depth ratio
    
    Lower ratio = more compact (harder to penetrate)
    Higher ratio = more spread (vulnerable to penetration)
    """
    
    defensive_players = get_players_in_defensive_zone(player_positions)
    
    # Horizontal spread (width)
    x_positions = [p[1] for p in defensive_players]
    width = max(x_positions) - min(x_positions)
    
    # Vertical spread (depth)
    y_positions = [p[2] for p in defensive_players]
    depth = max(y_positions) - min(y_positions)
    
    # Compactness ratio
    compactness = width / depth if depth > 0 else float('inf')
    
    # Ideal ranges by formation
    ideal_compactness = {
        '4-4-2': 1.2,
        '3-5-2': 1.4,
        '5-3-2': 1.1,
        '4-2-3-1': 1.25
    }
    
    return {
        'compactness_ratio': compactness,
        'width': width,
        'depth': depth,
        'deviation_from_ideal': abs(
            compactness - ideal_compactness.get(current_formation)
        ),
        'penetration_vulnerability': calculate_penetration_risk(
            compactness, defensive_players, ball_position
        )
    }
```

**Target Values:**
- Tight defensive: 0.8-1.0 (compact, hard to penetrate)
- Standard: 1.0-1.3 (balanced)
- Spread: 1.3+ (vulnerable to through-balls)

---

## 3. Possession-Based Coaching Model

### Possession as Tactical Control

Rather than purely statistical possession %, Franks & Hughes emphasize **possession with purpose**.

**Three Possession Functions:**

#### A. Possession for Ball Recovery
**Objective:** Maintain possession to rest team and recover tactical shape
**Metric:** Pass completion rate (target: 80%+)
**Duration:** Quick passes, 3-5 pass sequences

```python
def identify_recovery_possession(match_events):
    """Find possession used for recovery/regrouping"""
    
    recovery_possessions = []
    current_sequence = []
    
    for event in match_events:
        if event['type'] == 'pass' and event['successful']:
            current_sequence.append(event)
            
        elif event['type'] in ['lost_ball', 'interception']:
            # Analyze completed sequence
            if len(current_sequence) > 0:
                sequence_analysis = {
                    'pass_count': len(current_sequence),
                    'completion_rate': sum(
                        1 for e in current_sequence if e['successful']
                    ) / len(current_sequence),
                    'avg_pass_length': np.mean([
                        e['pass_distance'] for e in current_sequence
                    ]),
                    'progression_distance': (
                        current_sequence[-1]['end_position'][1] - 
                        current_sequence[0]['start_position'][1]
                    ),
                    'purpose': classify_possession_purpose(
                        current_sequence
                    )
                }
                
                if sequence_analysis['purpose'] == 'recovery':
                    recovery_possessions.append(sequence_analysis)
            
            current_sequence = []
    
    return recovery_possessions
```

#### B. Possession for Penetration
**Objective:** Move ball forward into dangerous areas
**Metric:** Progressive pass %, Forward pass %
**Duration:** Longer sequences (8-15 passes) building to shot

#### C. Possession for Chance Creation
**Objective:** Generate shooting opportunities
**Metric:** Shots per possession, xG per possession
**Duration:** Complex, multi-directional passing

---

## 4. Attack Development Model

### Phases of Attack (Franks & Hughes)

#### Phase 1: Build-Up (Defensive to Midfield)
- Safe, high-completion passes
- Establish numerical superiority in possession
- Duration: First 3-5 passes

**Analysis:**
```python
def analyze_buildup_phase(match_events):
    """Evaluate first phase of team attacks"""
    
    buildup_sequences = []
    
    for sequence in identify_possession_sequences(match_events):
        # Select only initial phase
        if len(sequence) <= 5:
            team = sequence[0]['team']
            
            # Starting zone: defensive/middle third
            start_zone = get_zone(sequence[0]['start_position'])
            if start_zone in ['def_third', 'mid_third']:
                
                buildup_metrics = {
                    'sequence_length': len(sequence),
                    'pass_completion': sum(
                        1 for e in sequence if e['successful']
                    ) / len(sequence),
                    'lateral_distribution': measure_lateral_passes(sequence),
                    'possession_numbers': calculate_possession_advantage(
                        sequence, match_events
                    ),
                    'tempo': measure_pass_tempo(sequence),
                    'progressed_to_mid': (
                        sequence[-1]['end_position'][1] > 40  # Y > 40 = midfield
                    )
                }
                
                buildup_sequences.append(buildup_metrics)
    
    return {
        'avg_sequence_length': np.mean([
            s['sequence_length'] for s in buildup_sequences
        ]),
        'completion_rate': np.mean([
            s['pass_completion'] for s in buildup_sequences
        ]),
        'progression_success': sum(
            1 for s in buildup_sequences if s['progressed_to_mid']
        ) / len(buildup_sequences),
        'possession_advantage': np.mean([
            s['possession_numbers'] for s in buildup_sequences
        ])
    }
```

#### Phase 2: Approach Play (Midfield to Attacking Third)
- Increase tempo
- Search for penetrative passes
- Begin wing crosses or central movements

**Key Metric:** Successful penetrative passes (moves into attacking third)

#### Phase 3: Chance Development (Final Third Operations)
- Create specific scoring opportunities
- Final ball delivery
- Position advantage in box

**Success Metric:** Shots per sequence (target: 0.3-0.5 shots per 5-pass sequence)

#### Phase 4: Finishing (Shooting)
- Execute chance
- Quality of finish (accuracy, power, placement)
- Rebound opportunities

---

## 5. Tactical Transitions & Counter-Attacking

### Rapid Transition Model

**Definition:** Quick movement from defense to attack (or vice versa) within 5-10 seconds

#### Counter-Attack Success Factors

1. **Speed of Ball Movement**
   - Metric: Meters per second of ball progression
   - Target: 3-5 m/s (vs. 1-2 m/s in build-up)

2. **Number of Touches**
   - Fewer touches = faster transition
   - Target: 2-4 touches to enter attacking third

3. **Vertical Spacing**
   - Forward players positioned ahead of ball
   - Metric: Average Y-position of attacking players vs. ball Y

```python
def analyze_counter_attack_efficiency(match_events):
    """Measure rapid transition effectiveness"""
    
    counter_attacks = []
    
    for i, event in enumerate(match_events):
        # Trigger: Ball recovery in defensive/mid third
        if event['type'] == 'ball_recovery' and event['location_zone'] in ['def_third', 'mid_third']:
            
            # Track next 20 events (approximately 30 seconds)
            counter_window = match_events[i:i+20]
            
            # Calculate transition metrics
            ball_positions = [e['ball_position'] for e in counter_window]
            vertical_progression = ball_positions[-1][1] - ball_positions[0][1]
            
            elapsed_time = counter_window[-1]['timestamp'] - event['timestamp']
            ball_speed = vertical_progression / elapsed_time if elapsed_time > 0 else 0
            
            # Check for shot
            shot_in_counter = any(
                e['type'] == 'shot' for e in counter_window
            )
            
            counter_attacks.append({
                'ball_speed': ball_speed,
                'vertical_progression': vertical_progression,
                'passes_in_transition': sum(
                    1 for e in counter_window if e['type'] == 'pass'
                ),
                'resulted_in_shot': shot_in_counter,
                'efficiency': vertical_progression / sum(
                    1 for e in counter_window if e['type'] == 'pass'
                )
            })
    
    return {
        'counter_attack_frequency': len(counter_attacks),
        'avg_ball_speed': np.mean([c['ball_speed'] for c in counter_attacks]),
        'shot_conversion': sum(
            1 for c in counter_attacks if c['resulted_in_shot']
        ) / len(counter_attacks),
        'avg_passes_per_counter': np.mean([
            c['passes_in_transition'] for c in counter_attacks
        ])
    }
```

---

## 6. Player Role Definition & Specialization

### Position-Specific Frameworks

#### Defender Roles

**Center Back (CB)**
- Aerial dominance (heading accuracy %)
- 1v1 defending success rate
- Pass accuracy (95%+ target)
- Defensive action frequency

```python
def evaluate_center_back_performance(player_events):
    """CB-specific performance framework"""
    
    return {
        'aerial_effectiveness': (
            headers_won / headers_contested
        ),
        'defensive_actions': tackles + interceptions + blocks,
        'pass_accuracy': successful_passes / total_passes,
        'positioning_rating': measure_defensive_positioning(player_events),
        'ball_recovery_rate': (
            possessions_recovered / possessions_contested
        ),
        'distribution_progressiveness': (
            progressive_passes / total_passes
        )
    }
```

**Wing Back (WB)**
- Crossing accuracy (when providing width)
- Defensive coverage (distance to CB)
- Offensive involvement (passes received, dribbles)

#### Midfielder Roles

**Central Midfielder (CM)**
- Pass completion (88%+ target)
- Possession retention
- Defensive pressure application
- Progressive passing rate

**Attacking Midfielder (AM)**
- Chance creation (xA)
- Forward pass frequency
- Through-ball success
- Dribbling efficiency

#### Forward Roles

**Striker (ST)**
- Shot frequency and accuracy
- Positional efficiency (xG vs. shots)
- Aerial duels won %
- Movement away from defenders

**Winger (W)**
- Crossing accuracy
- Dribbling past defenders (success %)
- Offensive ground duels
- Cross-box efficiency

---

## 7. Coaching Decision Framework

### Using Analytics to Validate Tactical Decisions

#### Pre-Match Decisions

```python
def pre_match_tactical_analysis(team_profile, opponent_profile, conditions):
    """Recommend formation and pressing strategy"""
    
    # Team strengths
    team_defensive_rating = evaluate_defense_quality(team_profile)
    team_attacking_rating = evaluate_attacking_quality(team_profile)
    
    # Opponent weaknesses
    opponent_defensive_vulnerability = (
        opponent_profile['xG_conceded'] / opponent_profile['matches']
    )
    opponent_high_line_tendency = measure_defensive_line_height(
        opponent_profile['historical_positioning']
    )
    
    # Conditions (home/away, weather, injuries)
    fatigue_factor = estimate_squad_fatigue(conditions['recent_fixtures'])
    
    # Formation recommendation
    if team_attacking_rating > opponent_defensive_rating:
        formation_recommendation = '4-3-3'  # Offensive
    elif team_defensive_rating > opponent_attacking_rating:
        formation_recommendation = '5-4-1'  # Defensive
    else:
        formation_recommendation = '4-4-2'  # Balanced
    
    # Pressing strategy
    if opponent_high_line_tendency > 0.55:
        pressing_strategy = 'high_press'
    else:
        pressing_strategy = 'medium_press'
    
    return {
        'recommended_formation': formation_recommendation,
        'pressing_strategy': pressing_strategy,
        'key_tactical_focus': identify_weakness_to_exploit(
            opponent_profile
        ),
        'risk_assessment': assess_tactical_risk(
            formation_recommendation, opponent_profile
        )
    }
```

#### Live Match Adjustments

**Monitoring Points:**
- If xG > 1.0 without goal: Finishing drill needed
- If xG conceded > 1.0: Defensive shape adjustment
- If possession > 60% but limited shots: Need penetrative passes
- If transition time > 4 seconds: Fatigue or tactical confusion

#### Post-Match Review

**Analysis Checklist:**
1. Did formation execute as planned? (Positioning stability)
2. Was pressing strategy effective? (Success rate analysis)
3. Did key players perform role expectations? (Role-specific metrics)
4. Were tactical adjustments timely and effective? (Event analysis)
5. What adjustment would improve next match? (Comparative analysis)

---

## Integration with Prediction Markets

### Tactical Impact on Betting Markets

**Formation Impact on Goal Markets:**
- 4-4-2: Conservative (lower goal totals)
- 4-3-3: Balanced
- 3-5-2: Attacking (higher goals)
- 5-3-2: Defensive (lower goals, more clean sheets)

**Pressing Strategy Correlation:**
- High press success → More transitions → More goals
- High press failure → Exposed backline → More xG conceded

**Sample Prediction Model:**
```python
def predict_match_outcome(team1, team2):
    """Integration of tactical frameworks into prediction"""
    
    # Formation analysis
    t1_formation = analyze_formation_execution(team1)
    t2_formation = analyze_formation_execution(team2)
    
    # Tactical matchup
    pressing_advantage = calculate_pressing_advantage(
        team1['pressing_strategy'],
        team2['build_up_quality']
    )
    
    # Attack vs Defense
    team1_attacking = evaluate_attacking_quality(team1, t2_formation)
    team2_attacking = evaluate_attacking_quality(team2, t1_formation)
    
    # Expected goal calculation
    team1_xG = (
        team1_attacking * 
        (1 + pressing_advantage * 0.15) *
        formation_adjustment(t1_formation, t2_formation)
    )
    
    team2_xG = (
        team2_attacking * 
        (1 - pressing_advantage * 0.15) *
        formation_adjustment(t2_formation, t1_formation)
    )
    
    return {
        'team1_xG': team1_xG,
        'team2_xG': team2_xG,
        'match_total_goals': team1_xG + team2_xG,
        'team1_win_prob': calculate_poisson_win_prob(team1_xG, team2_xG),
        'under_2_5': calculate_under_probability(team1_xG + team2_xG)
    }
```

---

## References & Framework Sources

**Franks & Hughes Key Chapters:**
- Chapter 2: Formation Analysis and Stability
- Chapter 4: Pressing Models and Defensive Organization
- Chapter 6: Attack Development Phases
- Chapter 8: Player Role Specialization
- Chapter 10: Tactical Coaching Frameworks

---

*Last Updated: 2026-08-14*
*Application: FPL Manager Selection + Kalshi Match Prediction*
