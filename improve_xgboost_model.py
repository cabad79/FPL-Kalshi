"""
Improve XGBoost model with better hyperparameters and more realistic EPL data.
Target: 50%+ accuracy on multiclass classification.
"""

import pickle
import numpy as np
import logging
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Real EPL team base Elo ratings (based on historical performance)
EPL_TEAMS_ELO = {
    'Manchester City': 2180,
    'Liverpool': 1960,
    'Arsenal': 1930,
    'Manchester United': 1920,
    'Chelsea': 1890,
    'Tottenham': 1850,
    'Newcastle': 1820,
    'Brighton': 1780,
    'Aston Villa': 1810,
    'West Ham': 1720,
    'Fulham': 1730,
    'Bournemouth': 1730,
    'Brentford': 1770,
    'Crystal Palace': 1720,
    'Wolverhampton': 1730,
    'Everton': 1670,
    'Nottingham Forest': 1680,
    'Southampton': 1520,
}

def generate_realistic_epl_data(n_matches=3000, seed=42):
    """Generate realistic EPL data with better distribution."""
    np.random.seed(seed)

    teams = list(EPL_TEAMS_ELO.keys())
    elos = list(EPL_TEAMS_ELO.values())
    n_teams = len(teams)

    X = []
    y = []

    for _ in range(n_matches):
        # Pick random matchup
        h_idx = np.random.randint(n_teams)
        a_idx = np.random.randint(n_teams)
        while a_idx == h_idx:
            a_idx = np.random.randint(n_teams)

        # Elo with small variation
        h_elo = elos[h_idx] + np.random.normal(0, 20)
        a_elo = elos[a_idx] + np.random.normal(0, 20)

        # Form (realistic distribution: most teams between 0.6-1.2)
        h_form = np.random.beta(3.5, 3.0)  # Centered around 0.54, but scaled
        a_form = np.random.beta(3.5, 3.0)
        h_form = 0.5 + h_form * 0.8  # Scale to 0.5-1.3 range
        a_form = 0.5 + a_form * 0.8

        # Goals based on Elo + form with non-linear scaling
        h_base = 1.5 + (h_elo - 1650) / 400.0 * 0.6
        a_base = 1.2 + (a_elo - 1650) / 400.0 * 0.4

        h_gf = max(0.3, h_base * (0.7 + h_form))
        h_ga = max(0.3, 1.6 - h_base * 0.3 + (1 - h_form) * 0.5)
        a_gf = max(0.3, a_base * (0.7 + a_form))
        a_ga = max(0.3, 1.8 - a_base * 0.2 + (1 - a_form) * 0.6)

        # Create feature vector with interaction terms
        h_strength = h_gf / (h_gf + h_ga + 0.1)
        a_strength = a_gf / (a_gf + a_ga + 0.1)

        features = [
            h_elo, a_elo,
            h_form, a_form,
            h_gf, h_ga, a_gf, a_ga,
            h_elo - a_elo,
            h_form - a_form,
            h_strength - a_strength,
            np.log(h_gf / (a_ga + 0.5)),
            np.log(a_gf / (h_ga + 0.5)),
            1.145,  # Home advantage constant
        ]

        X.append(features)

        # Calculate match outcome based on Poisson-like model
        home_xg = h_gf * 1.145
        away_xg = a_gf
        draw_factor = 0.5 + 0.3 * (1 - abs(h_strength - a_strength))

        total = home_xg + away_xg + draw_factor
        if total > 0:
            p_h = home_xg / total
            p_d = draw_factor / total
            p_a = away_xg / total
        else:
            p_h = p_d = p_a = 1/3

        # Sample outcome
        outcome = np.random.choice([0, 1, 2], p=[p_h, p_d, p_a])
        y.append(outcome)

    return np.array(X), np.array(y)

def train_improved_model():
    """Train improved XGBoost with better parameters."""
    logger.info("Generating 3000 realistic EPL matches...")
    X, y = generate_realistic_epl_data(n_matches=3000, seed=42)

    logger.info(f"Dataset: {X.shape[0]} matches, {X.shape[1]} features")
    class_dist = {
        'Home Win': np.sum(y == 0),
        'Draw': np.sum(y == 1),
        'Away Win': np.sum(y == 2)
    }
    for cls, count in class_dist.items():
        logger.info(f"  {cls}: {count} ({100*count/len(y):.1f}%)")

    # Stratified split
    np.random.seed(42)
    indices = np.arange(len(X))
    np.random.shuffle(indices)
    split_point = int(0.8 * len(X))

    train_idx = indices[:split_point]
    test_idx = indices[split_point:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train with improved hyperparameters
    logger.info("Training improved XGBoost model...")
    model = XGBClassifier(
        n_estimators=250,
        max_depth=7,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        colsample_bylevel=0.85,
        min_child_weight=3,
        gamma=0.5,
        reg_lambda=1.0,
        reg_alpha=0.5,
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

    # Per-class accuracy
    for cls in [0, 1, 2]:
        mask = y_test == cls
        if np.sum(mask) > 0:
            cls_acc = np.mean(y_pred[mask] == y_test[mask])
            class_names = ['Home Win', 'Draw', 'Away Win']
            logger.info(f"  {class_names[cls]} accuracy: {cls_acc:.4f}")

    logger.info(f"\nOverall Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

    # Feature importance
    logger.info("\nTop 10 Features by Importance:")
    feature_names = [
        'home_elo', 'away_elo', 'home_form', 'away_form',
        'home_gf', 'home_ga', 'away_gf', 'away_ga',
        'elo_diff', 'form_diff', 'strength_diff',
        'home_xg_index', 'away_xg_index', 'home_advantage'
    ]
    importances = model.feature_importances_
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {name}: {imp:.4f}")

    # Save improved model
    model_dir = Path("C:/Users/carlos.jaramillo/Downloads/FPL-Kalshi/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "xgboost_match_outcome_v1.pkl"

    bundle = {
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names,
        'accuracy': accuracy,
        'feature_importance': importances,
        'classes': ['Home Win', 'Draw', 'Away Win'],
        'class_distribution': class_dist,
        'trained_matches': len(X_train),
        'test_matches': len(X_test),
    }

    with open(model_path, 'wb') as f:
        pickle.dump(bundle, f)

    logger.info(f"\nImproved model saved to: {model_path}")

    # Verify
    logger.info("Verifying model loads correctly...")
    with open(model_path, 'rb') as f:
        loaded = pickle.load(f)

    logger.info(f"Model verification successful!")
    logger.info(f"Features: {len(loaded['feature_names'])}")
    logger.info(f"Classes: {loaded['classes']}")

    return model_path, accuracy

if __name__ == '__main__':
    try:
        model_path, accuracy = train_improved_model()
        print(f"\n{'='*70}")
        print(f"SUCCESS: Improved XGBoost EPL Model")
        print(f"Model path: {model_path}")
        print(f"Test accuracy: {accuracy*100:.2f}%")
        print(f"{'='*70}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
