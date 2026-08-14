# Soccer Analytics: Performance Metrics & Measurement Framework

**Source**: Soccer Analytics: A Guide to Performance Analysis for Coaches, Managers, and Analysts (Ian Franks & Mike Hughes)

## Overview

Performance metrics in soccer analytics provide quantifiable measures of player and team effectiveness. These metrics form the foundation for objective performance assessment, talent evaluation, and tactical analysis.

## Core Performance Categories

### 1. Possession and Ball Control Metrics

#### Definition
Measures of how effectively a team or player controls and uses the ball during match play.

**Key Metrics:**
- **Possession Percentage**: Proportion of time team has ball (contextual - depends on tactical approach)
- **Pass Completion Rate**: Percentage of successful passes to total passes attempted
- **Progressive Passes**: Passes that move the ball significantly closer to opponent's goal
- **Possession in Different Thirds**: 
  - Defensive third
  - Middle third
  - Attacking/Final third
- **Ball Retention Index**: Consecutive passes without losing ball

#### Practical Significance
- High possession with low efficiency = poor tactical execution
- Context-dependent: Defensive teams expect lower possession
- Progressive passes > total passes = attacking intent

#### Formula
```python
# Pass Completion Rate
pass_completion_rate = (successful_passes / total_passes_attempted) * 100

# Progressive Pass Percentage
progressive_pass_ratio = (progressive_passes / total_passes) * 100

# Possession Efficiency
possession_efficiency = (shots_on_target / possession_percentage) * 100
```

---

### 2. Shot & Goal Metrics

#### Definition
Measures of shot-taking quality, volume, and effectiveness.

**Key Metrics:**
- **Shots per Match**: Total shot attempts
- **Shots on Target**: Shots that required goalkeeper intervention
- **Shot Accuracy**: (Shots on Target / Total Shots) × 100
- **Shots per Possession**: Conversion of possession into shooting opportunities
- **Expected Goals (xG)**:
  - Probability-weighted measure of shot quality
  - Based on location, angle, defender proximity
  - 0-1 scale per shot
- **Expected Assists (xA)**: Quality of chance creation

#### Categories by Location
- **Distance bands**: 0-6m, 6-18m, 18m-penalty, outside penalty
- **Central vs. wide**: Positional quality assessment
- **Headed vs. footed**: Different success rates

#### Practical Application
```python
# Expected Goals Calculation (simplified)
def calculate_xG(shot_location, defenders_nearby, shot_type):
    base_xg = {
        'penalty': 0.79,
        'clear_chance': 0.45,
        'half_chance': 0.15,
        'long_range': 0.04
    }
    
    xg = base_xg.get(shot_type, 0.10)
    
    # Adjust for defenders
    defender_factor = 1.0 - (defenders_nearby * 0.08)
    xg *= defender_factor
    
    return min(1.0, max(0.0, xg))

# Team Attacking Efficiency
attacking_efficiency = total_goals / expected_goals_total
```

---

### 3. Passing Network Metrics

#### Definition
Structural analysis of how players connect through passes, revealing team organization and tactical patterns.

**Key Metrics:**
- **Pass Frequency**: Number of passes between specific players
- **Pass Triangulation**: Three-player passing patterns
- **Network Density**: How interconnected the passing network is
- **Centrality Measures**:
  - Node degree: How many teammates a player passes to
  - Betweenness: Player's role in connecting team
  - Closeness: Average distance to other players via passes
- **Pass Directionality**: Forward, lateral, backward distribution

#### Strategic Insights
- Hub players (high centrality) = tactical key players
- Dense networks = flexible, multiple passing options
- Sparse networks = rigid, limited passing variety

#### Code Framework
```python
import networkx as nx

def build_passing_network(match_events):
    """Create pass network graph from match events"""
    G = nx.DiGraph()
    
    for event in match_events:
        if event['type'] == 'pass' and event['successful']:
            passer = event['player_id']
            receiver = event['receiver_id']
            
            # Add edge with pass count as weight
            if G.has_edge(passer, receiver):
                G[passer][receiver]['weight'] += 1
            else:
                G.add_edge(passer, receiver, weight=1)
    
    # Calculate metrics
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    
    return {
        'network': G,
        'degree_centrality': degree_centrality,
        'betweenness_centrality': betweenness,
        'closeness_centrality': closeness,
        'network_density': nx.density(G)
    }
```

