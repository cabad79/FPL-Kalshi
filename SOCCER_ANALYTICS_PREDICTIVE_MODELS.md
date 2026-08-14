# Soccer Analytics: Predictive Models

## Overview

This guide covers practical implementation of ML models for soccer prediction with focus on accuracy ranges and sports betting applications.

---

## 1. Match Outcome Prediction

### 1.1 Problem Definition

**Prediction Target**: Home Win, Draw, Away Win (Multiclass classification)
- Home Win (W): 1.0
- Draw (D): 0.5  
- Away Win (L): 0.0

**Alternative**: Direct probability for each outcome

**Historical Baselines**:
- Home wins: ~46%
- Draws: ~26%
- Away wins: ~28%
- Home advantage: ~0.35 goals equivalent

### 1.2 Data Preparation

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Load historical matches
matches = pd.read_csv('historical_matches.csv')

# Features from previous sections
X = engineer_features(matches)

# Target variable (multiclass)
y_multiclass = matches['result']  # 'W', 'D', 'L'

# Or binary (Home win vs not)
y_binary = (matches['result'] == 'W').astype(int)

# Time-based split (crucial for sports data!)
cutoff_date = '2024-01-01'
train_mask = X['match_date'] < cutoff_date
test_mask = X['match_date'] >= cutoff_date

X_train, X_test = X[train_mask], X[test_mask]
y_train, y_test = y_multiclass[train_mask], y_multiclass[test_mask]

print(f"Training set: {len(X_train)} matches ({X_train['match_date'].min()} to {X_train['match_date'].max()})")
print(f"Test set: {len(X_test)} matches ({X_test['match_date'].min()} to {X_test['match_date'].max()})")
```

**Why Time-Based Split?**
- Forward validation: Test on future data
- Prevents data leakage
- Realistic performance estimate
- Avoids overfitting to specific seasons

### 1.3 Multiclass Model

```python
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

# Encode target
le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train)  # W=0, D=1, L=2
y_test_encoded = le.transform(y_test)

# XGBoost for multiclass
model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    objective='multi:softprob',  # Multiclass classification
    num_class=3,
    random_state=42
)

model.fit(
    X_train, y_train_encoded,
    eval_set=[(X_val, y_val_encoded)],
    early_stopping_rounds=20,
    verbose=False
)

# Predictions
y_pred_prob = model.predict_proba(X_test)
# Shape: (n_samples, 3) with columns [P(W), P(D), P(L)]

y_pred = model.predict(X_test)
y_pred_labels = le.inverse_transform(y_pred)

# Evaluation
from sklearn.metrics import classification_report, confusion_matrix

print(classification_report(y_test, y_pred_labels))
print(confusion_matrix(y_test, y_pred_labels))
```

**Typical Accuracy Ranges**:
- Random baseline: 46% (always pick home team)
- Logistic regression: 52-55%
- Random forest: 55-58%
- XGBoost: 58-62%
- Ensemble of multiple models: 60-65%

**Performance by Match Type**:
| Match Type | Accuracy | Notes |
|-----------|----------|-------|
| Heavy favorite (Elo diff > 200) | 68-72% | Strong teams reliable |
| Balanced match (Elo diff ±100) | 48-52% | More unpredictable |
| Underdog match (Away Elo < -100) | 55-60% | Away teams harder to predict |
| Derby matches | 45-50% | Rivalry increases variance |

---

### 1.4 Probability Calibration

```python
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

# Calibrate probabilities (important for betting!)
calibrator = CalibratedClassifierCV(model, cv='prefit', method='sigmoid')
y_pred_prob_calibrated = calibrator.fit(X_val, y_val).predict_proba(X_test)

# Check calibration
frac_pos, mean_pred = calibration_curve(y_test_binary, y_pred_prob_calibrated[:, 0], n_bins=10)

import matplotlib.pyplot as plt
plt.figure(figsize=(10, 8))
plt.plot(mean_pred, frac_pos, 's-', label='XGBoost')
plt.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
plt.xlabel('Mean predicted probability')
plt.ylabel('Fraction of positives')
plt.title('Calibration Curve')
plt.legend()
plt.grid(True)
plt.show()

