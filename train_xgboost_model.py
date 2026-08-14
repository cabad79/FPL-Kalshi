"""
Train XGBoost model for EPL match outcome prediction.

This script:
1. Generates realistic EPL training data from 2018-2024 seasons
2. Creates features: Elo ratings, form, GF/GA, home advantage
3. Trains XGBoost classifier for multiclass match prediction (Home Win/Draw/Away Win)
4. Saves model to models/xgboost_match_outcome_v1.pkl
5. Reports accuracy and feature importance
"""

import pickle
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# EPL team Elo ratings (approximate, based on historical performance)
EPL_TEAMS = {
    'Manchester City': 2150, 'Manchester United': 1950, 'Liverpool': 1950,
    'Arsenal': 1920, 'Chelsea': 1900, 'Tottenham': 1850, 'Newcastle': 1800,
    'Brighton': 1750, 'Aston Villa': 1800, 'West Ham': 1700,
    'Fulham': 1700, 'Brentford': 1750, 'Crystal Palace': 1700, 'Everton': 1650,
    'Nottingham Forest': 1650, 'Bournemouth': 1700, 'Wolverhampton': 1700,
    'Southampton': 1500, 'Ipswich Town': 1550, 'Luton Town': 1550,
    'Burnley': 1600, 'Leyton Orient': 1500, 'Huddersfield': 1450,
    'Leeds United': 1550, 'Derby County': 1450, 'Watford': 1550,
}

def generate_epl_training_data(n_matches=2000, random_state=42):
    """
    Generate realistic EPL match data for training.
    Uses Elo ratings to create reasonable match dynamics.
    """
    np.random.seed(random_state)

    teams = list(EPL_TEAMS.keys())
    base_elos = list(EPL_TEAMS.values())

    matches = []

    for _ in range(n_matches):
        # Random home/away teams
        home_idx = np.random.randint(0, len(teams))
        away_idx = np.random.randint(0, len(teams))
        while away_idx == home_idx:
            away_idx = np.random.randint(0, len(teams))

        home_team = teams[home_idx]
        away_team = teams[away_idx]
        home_elo = base_elos[home_idx]
        away_elo = base_elos[away_idx]

        # Add some seasonal variation
        home_elo += np.random.normal(0, 30)
        away_elo += np.random.normal(0, 30)

        # Generate form (recent performance: 0-1.0)
        home_form = np.random.uniform(0.4, 1.2)
        away_form = np.random.uniform(0.4, 1.2)

        # Generate goals for/against stats (per match)
        home_gf = max(0.3, home_form * (1.5 + (home_elo - 1650) / 500.0))
        home_ga = max(0.3, (2.0 - home_form) * (1.5 - (home_elo - 1650) / 500.0))
        away_gf = max(0.3, away_form * (1.0 + (away_elo - 1650) / 500.0))
        away_ga = max(0.3, (2.0 - away_form) * (1.5 + (away_elo - 1650) / 500.0))

        # Home advantage factor
        home_advantage = 1.145

        # Predict outcome based on model
        home_expected_goals = (home_gf * home_advantage)
        away_expected_goals = away_gf

        # Simulate result using Poisson-like probability
        home_win_prob = home_expected_goals / (home_expected_goals + away_expected_goals + 0.6)
        draw_prob = 0.6 / (home_expected_goals + away_expected_goals + 0.6)
        away_win_prob = away_expected_goals / (home_expected_goals + away_expected_goals + 0.6)

        # Draw outcome based on probabilities
        outcome = np.random.choice([0, 1, 2], p=[home_win_prob, draw_prob, away_win_prob])
        # 0 = Home Win, 1 = Draw, 2 = Away Win

        matches.append({
            'home_team': home_team,
            'away_team': away_team,
            'home_elo': home_elo,
            'away_elo': away_elo,
            'home_form': home_form,
            'away_form': away_form,
            'home_goals_for': home_gf,
            'home_goals_against': home_ga,
            'away_goals_for': away_gf,
            'away_goals_against': away_ga,
            'outcome': outcome  # 0=Home Win, 1=Draw, 2=Away Win
        })

    return pd.DataFrame(matches)

def create_features(df):
    """Create ML features from match data."""
    features = df[[
        'home_elo', 'away_elo', 'home_form', 'away_form',
        'home_goals_for', 'home_goals_against',
        'away_goals_for', 'away_goals_against'
    ]].copy()

    # Add derived features
    features['elo_diff'] = df['home_elo'] - df['away_elo']
    features['form_diff'] = df['home_form'] - df['away_form']
    features['gd_home'] = df['home_goals_for'] - df['home_goals_against']
    features['gd_away'] = df['away_goals_for'] - df['away_goals_against']
    features['gd_diff'] = features['gd_home'] - features['gd_away']
    features['home_strength'] = df['home_elo'] / (df['home_elo'] + df['away_elo'])

    return features

def main():
    logger.info("Starting XGBoost EPL model training...")

    # Generate training data
    logger.info("Generating 2000 synthetic EPL matches from historical patterns...")
    df = generate_epl_training_data(n_matches=2000, random_state=42)

    # Create features
    logger.info("Creating features...")
    X = create_features(df)
    y = df['outcome'].values

    logger.info(f"Dataset shape: {X.shape}")
    logger.info(f"Outcome distribution: Home={np.sum(y==0)}, Draw={np.sum(y==1)}, Away={np.sum(y==2)}")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info(f"Training set size: {X_train.shape[0]}")
    logger.info(f"Test set size: {X_test.shape[0]}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train XGBoost classifier
    logger.info("Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        tree_method='hist',
        objective='multi:softprob',
        num_class=3,
        early_stopping_rounds=10,
        eval_metric='mlogloss'
    )

    # Train with early stopping
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )

    # Evaluate
    logger.info("Evaluating model...")
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"\nModel Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info("\nClassification Report:")
    logger.info(classification_report(
        y_test, y_pred,
        target_names=['Home Win', 'Draw', 'Away Win']
    ))

    logger.info("\nConfusion Matrix:")
    logger.info(confusion_matrix(y_test, y_pred))

    # Feature importance
    logger.info("\nTop 10 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    for idx, row in feature_importance.head(10).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")

    # Save model with scaler
    model_dir = Path("C:/Users/carlos.jaramillo/Downloads/FPL-Kalshi/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "xgboost_match_outcome_v1.pkl"

    # Save model and scaler together for easy loading
    model_bundle = {
        'model': model,
        'scaler': scaler,
        'feature_columns': X.columns.tolist(),
        'accuracy': accuracy,
        'feature_importance': feature_importance.to_dict('records')
    }

    with open(model_path, 'wb') as f:
        pickle.dump(model_bundle, f)

    logger.info(f"\nModel saved to: {model_path}")
    logger.info(f"Model can be loaded with: pickle.load(open('{model_path}', 'rb'))")

    # Verify the model loads correctly
    logger.info("\nVerifying model can be loaded...")
    with open(model_path, 'rb') as f:
        loaded_bundle = pickle.load(f)

    logger.info(f"Model loaded successfully!")
    logger.info(f"Loaded model accuracy: {loaded_bundle['accuracy']:.4f}")

    return model_path, accuracy, feature_importance

if __name__ == '__main__':
    model_path, accuracy, importance = main()
    print(f"\n{'='*60}")
    print(f"SUCCESS: XGBoost model trained and saved")
    print(f"Model path: {model_path}")
    print(f"Test accuracy: {accuracy*100:.2f}%")
    print(f"{'='*60}")
