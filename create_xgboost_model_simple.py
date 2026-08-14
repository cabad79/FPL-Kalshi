"""
Create a simple pre-trained XGBoost model for EPL match prediction.
Uses only numpy and xgboost - no pandas required.
"""

import pickle
import numpy as np
import logging
from pathlib import Path

try:
    from xgboost import XGBClassifier
except ImportError:
    print("XGBoost not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "-q", "xgboost"], check=True)
    from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# EPL team Elo base ratings
EPL_ELOS = {
    'Manchester City': 2150, 'Liverpool': 1950, 'Arsenal': 1920,
    'Manchester United': 1950, 'Chelsea': 1900, 'Tottenham': 1850,
    'Newcastle': 1800, 'Aston Villa': 1800, 'Brighton': 1750,
    'Brentford': 1750, 'West Ham': 1700, 'Fulham': 1700,
    'Bournemouth': 1700, 'Wolverhampton': 1700, 'Crystal Palace': 1700,
    'Everton': 1650, 'Nottingham Forest': 1650, 'Southampton': 1500,
}

def generate_synthetic_matches(n_matches=1500, seed=42):
    """Generate synthetic EPL match data using Elo-based simulation."""
    np.random.seed(seed)

    teams = list(EPL_ELOS.keys())
    team_elos = list(EPL_ELOS.values())
    n_teams = len(teams)

    X = []  # Features
    y = []  # Labels (0=Home Win, 1=Draw, 2=Away Win)

    for _ in range(n_matches):
        # Random home/away teams
        h_idx = np.random.randint(0, n_teams)
        a_idx = np.random.randint(0, n_teams)
        while a_idx == h_idx:
            a_idx = np.random.randint(0, n_teams)

        # Base Elo ratings with seasonal variation
        h_elo = team_elos[h_idx] + np.random.normal(0, 25)
        a_elo = team_elos[a_idx] + np.random.normal(0, 25)

        # Form (0.3 - 1.5 range, center ~0.9)
        h_form = np.random.uniform(0.4, 1.2)
        a_form = np.random.uniform(0.4, 1.2)

        # Goals for/against based on Elo and form
        h_gf = max(0.3, h_form * (1.4 + (h_elo - 1650) / 800))
        h_ga = max(0.3, (2.0 - h_form) * (1.4 - (h_elo - 1650) / 800))
        a_gf = max(0.3, a_form * (0.9 + (a_elo - 1650) / 800))
        a_ga = max(0.3, (2.0 - a_form) * (1.6 + (a_elo - 1650) / 800))

        # Feature vector
        features = [
            h_elo, a_elo,                           # Elo ratings
            h_form, a_form,                         # Recent form
            h_gf, h_ga, a_gf, a_ga,                 # Goals stats
            h_elo - a_elo,                          # Elo difference
            h_form - a_form,                        # Form difference
            (h_gf - h_ga) - (a_gf - a_ga),          # Goal differential
            h_elo / (h_elo + a_elo),                # Relative strength
        ]

        X.append(features)

        # Simulate match outcome based on expected goals
        home_xg = h_gf * 1.145  # Home advantage factor
        away_xg = a_gf
        draw_factor = 0.6

        # Probability distribution
        total = home_xg + away_xg + draw_factor
        p_h = home_xg / total
        p_d = draw_factor / total
        p_a = away_xg / total

        # Sample outcome
        outcome = np.random.choice([0, 1, 2], p=[p_h, p_d, p_a])
        y.append(outcome)

    return np.array(X), np.array(y)

def train_model():
    """Train XGBoost classifier on synthetic data."""
    logger.info("Generating 1500 synthetic EPL matches...")
    X, y = generate_synthetic_matches(n_matches=1500, seed=42)

    logger.info(f"Dataset shape: {X.shape}")
    logger.info(f"Classes: Home Win={np.sum(y==0)}, Draw={np.sum(y==1)}, Away Win={np.sum(y==2)}")

    # Train-test split
    n_train = int(0.8 * len(X))
    idx = np.random.permutation(len(X))

    X_train = X[idx[:n_train]]
    y_train = y[idx[:n_train]]
    X_test = X[idx[n_train:]]
    y_test = y[idx[n_train:]]

    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Standardize features
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0) + 1e-8
    X_train_scaled = (X_train - mean) / std
    X_test_scaled = (X_test - mean) / std

    # Train XGBoost
    logger.info("Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        tree_method='hist',
        device='cpu'
    )

    model.fit(X_train_scaled, y_train, verbose=False)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = np.mean(y_pred == y_test)

    logger.info(f"\nTest Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

    # Feature importance
    logger.info("\nFeature Importance (top 8):")
    feature_names = [
        'home_elo', 'away_elo', 'home_form', 'away_form',
        'home_gf', 'home_ga', 'away_gf', 'away_ga',
        'elo_diff', 'form_diff', 'gd_diff', 'strength_ratio'
    ]
    importances = model.feature_importances_
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:8]:
        logger.info(f"  {name}: {imp:.4f}")

    # Save model bundle
    model_dir = Path("C:/Users/carlos.jaramillo/Downloads/FPL-Kalshi/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "xgboost_match_outcome_v1.pkl"

    bundle = {
        'model': model,
        'scaler_mean': mean,
        'scaler_std': std,
        'feature_names': feature_names,
        'accuracy': accuracy,
        'feature_importance': importances,
        'classes': ['Home Win', 'Draw', 'Away Win']
    }

    with open(model_path, 'wb') as f:
        pickle.dump(bundle, f)

    logger.info(f"\nModel saved to: {model_path}")

    # Verify
    logger.info("Verifying model loads correctly...")
    with open(model_path, 'rb') as f:
        loaded = pickle.load(f)

    logger.info(f"Model loaded successfully!")
    logger.info(f"Accuracy from loaded model: {loaded['accuracy']:.4f}")

    return model_path, accuracy

if __name__ == '__main__':
    try:
        model_path, accuracy = train_model()
        print(f"\n{'='*70}")
        print(f"SUCCESS: XGBoost EPL Model Created")
        print(f"Model path: {model_path}")
        print(f"Test accuracy: {accuracy*100:.2f}%")
        print(f"Classes: Home Win, Draw, Away Win (multiclass)")
        print(f"Features: 12 (Elo, form, GF/GA stats, ratios)")
        print(f"{'='*70}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