# Interpretation: If model says P(Home Win)=0.60, it should occur ~60% of the time
```

**Why Calibration Matters**:
- Betting odds based on miscalibrated probabilities = losses
- Logistic regression naturally better calibrated than tree models
- Calibration ≠ discrimination accuracy (can be well-calibrated but wrong)

---

## 2. Goal Prediction Models

### 2.1 Total Goals (Over/Under)

```python
# Target: Total goals in match
y_total_goals = matches['home_goals'] + matches['away_goals']

# Poisson regression baseline
from sklearn.linear_model import PoissonRegressor

model_poisson = PoissonRegressor()
model_poisson.fit(X_train, y_train)
y_pred_poisson = model_poisson.predict(X_test)

# XGBoost regression for count data
model_xgb = xgb.XGBRegressor(
    objective='count:poisson',  # Poisson loss
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1
)

model_xgb.fit(X_train, y_train)
y_pred_xgb = model_xgb.predict(X_test)

# Evaluate
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

mae = mean_absolute_error(y_test, y_pred_xgb)
mape = mean_absolute_percentage_error(y_test, y_pred_xgb)

print(f"MAE: {mae:.2f} goals")
print(f"MAPE: {mape:.1%}")

# Classification approach: O/U threshold
def total_goals_over_under(model_pred, threshold=2.5):
    """Convert predicted goals to Over/Under classification"""
    return (model_pred > threshold).astype(int)

y_ou_pred = total_goals_over_under(y_pred_xgb, threshold=2.5)
y_ou_true = (y_test > 2.5).astype(int)

accuracy_ou = (y_ou_pred == y_ou_true).mean()
print(f"Over/Under 2.5 accuracy: {accuracy_ou:.1%}")
```

**Typical Accuracy Ranges**:
- Prediction within 1 goal: 45-55%
- Over/Under 2.5: 56-62%
- Over/Under 1.5: 60-68%
- Over/Under 3.5: 72-78%

**Why O/U easier to predict**:
- Fewer classes (2 vs continuous)
- Tail effects less important
- Focus on average tendency

---

### 2.2 Home Team Goals Only

```python
# Poisson for home goals specifically
y_home_goals = matches['home_goals']

model = xgb.XGBRegressor(
    objective='count:poisson',
    n_estimators=200,
    max_depth=5
)

model.fit(X_train, y_train)
y_pred_home = model.predict(X_test)

# Typical goals by match type
print(f"Mean home goals: {y_train.mean():.2f}")
print(f"Std home goals: {y_train.std():.2f}")

# Prediction error distribution
errors = y_test - y_pred_home
print(f"RMSE: {np.sqrt((errors**2).mean()):.2f}")
print(f"MAE: {np.abs(errors).mean():.2f}")

# Error by team strength (check calibration)
for team in ['Strong Team', 'Mid Team', 'Weak Team']:
    team_mask = X_test['team'] == team
    team_error = errors[team_mask].mean()
    print(f"{team}: {team_error:+.2f} goals bias")
```

**Typical Prediction Accuracy**:
- Mean prediction: 1.3-1.6 goals/team
- RMSE: 1.0-1.2 goals
- "Home team scores" (>0 goals) accuracy: 78-85%

---

## 3. Expected Goals (xG) Model

### 3.1 Shot-Level xG Prediction

```python
# Load shot data (from StatsBomb, WhoScored, etc.)
shots = pd.read_csv('shots_data.csv')

# Feature engineering for shots
X_shots = pd.DataFrame({
    'distance': shots['distance'],
    'angle': shots['angle'],
    'defenders_nearby': shots['defenders_nearby'],
    'shot_type': pd.Categorical(shots['type']),
    'assist_type': pd.Categorical(shots['assist_type']),
    'pressure': shots['under_pressure'],
    'previous_action': pd.Categorical(shots['previous_action']),
    'shot_stationary_freeze_frame': shots['stationary']
})

