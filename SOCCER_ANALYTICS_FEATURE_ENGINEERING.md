# Soccer Analytics: Feature Engineering for ML Models

## Overview

Feature engineering transforms raw soccer data into predictive signals. Research shows 70% of model improvement comes from features, not algorithms. This guide covers practical feature creation for prediction markets.

---

## 1. Performance Features

### 1.1 Scoring Performance

**Goals For (GF)** and **Goals Against (GA)**

```python
# Calculate from event data
import pandas as pd

# Match-level aggregation
team_stats = matches.groupby('team').agg({
    'goals_scored': 'sum',
    'goals_conceded': 'sum',
    'matches_played': 'count'
})

# Per-match averages
team_stats['goals_per_match'] = team_stats['goals_scored'] / team_stats['matches_played']
team_stats['goals_conceded_per_match'] = team_stats['goals_conceded'] / team_stats['matches_played']

# Rolling averages (crucial for form)
team_stats['goals_per_match_L5'] = calculate_rolling_avg(goals_scored, window=5)
team_stats['goals_conceded_L5'] = calculate_rolling_avg(goals_conceded, window=5)

def calculate_rolling_avg(series, window=5):
    return series.rolling(window=window, min_periods=1).mean()
```

**Typical Correlation with Match Outcome**: 0.45-0.55

**Usage**:
- Home team GF + Away team GA = strong predictor of home win
- Ratio features (GF/GA) stabilize across seasons

---

### 1.2 Shot-Based Features

**Expected Goals (xG)** - Most Important Feature

```python
# xG combines:
# 1. Shot distance from goal
# 2. Shot angle to goal
# 3. Defensive pressure
# 4. Goalkeeper position
# 5. Shot type (header, foot, etc.)

def calculate_xg(shot_data):
    """
    Logistic regression model for shot quality
    """
    import numpy as np
    
    # Normalize features
    distance = shot_data['distance'].values  # meters from goal
    angle = shot_data['angle'].values  # degrees from center
    defenders = shot_data['defenders_nearby'].values
    shot_type = shot_data['type'].values  # 'header', 'foot', 'free_kick'
    
    # Coefficients from trained logistic model
    xg = []
    for d, ang, def_count, s_type in zip(distance, angle, defenders, shot_type):
        # Distance effect (inverse)
        dist_factor = 1.0 / (1.0 + np.exp(0.08 * (d - 10)))
        
        # Angle effect (symmetrical, worse at extreme angles)
        angle_factor = 1.0 - (abs(ang - 0) / 90.0) ** 2
        
        # Defender pressure effect
        defend_factor = 0.85 ** def_count  # Each defender reduces 15%
        
        # Shot type effect
        type_multiplier = {'header': 0.5, 'foot': 1.0, 'free_kick': 0.8}.get(s_type, 1.0)
        
        # Combine factors
        base_xg = 0.06 * dist_factor * angle_factor * defend_factor
        shot_xg = base_xg * type_multiplier
        
        xg.append(shot_xg)
    
    return np.array(xg)

# Aggregate to team level
team_xg = shots.groupby('team').agg({
    'xg': 'sum',  # Total xG
    'shots': 'count'
})
team_xg['xg_per_shot'] = team_xg['xg'] / team_xg['shots']

# Rolling averages
team_xg['xg_L5'] = team_xg['xg'].rolling(5).mean()
```

**Key Insights**:
- xG correlates 0.65-0.75 with actual goals (better than naive models)
- Teams that outperform xG tend to regress
- xG Against (xGA) equally important as xG

**Advanced xG Features**:
```python
# Expected Threat (xT) - probability a ball possession leads to goal
def calculate_threat(possession_data):
    # Chain of events leading to shot
    # Higher for actions closer to goal/higher quality
    return threat_value

# Shot quality variance
team_stats['xg_variance'] = team_stats['xg'].rolling(5).std()
# High variance = lucky/unlucky (high volatility)

# Actual vs Expected
team_stats['goal_diff'] = team_stats['goals_scored'] - team_stats['xg']
# Positive = outperforming xG (unsustainable long-term)
# Negative = underperforming xG (regression expected)
```

---

### 1.3 Venue Splits (Home vs Away)

**Critical Feature** - Home advantage averages 0.3-0.4 goals