---

### 4. Defensive Metrics

#### Definition
Quantitative measures of defensive action, positioning, and effectiveness.

**Key Metrics:**
- **Tackles**: Successful and attempted
- **Interceptions**: Breaking up opponent play
- **Clearances**: Emergency defensive actions
- **Blocked Shots**: Physical shot-blocking
- **Duels Won**: One-on-one contact success rate
- **Pressing Success Rate**: % of aggressive positioning that regains ball
- **Defensive Coverage**: Players positioned between ball and goal

#### Franks & Hughes Framework: Defensive Pressure Stages

**Stage 1 - High Pressing**
- Immediate pressure on ball carrier
- Win ball in attacking third
- Success rate: % ball recovery within 5 seconds of pressure

**Stage 2 - Medium Pressing**
- Controlled pressure in midfield
- Reduce passing options
- Measured by defensive actions per possession lost

**Stage 3 - Deep Defense**
- Set defensive shape
- Prevent penetration
- Measured by successful block rate

#### Implementation
```python
def calculate_defensive_effectiveness(match_data):
    """Comprehensive defensive performance calculation"""
    
    # Pressing intensity
    high_pressure_success = (
        successful_pressures / total_pressure_attempts
    )
    
    # Coverage metrics
    defensive_shape_rating = calculate_defensive_line_positioning(
        player_locations,
        ball_position,
        opponent_positions
    )
    
    # Duel success
    duel_win_rate = successful_duels / total_duels_contested
    
    # Defensive efficiency
    defensive_actions_per_possession_lost = (
        (tackles + interceptions + blocks) / 
        possessions_lost
    )
    
    return {
        'pressure_effectiveness': high_pressure_success,
        'defensive_shape': defensive_shape_rating,
        'duel_success': duel_win_rate,
        'action_efficiency': defensive_actions_per_possession_lost,
        'xG_conceded': expected_goals_conceded
    }
```

---

### 5. Transition Metrics

#### Definition
Measures of effectiveness in transitioning between defense and attack, or maintaining possession during challenges.

**Key Metrics:**
- **Ball Recovery Rate**: % of lost balls regained within X seconds
- **Counter-Attack Efficiency**: Shots/goals from rapid transitions
- **Transition Pass Accuracy**: Pass success during attacks/defenses
- **Time to First Shot**: Speed of transition to goal attempt
- **Press Success Rate**: Successfully regaining ball from aggressive action

**Tactical Transitions:**
1. **Defensive to Offensive**
   - Ball won → Shot in 5-15 seconds
   - Measure: Quick counter success rate
   
2. **Offensive to Defensive**
   - Ball lost → Regain in defensive third
   - Measure: Pressing success in own half

#### Code Example
```python
def analyze_transitions(match_events, time_window=10):
    """Analyze transition effectiveness (seconds)"""
    
    transitions = []
    
    for i, event in enumerate(match_events):
        if event['type'] == 'ball_loss':
            # Find next ball recovery
            for j in range(i, min(i+50, len(match_events))):
                next_event = match_events[j]
                if (next_event['team'] == event['team'] and 
                    next_event['type'] == 'ball_recovery'):
                    
                    time_elapsed = next_event['timestamp'] - event['timestamp']
                    
                    # Check if transition led to shot
                    shot_within_window = False
                    for k in range(j, min(j+20, len(match_events))):
                        if (match_events[k]['type'] == 'shot' and
                            match_events[k]['timestamp'] - event['timestamp'] < time_window):
                            shot_within_window = True
                            break
                    
                    transitions.append({
                        'recovery_time': time_elapsed,
                        'led_to_shot': shot_within_window,
                        'team': event['team']
                    })
                    break
    
    return {
        'avg_recovery_time': np.mean([t['recovery_time'] for t in transitions]),
        'shot_conversion_rate': sum(1 for t in transitions if t['led_to_shot']) / len(transitions),
        'transitions_count': len(transitions)
    }
```

---

### 6. Set-Piece Metrics

#### Definition
Specialized metrics for corners, free kicks, and throw-ins - structured plays with distinct advantages.

**Key Metrics:**
- **Set-Piece Conversion**: Goals / Set-Pieces
- **Expected Goals from Set-Pieces**: xG generated
- **Aerial Duel Success**: Headers won/lost
- **Delivery Accuracy**: Precision of service into box
- **Zonal Organization**: Player positioning during set-pieces