# Encode categorical features
X_shots_encoded = pd.get_dummies(X_shots, columns=['shot_type', 'assist_type', 'previous_action'])

y_shots = shots['outcome'] == 'goal'  # Binary: goal or not

# Train xG model
model_xg = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=(~y_shots).sum() / y_shots.sum()  # Handle imbalance
)

model_xg.fit(X_shots_train, y_shots_train)
xg_values = model_xg.predict_proba(X_shots_test)[:, 1]

# Evaluate xG model
from sklearn.metrics import roc_auc_score, brier_score_loss

auc = roc_auc_score(y_shots_test, xg_values)
brier = brier_score_loss(y_shots_test, xg_values)

print(f"xG Model AUC: {auc:.3f}")
print(f"Brier Score: {brier:.4f}")

# Aggregation to team level
match_xg = shots.groupby(['match_id', 'team']).apply(
    lambda group: {
        'xg': group['xg'].sum(),
        'shots': len(group),
        'goals': group['goal'].sum()
    }
)
```

**Typical xG Model Accuracy**:
- AUC: 0.72-0.76 (decent discrimination)
- Calibration: Well-calibrated when trained on large sample
- Correlation with actual goals: 0.65-0.75

**xG Interpretation**:
- xG per shot: 0.08-0.12 average
- High xG underperformance: Regression to mean expected
- Teams: Top team xG 15-20/match, weak team 8-12/match

---

### 3.2 Player Shot Quality

```python
# Player-specific xG
player_shots = shots.groupby('player').agg({
    'xg': ['sum', 'count', 'mean'],
    'goal': 'sum'
}).round(3)

player_shots.columns = ['xg_total', 'shots', 'xg_per_shot', 'goals']
player_shots['xg_over_under'] = player_shots['goals'] - player_shots['xg_total']
player_shots['shot_conversion'] = player_shots['goals'] / player_shots['shots']

# Conversion: Expected vs Actual
player_shots['outperformance_pct'] = (
    (player_shots['goals'] - player_shots['xg_total']) / 
    player_shots['xg_total']
)

print(player_shots.sort_values('xg_total', ascending=False).head(10))

# Elite finishers: +2 to +5 xG outperformance
# Poor finishers: -2 to -5 xG underperformance
# Average: ±0.5 xG
```

---

## 4. Player Performance Prediction

### 4.1 Appearance-Level Prediction

```python
# Player game statistics
player_appearances = pd.read_csv('player_appearances.csv')

# Features
X_player = pd.DataFrame({
    'goals_per_90_l5': player_appearances['goals_per_90_l5'],
    'assists_per_90_l5': player_appearances['assists_per_90_l5'],
    'shots_per_90_l5': player_appearances['shots_per_90_l5'],
    'pass_completion_l5': player_appearances['pass_completion_l5'],
    'tackles_per_90_l5': player_appearances['tackles_per_90_l5'],
    'minutes_last_match': player_appearances['minutes_last_match'],
    'is_home': player_appearances['is_home'],
    'opponent_strength': player_appearances['opponent_elo'],
    'injury_recovery': player_appearances['injury_recovery'],
    'position_category': pd.Categorical(player_appearances['position'])
})

X_player_encoded = pd.get_dummies(X_player)

# Target: Points (goals=5, assists=3, clean sheet=1 for def, etc.)
y_player = player_appearances['fantasy_points']

# Model
model_player = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05
)

model_player.fit(X_player_train, y_player_train)
y_pred = model_player.predict(X_player_test)

# Evaluation by position
for position in ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']:
    mask = X_player_test['position'] == position
    mae = mean_absolute_error(y_player_test[mask], y_pred[mask])
    print(f"{position}: MAE = {mae:.2f} points")