```python
# Split statistics by venue
team_stats_home = matches[matches['is_home']==True].groupby('team').agg({
    'goals_scored': 'sum',
    'goals_conceded': 'sum',
    'matches_played': 'count'
})

team_stats_away = matches[matches['is_home']==False].groupby('team').agg({
    'goals_scored': 'sum',
    'goals_conceded': 'sum',
    'matches_played': 'count'
})

# Home advantage multiplier
team_stats['home_advantage'] = (
    team_stats_home['goals_scored'] / team_stats_home['matches_played'] - 
    team_stats_away['goals_scored'] / team_stats_away['matches_played']
)

# Typical range: -0.3 to +1.0 (varies by team)
```

**Model Application**:
```python
# Add to match prediction
def add_venue_features(match):
    home_team = match['home_team']
    away_team = match['away_team']
    
    match['home_team_home_gf'] = team_stats_home.loc[home_team, 'goals_per_match']
    match['away_team_away_gf'] = team_stats_away.loc[away_team, 'goals_per_match']
    match['away_team_away_ga'] = team_stats_away.loc[away_team, 'goals_conceded_per_match']
    match['home_advantage_factor'] = 0.35  # Constant ~0.35 goals for home
```

---

## 2. Tactical Features

### 2.1 Passing and Possession

```python
# Calculate possession percentage
match_possession = matches.groupby('team').agg({
    'passes_completed': 'sum',
    'passes_attempted': 'sum'
})
match_possession['possession_pct'] = (
    match_possession['passes_completed'] / match_possession['passes_attempted']
)

# Pass accuracy
team_stats['pass_completion_pct'] = match_possession['possession_pct']

# Ball control impact on outcomes
# Note: High possession doesn't always predict wins
# More important: Possession in final third (attacking third)
team_stats['possession_final_third'] = (
    matches[matches['location'] == 'final_third'].groupby('team')
    .size() / matches.groupby('team').size()
)
```

**Correlation with Match Outcome**: 0.15-0.25 (weak-moderate)
- Too high possession without shots = poor conversion
- Low possession with high shot quality = efficient play

---

### 2.2 Defensive Actions

```python
# Tackles, interceptions, clearances
defensive_stats = matches.groupby('team').agg({
    'tackles': 'sum',
    'interceptions': 'sum',
    'clearances': 'sum',
    'blocks': 'sum'
})

# Per-match rates
team_stats['tackles_per_match'] = defensive_stats['tackles'] / match_count
team_stats['interceptions_per_match'] = defensive_stats['interceptions'] / match_count

# Defensive intensity = tackles + interceptions
team_stats['defensive_intensity'] = (
    team_stats['tackles_per_match'] + team_stats['interceptions_per_match']
)

# Successful defensive actions %
team_stats['tackle_success_rate'] = (
    defensive_stats['successful_tackles'] / defensive_stats['tackles']
)
```

**Correlation with Goals Against**: 0.35-0.45

---

### 2.3 Pressing Intensity

```python
# Pressure success rate - when team presses, do they win ball?
pressure_stats = matches.groupby('team').agg({
    'pressures': 'sum',
    'pressures_successful': 'sum'
})

team_stats['pressure_success_rate'] = (
    pressure_stats['pressures_successful'] / pressure_stats['pressures']
)

# Active pressure rate (per 90 minutes)
team_stats['pressures_per_90'] = pressure_stats['pressures'] / (match_count * 90) * 90

# Pressing in attacking third vs defensive third
team_stats['pressing_ratio_attacking'] = (
    matches[matches['location']=='final_third'].groupby('team')['pressures'].sum() /
    matches.groupby('team')['pressures'].sum()
)
```

**Performance Range**: 40-65% pressure success rate depending on league

---

### 2.4 Set Pieces

```python
# Goals from set pieces (corners, free kicks, throw-ins)
set_piece_goals = matches[matches['set_piece_type'].notna()].groupby('team').agg({
    'goals': 'sum'
})

team_stats['goals_from_set_pieces'] = set_piece_goals['goals']
team_stats['set_piece_conversion'] = (
    set_piece_goals['goals'] / 
    matches[matches['set_piece_type'].notna()].groupby('team')['set_pieces'].count()
)

# Defensive set pieces conceded
team_stats['goals_conceded_set_pieces'] = (
    matches[matches['set_piece_type'].notna() & (matches['team']==opposing_team)]
    .groupby('team')['goals_conceded'].sum()
)

# Typical range: 0.08-0.15 goals per set piece opportunity
```

**Strategic Value**: 
- Set pieces 15-20% of goals in lower leagues
- Increasingly important in tight matches
- More predictable than open play

---

## 3. Contextual Features

