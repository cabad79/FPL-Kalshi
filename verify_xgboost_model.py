"""
Verify XGBoost model loads and works correctly.
Test integration with match outcome prediction.
"""

import pickle
import numpy as np
from pathlib import Path

def load_model():
    """Load the trained XGBoost model."""
    model_path = Path("C:/Users/carlos.jaramillo/Downloads/FPL-Kalshi/models/xgboost_match_outcome_v1.pkl")

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")

    with open(model_path, 'rb') as f:
        bundle = pickle.load(f)

    return bundle

def predict_match(bundle, home_elo, away_elo, home_form, away_form,
                  home_gf, home_ga, away_gf, away_ga):
    """Make a prediction using the XGBoost model."""
    model = bundle['model']
    scaler = bundle['scaler']
    feature_names = bundle['feature_names']

    # Create feature vector
    h_strength = home_gf / (home_gf + home_ga + 0.1)
    a_strength = away_gf / (away_gf + away_ga + 0.1)

    features = np.array([[
        home_elo, away_elo,
        home_form, away_form,
        home_gf, home_ga, away_gf, away_ga,
        home_elo - away_elo,
        home_form - away_form,
        h_strength - a_strength,
        np.log(home_gf / (away_ga + 0.5)),
        np.log(away_gf / (home_ga + 0.5)),
        1.145,  # Home advantage
    ]])

    # Scale and predict
    features_scaled = scaler.transform(features)
    probabilities = model.predict_proba(features_scaled)[0]

    class_names = bundle['classes']
    prediction = model.predict(features_scaled)[0]

    return {
        'prediction': class_names[prediction],
        'probabilities': {
            class_names[i]: float(probabilities[i])
            for i in range(len(class_names))
        }
    }

def main():
    print("=" * 70)
    print("XGBoost EPL Model Verification")
    print("=" * 70)

    # Load model
    print("\n1. Loading model...")
    try:
        bundle = load_model()
        print("   [OK] Model loaded successfully")
        print(f"   - Accuracy on test set: {bundle['accuracy']:.4f} ({bundle['accuracy']*100:.2f}%)")
        print(f"   - Features: {len(bundle['feature_names'])}")
        print(f"   - Classes: {', '.join(bundle['classes'])}")
    except Exception as e:
        print(f"   [FAIL] Failed to load model: {e}")
        return False

    # Test prediction
    print("\n2. Testing predictions...")

    test_cases = [
        {
            'name': 'Manchester City vs Nottingham (Strong Favorite)',
            'home_elo': 2150, 'away_elo': 1680,
            'home_form': 1.1, 'away_form': 0.7,
            'home_gf': 2.5, 'home_ga': 0.6,
            'away_gf': 1.2, 'away_ga': 1.8,
        },
        {
            'name': 'Liverpool vs Arsenal (Equal Match)',
            'home_elo': 1960, 'away_elo': 1930,
            'home_form': 0.95, 'away_form': 1.0,
            'home_gf': 2.1, 'home_ga': 0.8,
            'away_gf': 2.0, 'away_ga': 0.9,
        },
        {
            'name': 'Southampton vs Chelsea (Away Favorite)',
            'home_elo': 1520, 'away_elo': 1890,
            'home_form': 0.6, 'away_form': 1.1,
            'home_gf': 0.9, 'home_ga': 1.8,
            'away_gf': 2.3, 'away_ga': 0.7,
        }
    ]

    for test in test_cases:
        print(f"\n   Test: {test['name']}")
        try:
            result = predict_match(
                bundle,
                test['home_elo'], test['away_elo'],
                test['home_form'], test['away_form'],
                test['home_gf'], test['home_ga'],
                test['away_gf'], test['away_ga']
            )
            print(f"   Prediction: {result['prediction']}")
            for cls, prob in sorted(result['probabilities'].items(),
                                   key=lambda x: x[1], reverse=True):
                print(f"     - {cls}: {prob:.1%}")
        except Exception as e:
            print(f"   [FAIL] Prediction failed: {e}")
            return False

    # Feature importance
    print("\n3. Feature Importance (Top 5)...")
    importances = bundle['feature_importance']
    feature_names = bundle['feature_names']
    for i, (name, imp) in enumerate(
        sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:5]
    ):
        print(f"   {i+1}. {name}: {imp:.4f}")

    # File info
    print("\n4. Model File Information...")
    model_path = Path("C:/Users/carlos.jaramillo/Downloads/FPL-Kalshi/models/xgboost_match_outcome_v1.pkl")
    size_mb = model_path.stat().st_size / (1024 * 1024)
    print(f"   Path: {model_path}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Type: XGBoost Classifier (multiclass)")

    print("\n" + "=" * 70)
    print("[SUCCESS] All verifications passed!")
    print("=" * 70)

    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