```

**Typical Accuracy**:
| Position | MAE (points) | Accuracy |
|----------|-------------|----------|
| Forward | 1.5-2.0 | 40-45% |
| Midfielder | 1.8-2.2 | 38-42% |
| Defender | 1.2-1.6 | 45-50% |
| Goalkeeper | 1.0-1.4 | 50-55% |

**Why Defenders More Predictable**:
- Consistent playing time
- Fewer variance sources
- Clean sheets moderately predictable

---

### 4.2 Binary Prediction: Goal/No Goal

```python
# Will player score (binary)?
y_player_goal = player_appearances['goals'] > 0

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    scale_pos_weight=(~y_player_goal).sum() / y_player_goal.sum()  # Imbalanced
)

model.fit(X_player_train, y_player_goal_train)
y_prob = model.predict_proba(X_player_test)[:, 1]

# Evaluation
from sklearn.metrics import precision_score, recall_score, roc_auc_score

precision = precision_score(y_player_goal_test, y_prob > 0.5)
recall = recall_score(y_player_goal_test, y_prob > 0.5)
auc = roc_auc_score(y_player_goal_test, y_prob)

print(f"Precision: {precision:.1%}")
print(f"Recall: {recall:.1%}")
print(f"AUC: {auc:.3f}")

# Optimal threshold (not 0.5 for imbalanced data)
from sklearn.metrics import f1_score

f1_scores = [f1_score(y_player_goal_test, y_prob > t) for t in np.arange(0.1, 0.9, 0.05)]
optimal_threshold = np.arange(0.1, 0.9, 0.05)[np.argmax(f1_scores)]
print(f"Optimal threshold: {optimal_threshold:.2f}")
```

**Typical Baseline**: 
- Striker goal probability: 10-15% per match
- Midfielder: 4-7%
- Defender: 1-3%
- Goalkeeper: <0.1%

**Model Improvement**: 10-15% relative improvement over naive rates

---

## 5. Injury & Suspension Prediction

### 5.1 Injury Risk

```python
# Historical injury data
injuries = pd.read_csv('injuries.csv')

# Features
X_injury = pd.DataFrame({
    'age': injuries['age'],
    'minutes_last_month': injuries['minutes_last_month'],
    'matches_last_month': injuries['matches_last_month'],
    'recent_injury_count': injuries['recent_injury_count'],
    'position': injuries['position'],
    'intense_match': injuries['high_intensity_match'],
    'international_duty': injuries['international_break']
})

X_injury_encoded = pd.get_dummies(X_injury)

# Target: Will player be injured in next match?
y_injury = injuries['injured_next_match']

model_injury = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    scale_pos_weight=(~y_injury).sum() / y_injury.sum()
)

model_injury.fit(X_injury_train, y_injury_train)
injury_prob = model_injury.predict_proba(X_injury_test)[:, 1]

# Evaluation
auc = roc_auc_score(y_injury_test, injury_prob)
print(f"Injury prediction AUC: {auc:.3f}")

# Risk factors (from SHAP)
import shap
explainer = shap.TreeExplainer(model_injury)
shap_values = explainer.shap_values(X_injury_test)

# Top risk factors
risk_importance = pd.DataFrame({
    'feature': X_injury.columns,
    'impact': np.abs(shap_values).mean(axis=0)
}).sort_values('impact', ascending=False)

print(risk_importance.head(10))
```

**Typical Baseline**: 5-8% injury rate per match
**Model Improvement**: Better identify at-risk players (e.g., players coming back from injury)

---

## 6. Model Validation & Testing

### 6.1 K-Fold Cross Validation

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold

# For temporal data, use time-series split
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
scores = []

for train_idx, test_idx in tscv.split(X):
    X_fold_train, X_fold_test = X.iloc[train_idx], X.iloc[test_idx]
    y_fold_train, y_fold_test = y.iloc[train_idx], y.iloc[test_idx]
    
    model = xgb.XGBClassifier(n_estimators=100, max_depth=5)
    model.fit(X_fold_train, y_fold_train)
    
    score = model.score(X_fold_test, y_fold_test)
    scores.append(score)

print(f"Cross-validation scores: {scores}")
print(f"Mean: {np.mean(scores):.3f} +/- {np.std(scores):.3f}")
```

**Why Time Series Split?**
- Respects temporal ordering
- Prevents future data leakage
- Realistic performance estimate

---

### 6.2 Walk-Forward Validation