### 3.1 Rest and Fatigue

```python
# Days between matches
matches = matches.sort_values('date')
matches['days_since_last_match'] = matches.groupby('team')['date'].diff().dt.days

team_stats['avg_rest_days'] = matches.groupby('team')['days_since_last_match'].mean()

# Match congestion (matches in last 2 weeks)
def calculate_congestion(match_date, team, matches_df):
    last_14_days = matches_df[
        (matches_df['team'] == team) &
        (matches_df['date'] > match_date - pd.Timedelta(days=14)) &
        (matches_df['date'] <= match_date)
    ]
    return len(last_14_days)

matches['congestion_home'] = matches.apply(
    lambda x: calculate_congestion(x['date'], x['home_team'], matches),
    axis=1
)
matches['congestion_away'] = matches.apply(
    lambda x: calculate_congestion(x['date'], x['away_team'], matches),
    axis=1
)

# Feature engineering
matches['congestion_diff'] = (
    matches['congestion_home'] - matches['congestion_away']
)  # Positive = home team more congested (disadvantage)
```

**Impact on Performance**:
- 2-3 matches in 7 days: ~0.1-0.2 goal reduction
- 3-4 matches in 7 days: ~0.3-0.4 goal reduction
- Major factor in cup competitions

---

### 3.2 Form and Momentum

```python
# Rolling form metrics (Last 5 matches)
def calculate_form(matches_df, team, window=5):
    team_matches = matches_df[
        (matches_df['team'] == team) |
        (matches_df['opponent'] == team)
    ].sort_values('date').tail(window)
    
    wins = (team_matches['result'] == 'W').sum()
    draws = (team_matches['result'] == 'D').sum()
    losses = (team_matches['result'] == 'L').sum()
    
    # Form points: W=3, D=1, L=0
    form_points = wins * 3 + draws
    
    goals_for = team_matches['goals_scored'].sum()
    goals_against = team_matches['goals_conceded'].sum()
    
    return {
        'form_points': form_points,
        'wins_last_5': wins,
        'goal_diff_last_5': goals_for - goals_against,
        'goals_per_match_last_5': goals_for / len(team_matches),
        'goals_conceded_last_5': goals_against / len(team_matches)
    }

# Apply to each match
matches['form_home'] = matches.apply(
    lambda x: calculate_form(matches, x['home_team'], window=5)['form_points'],
    axis=1
)

# Win probability directly correlated with recent form
# Form points: 0-15 (0-5 matches)
# Correlation with next match win: 0.35-0.45
```

---

### 3.3 Ranking and Rating Systems

#### **Colley Matrix**

```python
def colley_matrix(matches):
    """
    Linear algebraic approach to team strength
    """
    teams = matches['team'].unique()
    n = len(teams)
    
    # Initialize matrix
    C = np.zeros((n, n))
    b = np.zeros(n)
    
    # Build system
    for _, match in matches.iterrows():
        home_idx = np.where(teams == match['home_team'])[0][0]
        away_idx = np.where(teams == match['away_team'])[0][0]
        
        # Diagonal: 2 + total matches for team
        C[home_idx, home_idx] += 2
        C[away_idx, away_idx] += 2
        
        # Off-diagonal: -1
        C[home_idx, away_idx] -= 1
        C[away_idx, home_idx] -= 1
        
        # Right-hand side
        if match['result'] == 'W':
            b[home_idx] += 1
            b[away_idx] -= 1
        elif match['result'] == 'D':
            b[home_idx] += 0.5
            b[away_idx] += 0.5
        else:
            b[home_idx] -= 1
            b[away_idx] += 1
    
    # Solve
    colley_ratings = np.linalg.solve(C, b)
    
    return pd.DataFrame({
        'team': teams,
        'colley_rating': colley_ratings
    })

# Typical range: -1 to +1 (relative strength)
```

#### **PageRank for Soccer**

```python
def pagerank_rating(matches, damping=0.85):
    """
    Network-based approach treating matches as directed edges
    """
    teams = matches['team'].unique()
    
    # Build transition matrix
    # Win = strong connection, Loss = weak connection
    A = np.zeros((len(teams), len(teams)))
    
    for _, match in matches.iterrows():
        home_idx = np.where(teams == match['home_team'])[0][0]
        away_idx = np.where(teams == match['away_team'])[0][0]
        
        if match['result'] == 'W':
            A[home_idx, away_idx] += 1
        else:
            A[away_idx, home_idx] += 1
    
    # Normalize columns
    A = A / A.sum(axis=0, keepdims=True)
    
    # PageRank iteration
    r = np.ones(len(teams)) / len(teams)
    for _ in range(50):
        r = (1 - damping) / len(teams) + damping * A @ r
    
    return pd.DataFrame({
        'team': teams,
        'pagerank_rating': r
    })

# Advantage: Captures strength of schedule
# Disadvantage: Computationally intensive
```

