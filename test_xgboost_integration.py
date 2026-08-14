"""Test XGBoost integration with match_outcomes module."""

import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent / "fpl-mcp-v2" / "src"))

from fpl_mcp.ml import predict_match_outcome_xgboost

def test_basic_prediction():
    """Test basic XGBoost prediction."""
    print("Testing XGBoost integration...")

    result = predict_match_outcome_xgboost(
        home_elo=2150,
        away_elo=1680,
        home_form=1.1,
        away_form=0.7,
        home_gf=2.5,
        home_ga=0.6,
        away_gf=1.2,
        away_ga=1.8,
    )

    print(f"\nPrediction Result:")
    print(f"  Home Win: {result['home_win']:.1%}")
    print(f"  Draw:     {result['draw']:.1%}")
    print(f"  Away Win: {result['away_win']:.1%}")
    print(f"  Confidence: {result['confidence']:.1%}")

    # Validate
    assert 'home_win' in result
    assert 'draw' in result
    assert 'away_win' in result
    assert 'confidence' in result
    assert 0.99 < sum([result['home_win'], result['draw'], result['away_win']]) < 1.01

    print("\n[SUCCESS] XGBoost integration working!")
    return True

if __name__ == '__main__':
    try:
        success = test_basic_prediction()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