```python
# Progressive validation (most realistic)
results = []

for end_date in pd.date_range('2023-01-01', '2024-01-01', freq='M'):
    train_end = end_date - pd.Timedelta(days=1)
    test_start = end_date
    test_end = end_date + pd.Timedelta(days=30)
    
    train_mask = X['date'] <= train_end
    test_mask = (X['date'] > test_start) & (X['date'] <= test_end)
    
    if test_mask.sum() < 10:
        continue
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    model = xgb.XGBClassifier(n_estimators=100, max_depth=5)
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    results.append({
        'period': end_date,
        'accuracy': accuracy,
        'n_matches': test_mask.sum()
    })

results_df = pd.DataFrame(results)
print(results_df)
print(f"Mean accuracy across periods: {results_df['accuracy'].mean():.1%}")
```

**Why Important**: Detects model degradation over time (concept drift)

---

## 7. Betting Application

### 7.1 Expected Value Calculation

```python
def calculate_ev(predicted_prob, betting_odds):
    """
    Expected Value = (prob_of_win * odds) - (prob_of_loss * 1)
    """
    prob_loss = 1 - predicted_prob
    ev = (predicted_prob * betting_odds) - prob_loss
    return ev

# Example
model_prob_home_win = 0.55
betting_odds = 1.80

ev = calculate_ev(model_prob_home_win, betting_odds)
print(f"EV: {ev:.3f}")  # Positive EV = expected profit

# Win probability from odds (bookmaker implied)
def odds_to_probability(odds):
    return 1 / odds

bookmaker_prob = odds_to_probability(1.80)
print(f"Bookmaker's implied probability: {bookmaker_prob:.1%}")

# Model probability
model_prob = 0.55
print(f"Our model probability: {model_prob:.1%}")

# Edge
edge = model_prob - bookmaker_prob
print(f"Edge: {edge:+.1%}")
```

### 7.2 Profitable Betting Strategies

```python
# Filter for positive EV bets only
profitable_bets = []

for _, match in matches.iterrows():
    # Get model prediction
    pred_prob = model.predict_proba(X.loc[match.name])[0, 1]  # Home win prob
    
    # Get betting odds
    odds = match['home_odds']
    
    # Calculate EV
    ev = calculate_ev(pred_prob, odds)
    
    if ev > 0.05:  # Only bet if EV > 5%
        profitable_bets.append({
            'match': match['fixture'],
            'prob': pred_prob,
            'odds': odds,
            'ev': ev,
            'roi_pct': ev / (odds - 1) * 100
        })

profitable_df = pd.DataFrame(profitable_bets)
print(profitable_df.sort_values('ev', ascending=False))

# Expected long-term ROI
if len(profitable_df) > 0:
    avg_ev = profitable_df['ev'].mean()
    expected_roi = avg_ev * len(profitable_df)
    print(f"Expected ROI on 100 bets: {expected_roi:.1%}")
```

**Kelly Criterion for Bet Sizing**:
```python
def kelly_fraction(win_prob, odds):
    """
    Kelly Criterion: f = (prob * odds - 1) / (odds - 1)
    Fraction of bankroll to wager
    """
    if odds <= 1:
        return 0
    
    f = (win_prob * odds - 1) / (odds - 1)
    
    # Cap at 5% for safety (fractional Kelly)
    return min(max(f, 0), 0.05)

# Example
best_fraction = kelly_fraction(pred_prob=0.55, odds=1.80)
print(f"Kelly fraction: {best_fraction:.1%} of bankroll")
```

---

## Key Takeaways

1. **Match Prediction**: 58-62% accuracy realistic ceiling with good features
2. **Goal Prediction**: 60-70% accuracy on O/U 2.5, better than individual team goals
3. **xG Models**: 72-76% AUC, fundamental for modern analysis
4. **Player Predictions**: 40-50% accuracy (high variance in football)
5. **Time-based validation**: Essential to prevent data leakage
6. **Calibration**: Critical for profitable betting
7. **Ensemble methods**: 2-4% improvement over single models