#### **Elo Ratings (Most Popular)**

```python
class EloRating:
    def __init__(self, k=32, initial_rating=1600):
        self.k = k  # Rating change factor
        self.initial_rating = initial_rating
        self.ratings = {}
    
    def get_rating(self, team):
        return self.ratings.get(team, self.initial_rating)
    
    def update_rating(self, match):
        home_team = match['home_team']
        away_team = match['away_team']
        
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)
        
        # Expected probability
        home_expected = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
        away_expected = 1 / (1 + 10 ** ((home_rating - away_rating) / 400))
        
        # Home advantage adjustment
        home_rating_adjusted = home_rating + 100  # ~0.35 goal advantage
        home_expected = 1 / (1 + 10 ** ((away_rating - home_rating_adjusted) / 400))
        away_expected = 1 - home_expected
        
        # Determine outcome
        if match['result'] == 'W':
            home_score, away_score = 1, 0
        elif match['result'] == 'D':
            home_score, away_score = 0.5, 0.5
        else:
            home_score, away_score = 0, 1
        
        # Update ratings
        self.ratings[home_team] = home_rating + self.k * (home_score - home_expected)
        self.ratings[away_team] = away_rating + self.k * (away_score - away_expected)
    
    def predict_probability(self, home_team, away_team):
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)
        
        home_rating_adjusted = home_rating + 100
        p_home = 1 / (1 + 10 ** ((away_rating - home_rating_adjusted) / 400))
        
        return p_home

# Implementation
elo = EloRating(k=32)
for _, match in matches.iterrows():
    elo.update_rating(match)

# Feature: Latest Elo rating
matches['elo_home'] = matches['home_team'].apply(elo.get_rating)
matches['elo_away'] = matches['away_team'].apply(elo.get_rating)
matches['elo_diff'] = matches['elo_home'] - matches['elo_away']

# Correlation with win probability: 0.55-0.65 (strong)
```

**Comparison**:
| Method | Interpretability | Responsiveness | Computation |
|--------|-----------------|-----------------|-------------|
| Colley | High | Slow | Fast |
| PageRank | Medium | Medium | Slow |
| Elo | High | Fast | Very Fast |

---

## 4. Player-Level Features

### 4.1 Individual Performance

```python
# Player-level aggregation
player_stats = player_events.groupby(['player', 'team']).agg({
    'passes_completed': 'sum',
    'passes_attempted': 'sum',
    'shots': 'sum',
    'goals': 'sum',
    'assists': 'sum',
    'tackles': 'sum',
    'interceptions': 'sum',
    'minutes_played': 'sum'
})

# Per-90-minute rates (standardize for playing time)
player_stats['goals_per_90'] = (player_stats['goals'] / player_stats['minutes_played']) * 90
player_stats['shots_per_90'] = (player_stats['shots'] / player_stats['minutes_played']) * 90
player_stats['pass_completion'] = (
    player_stats['passes_completed'] / player_stats['passes_attempted']
)

# Quality metrics
player_stats['expected_goals_per_90'] = player_stats['xg'] / player_stats['minutes_played'] * 90
player_stats['goal_conversion'] = player_stats['goals'] / player_stats['shots']

# Form (Last 5 appearances)
def player_recent_form(player, team, window=5):
    recent = player_events[
        (player_events['player'] == player) &
        (player_events['team'] == team)
    ].tail(window)
    
    return {
        'goals_last_5': recent['goals'].sum(),
        'xg_last_5': recent['xg'].sum(),
        'minutes_last_5': recent['minutes'].sum()
    }
```

---

### 4.2 Position-Specific Features

```python
# Normalize by position
def get_position_stats(position):
    pos_players = player_stats[player_stats['position'] == position]
    
    for feature in ['goals_per_90', 'shots_per_90', 'tackles_per_90']:
        mean = pos_players[feature].mean()
        std = pos_players[feature].std()
        pos_players[f'{feature}_z_score'] = (pos_players[feature] - mean) / std
    
    return pos_players

# Z-score: How many standard deviations from position average
# Useful for identifying outliers and elite players
```