#### Set-Piece Types & Analysis
- **Corner Kicks**: Near post, far post, short variations
- **Free Kicks**: Shooting opportunities vs. delivery positions
- **Throw-Ins**: Quick outlet or build-up option
- **Penalty Kicks**: Simple xG = 0.79 (conversion dependent on taker)

#### Framework
```python
def analyze_set_pieces(match_data):
    """Set-piece efficiency analysis"""
    
    set_piece_analysis = {}
    
    for sp_type in ['corner', 'free_kick', 'throw_in']:
        events = filter(match_data, event_type=sp_type)
        
        conversions = sum(1 for e in events if e['resulted_in_goal'])
        xG = sum(e.get('xG', 0) for e in events)
        accuracy = (
            sum(1 for e in events if e['successful']) / len(events)
            if events else 0
        )
        
        set_piece_analysis[sp_type] = {
            'count': len(events),
            'conversion_rate': conversions / len(events) if events else 0,
            'expected_goals': xG,
            'delivery_accuracy': accuracy,
            'goals_from_xG': conversions / xG if xG > 0 else 0
        }
    
    return set_piece_analysis
```

---

## Integration with Prediction Markets

### FPL Fantasy Points Correlation

**Points System:**
- Clean sheet: 4 pts (defender/GK)
- Goal: 5-10 pts
- Assist: 3-5 pts
- Saves: 0.5 pts per save
- Tackles: 0.5 pts each

**Metrics → FPL Scoring:**
1. **Attacking Metrics** → Goal/Assist probability
   - xG directly predicts goal probability
   - Progressive passes → assist potential
   
2. **Defensive Metrics** → Clean sheets
   - xG Conceded → clean sheet probability
   - Tackle/block rate → defensive solidity
   
3. **Playing Time Risk**:
   - Possession time → match importance
   - Transfer risk (injuries from duels/contacts)

### Kalshi Betting Market Applications

**Prediction Models:**
- Goals/Assists: Use xG/xA plus historical player performance
- Clean Sheets: Use defensive metrics + opponent xG
- Player performance: Combine all metrics for rating

```python
def calculate_performance_probability(
    player_metrics,
    match_context,
    market_type
):
    """Convert metrics to market probabilities"""
    
    if market_type == 'goal':
        # xG-based probability
        base_prob = player_metrics['xG_per_match']
        
        # Historical adjustment
        historical_factor = (
            player_metrics['goals_scored'] / 
            player_metrics['total_xG']
        )
        
        # Matchup adjustment
        opponent_factor = (
            1.0 - (opponent_defense_rating * 0.15)
        )
        
        return min(
            1.0,
            base_prob * historical_factor * opponent_factor
        )
    
    elif market_type == 'clean_sheet':
        # Defensive metric-based
        team_xGc = match_context['opponent_xG']
        team_defensive_rating = player_metrics['team_def_rating']
        
        # Logistic transformation
        clean_sheet_prob = 1 / (
            1 + np.exp(0.5 * team_xGc / team_defensive_rating)
        )
        
        return clean_sheet_prob
```

---

## Practical Application: Match Analysis Workflow

### Pre-Match Analysis
1. **Expected Performance Metrics**
   - Team xG based on shot location model
   - Defensive vulnerability (xG conceded)
   - Possession expectations (tactical approach)

2. **Player Variance**
   - Individual xG contribution
   - Pass completion vs. team average
   - Defensive actions per position

### Live Match Monitoring
- Real-time xG accumulation
- Transition success tracking
- Defensive pressure intensity

### Post-Match Evaluation
- Metric vs. result analysis (why win/loss)
- Over/under-performance
- Injury/fatigue indicators

---

## References

**Franks & Hughes Framework:**
- Chapter 3: Quantifying Possession and Control
- Chapter 5: Offensive Production Metrics
- Chapter 7: Defensive Systems and Measurement
- Chapter 9: Transition Analysis and Tactical Efficiency

**Key Concepts:**
- Expected Goals (xG) model
- Possession-adjusted metrics
- Defensive pressing frameworks
- Set-piece specialization analysis

---

*Last Updated: 2026-08-14*
*Integration Ready: FPL + Kalshi Market Analysis*
