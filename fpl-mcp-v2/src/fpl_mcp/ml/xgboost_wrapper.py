"""
XGBoost wrapper for EPL match outcome prediction.

Provides easy integration with the predict_match_outcome function.
Loads the pre-trained model and handles feature scaling.
"""

import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Path to pre-trained model (in root-level models directory)
# __file__ -> .../fpl-mcp-v2/src/fpl_mcp/ml/xgboost_wrapper.py
# parent.parent.parent.parent -> .../fpl-mcp-v2/
# parent again -> ...
MODEL_PATH = Path(__file__).parent.parent.parent.parent.parent / "models" / "xgboost_match_outcome_v1.pkl"


class XGBoostMatcher:
    """Wrapper for XGBoost EPL match prediction model."""

    def __init__(self, model_path: Path | None = None):
        """Initialize model wrapper.

        Args:
            model_path: Path to pickled model bundle. Uses default if None.

        Raises:
            FileNotFoundError: If model file not found
            ValueError: If model bundle invalid
        """
        if model_path is None:
            model_path = MODEL_PATH

        if not model_path.exists():
            raise FileNotFoundError(f"XGBoost model not found: {model_path}")

        try:
            with open(model_path, 'rb') as f:
                self.bundle = pickle.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load model bundle: {e}")

        self.model = self.bundle['model']
        self.scaler = self.bundle['scaler']
        self.feature_names = self.bundle['feature_names']
        self.classes = self.bundle['classes']

        logger.info(f"Loaded XGBoost model with accuracy: {self.bundle['accuracy']:.4f}")

    def predict(
        self,
        home_elo: float,
        away_elo: float,
        home_form: float,
        away_form: float,
        home_gf: float,
        home_ga: float,
        away_gf: float,
        away_ga: float,
    ) -> dict[str, float]:
        """Predict match outcome probabilities.

        Args:
            home_elo: Home team Elo rating
            away_elo: Away team Elo rating
            home_form: Home team recent form (0.0-2.0 scale)
            away_form: Away team recent form (0.0-2.0 scale)
            home_gf: Home team goals for per match
            home_ga: Home team goals against per match
            away_gf: Away team goals for per match
            away_ga: Away team goals against per match

        Returns:
            Dictionary with probabilities:
                - home_win: P(Home Win)
                - draw: P(Draw)
                - away_win: P(Away Win)
                - confidence: Max probability

        Raises:
            ValueError: If inputs invalid
        """
        # Validate inputs
        if not all(isinstance(x, (int, float)) for x in [home_elo, away_elo]):
            raise ValueError("Elo ratings must be numeric")

        if home_gf < 0 or home_ga < 0 or away_gf < 0 or away_ga < 0:
            raise ValueError("Goals statistics cannot be negative")

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
            np.log(max(0.01, home_gf / (away_ga + 0.5))),
            np.log(max(0.01, away_gf / (home_ga + 0.5))),
            1.145,  # Home advantage constant
        ]])

        # Scale and predict
        try:
            features_scaled = self.scaler.transform(features)
            probabilities = self.model.predict_proba(features_scaled)[0]
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise ValueError(f"Prediction failed: {e}")

        # Return probabilities
        prob_dict = {
            'home_win': float(probabilities[0]),
            'draw': float(probabilities[1]),
            'away_win': float(probabilities[2]),
            'confidence': float(np.max(probabilities)),
        }

        return prob_dict

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance from trained model.

        Returns:
            Dictionary mapping feature names to importance scores.
        """
        return dict(zip(self.feature_names, self.bundle['feature_importance']))


# Singleton instance for easy access
_matcher = None


def get_matcher() -> XGBoostMatcher:
    """Get or create singleton matcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = XGBoostMatcher()
    return _matcher


def predict_match_outcome_xgboost(
    home_elo: float,
    away_elo: float,
    home_form: float,
    away_form: float,
    home_gf: float,
    home_ga: float,
    away_gf: float,
    away_ga: float,
) -> dict[str, float]:
    """Convenience function for XGBoost predictions.

    Args:
        home_elo: Home team Elo rating
        away_elo: Away team Elo rating
        home_form: Home team recent form
        away_form: Away team recent form
        home_gf: Home team goals for per match
        home_ga: Home team goals against per match
        away_gf: Away team goals for per match
        away_ga: Away team goals against per match

    Returns:
        Dictionary with match outcome probabilities
    """
    matcher = get_matcher()
    return matcher.predict(
        home_elo, away_elo, home_form, away_form,
        home_gf, home_ga, away_gf, away_ga
    )