---

## 5. Feature Engineering Pipeline

### Complete Example

```python
def engineer_features(match):
    """
    Transform raw match data into feature vector
    """
    home_team = match['home_team']
    away_team = match['away_team']
    match_date = match['date']
    
    # Historical data up to match date
    historical = matches[matches['date'] < match_date]
    
    features = {}
    
    # Performance features
    features['home_gf_l5'] = calculate_rolling_avg(
        historical[historical['team']==home_team]['goals_scored'],
        window=5
    )
    features['away_ga_l5'] = calculate_rolling_avg(
        historical[historical['team']==away_team]['goals_conceded'],
        window=5
    )
    
    # Tactical features
    features['home_possession'] = historical[
        historical['team']==home_team
    ]['possession_pct'].tail(5).mean()
    
    # Context features
    features['home_rest_days'] = (
        match_date - 
        historical[historical['team']==home_team].iloc[-1]['date']
    ).days
    
    features['congestion_home'] = calculate_congestion(match_date, home_team, historical)
    
    # Rating features
    elo_rater = EloRating()
    for _, prev_match in historical.iterrows():
        elo_rater.update_rating(prev_match)
    
    features['elo_home'] = elo_rater.get_rating(home_team)
    features['elo_away'] = elo_rater.get_rating(away_team)
    
    return pd.DataFrame([features])

# Apply to all matches
X = matches.apply(engineer_features, axis=1).reset_index(drop=True)
```

---

## 6. Feature Selection & Importance

### Identifying Top Features

```python
from sklearn.inspection import permutation_importance
from sklearn.feature_selection import SelectKBest, f_classif

# Method 1: Model feature importance (tree-based)
model = xgb.XGBClassifier()
model.fit(X_train, y_train)
importance_df = pd.DataFrame({
    'feature': X_train.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

# Method 2: Permutation importance (model-agnostic)
perm_importance = permutation_importance(model, X_test, y_test, n_repeats=10)
perm_df = pd.DataFrame({
    'feature': X_train.columns,
    'importance': perm_importance.importances_mean
}).sort_values('importance', ascending=False)

# Method 3: Statistical correlation
correlation_with_target = X_train.corrwith(y_train).abs().sort_values(ascending=False)

# Top features for match prediction (typical):
# 1. Elo home rating difference
# 2. Form (points last 5)
# 3. Rest days difference
# 4. Home advantage constant
# 5. xG and xGA last 5
```

---

## 7. Feature Interaction & Engineering

```python
# Multiplicative effects
X['home_form_rating_interaction'] = X['home_form_points'] * X['elo_home']

# Non-linear transformations
X['home_rating_squared'] = X['elo_home'] ** 2
X['rest_days_log'] = np.log1p(X['rest_days_diff'])

# Ratio features
X['goal_diff_ratio'] = (X['home_gf_l5'] + 0.01) / (X['away_ga_l5'] + 0.01)

# Difference features
X['rating_diff'] = X['elo_home'] - X['elo_away']
X['form_diff'] = X['home_form'] - X['away_form']

# Scaling features
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

---

## 8. Domain Knowledge Features

### Soccer-Specific Insights

```python
# Rivalry bonus (teams with historical rivalry)
rivalry_bonus = {
    ('Team A', 'Team B'): 0.15,  # Extra goals for Team A vs B
    # ... populated from historical data
}

features['rivalry_boost_home'] = rivalry_bonus.get(
    (home_team, away_team), 0
)

# Stadium temperature/altitude (available from weather APIs)
weather_data = fetch_weather(stadium_location, match_date)
features['temperature_home'] = weather_data['temp']
features['altitude_home'] = get_stadium_altitude(home_team)

# International break effect (players fatigued/injured from national duty)
features['international_break'] = is_international_break(match_date)

# Manager tactics (if tracking available)
features['home_defensive_style'] = 0.8  # 0=attacking, 1=defensive
features['away_pressing_intensity'] = 0.6
```

---

## Key Takeaways

1. **Raw features matter more than algorithm**: Feature engineering = 70% of work
2. **Domain knowledge critical**: Understand soccer context (rest, fatigue, form)
3. **Temporal features essential**: Form, rolling averages, recent performance
4. **Venue splits important**: Home/away are effectively different teams
5. **Interaction effects matter**: Rating * Form, Possession * Efficiency
6. **Feature selection critical**: Too many features → overfitting
7. **Validation crucial**: Check feature stability across time periods

