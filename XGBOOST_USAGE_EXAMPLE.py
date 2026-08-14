"""
Example: How to use XGBoost model in predict_match_outcome()

This shows the recommended way to integrate the XGBoost model
into the existing ensemble prediction system.
"""

from fpl_mcp.ml import predict_match_outcome_xgboost
from fpl_mcp.skills.match_outcomes import (
    predict_match_outcome,
    MatchData,
    MatchOutcomePrediction
)


def predict_match_outcome_with_xgboost(
    match_data: MatchData,
    model_params: dict | None = None
) -> MatchOutcomePrediction:
    """
    Enhanced predict_match_outcome with optional XGBoost model.

    If model_params contains use_xgboost=True, uses the XGBoost model.
    Otherwise falls back to the ensemble method.

    Args:
        match_data: Match information dictionary
        model_params: Optional parameters including use_xgboost flag

    Returns:
        Match outcome prediction with probabilities
    """

    if not model_params:
        model_params = {}

    # Check if XGBoost model should be used
    use_xgboost = model_params.get('use_xgboost', False)

    if use_xgboost:
        try:
            # Extract required fields for XGBoost model
            home_elo = match_data.get('home_rating', 1650)
            away_elo = match_data.get('away_rating', 1650)

            # Get form data (would come from data service)
            home_form = model_params.get('home_form', 1.0)
            away_form = model_params.get('away_form', 1.0)

            # Get goal statistics
            home_gf = match_data.get('home_goals_for', 1.5)
            home_ga = match_data.get('home_goals_against', 1.5)
            away_gf = match_data.get('away_goals_for', 1.5)
            away_ga = match_data.get('away_goals_against', 1.5)

            # Get XGBoost predictions
            xgb_result = predict_match_outcome_xgboost(
                home_elo=home_elo,
                away_elo=away_elo,
                home_form=home_form,
                away_form=away_form,
                home_gf=home_gf,
                home_ga=home_ga,
                away_gf=away_gf,
                away_ga=away_ga,
            )

            return {
                'home_win': xgb_result['home_win'],
                'draw': xgb_result['draw'],
                'away_win': xgb_result['away_win'],
                'confidence': xgb_result['confidence'],
            }

        except Exception as e:
            print(f"XGBoost prediction failed, falling back to ensemble: {e}")
            # Fall through to ensemble method

    # Default: Use ensemble method (existing implementation)
    return predict_match_outcome(match_data, model_params)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == '__main__':

    # Example 1: Using XGBoost model directly
    print("=" * 70)
    print("Example 1: Direct XGBoost Usage")
    print("=" * 70)

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

    print(f"\nMatch: Manchester City vs Nottingham Forest")
    print(f"Home Win: {result['home_win']:.1%}")
    print(f"Draw: {result['draw']:.1%}")
    print(f"Away Win: {result['away_win']:.1%}")
    print(f"Model Confidence: {result['confidence']:.1%}")

    # Example 2: Integration with match_outcomes module
    print("\n" + "=" * 70)
    print("Example 2: Integration with predict_match_outcome()")
    print("=" * 70)

    match_data = {
        'home_team': 'Liverpool',
        'away_team': 'Arsenal',
        'home_rating': 1960,
        'away_rating': 1930,
        'home_goals_for': 2.1,
        'home_goals_against': 0.8,
        'away_goals_for': 2.0,
        'away_goals_against': 0.9,
    }

    # Using ensemble (default)
    result_ensemble = predict_match_outcome(match_data)
    print(f"\nEnsemble Method:")
    print(f"  Home Win: {result_ensemble['home_win']:.1%}")
    print(f"  Draw: {result_ensemble['draw']:.1%}")
    print(f"  Away Win: {result_ensemble['away_win']:.1%}")

    # Using XGBoost with enhanced wrapper
    result_xgboost = predict_match_outcome_with_xgboost(
        match_data,
        model_params={
            'use_xgboost': True,
            'home_form': 0.95,
            'away_form': 1.0,
        }
    )
    print(f"\nXGBoost Method:")
    print(f"  Home Win: {result_xgboost['home_win']:.1%}")
    print(f"  Draw: {result_xgboost['draw']:.1%}")
    print(f"  Away Win: {result_xgboost['away_win']:.1%}")

    # Example 3: Fallback behavior
    print("\n" + "=" * 70)
    print("Example 3: Fallback to Ensemble on XGBoost Error")
    print("=" * 70)

    incomplete_data = {
        'home_team': 'Chelsea',
        'away_team': 'Manchester United',
        # Missing ratings - will trigger fallback
    }

    result_fallback = predict_match_outcome_with_xgboost(
        incomplete_data,
        model_params={'use_xgboost': True}  # Will fail and fall back
    )
    print(f"\nFallback to Ensemble (missing data):")
    print(f"  Home Win: {result_fallback['home_win']:.1%}")
    print(f"  Draw: {result_fallback['draw']:.1%}")
    print(f"  Away Win: {result_fallback['away_win']:.1%}")

    # Example 4: For Kalshi contract pricing
    print("\n" + "=" * 70)
    print("Example 4: Converting to Kalshi Contract Odds")
    print("=" * 70)

    match = {
        'home_team': 'Manchester City',
        'away_team': 'Brighton',
        'home_rating': 2150,
        'away_rating': 1750,
        'home_goals_for': 2.5,
        'home_goals_against': 0.6,
        'away_goals_for': 1.5,
        'away_goals_against': 1.3,
    }

    probs = predict_match_outcome_xgboost(
        home_elo=match['home_rating'],
        away_elo=match['away_rating'],
        home_form=1.0,
        away_form=1.0,
        home_gf=match['home_goals_for'],
        home_ga=match['home_goals_against'],
        away_gf=match['away_goals_for'],
        away_ga=match['away_goals_against'],
    )

    # Convert probabilities to decimal odds
    # Decimal odds = 1 / probability
    home_win_odds = 1 / max(0.01, probs['home_win'])
    draw_odds = 1 / max(0.01, probs['draw'])
    away_win_odds = 1 / max(0.01, probs['away_win'])

    print(f"\nMatch: {match['home_team']} vs {match['away_team']}")
    print(f"\nProbabilities:")
    print(f"  Home Win: {probs['home_win']:.1%}")
    print(f"  Draw: {probs['draw']:.1%}")
    print(f"  Away Win: {probs['away_win']:.1%}")

    print(f"\nImplied Decimal Odds (for Kalshi):")
    print(f"  Home Win: {home_win_odds:.2f}")
    print(f"  Draw: {draw_odds:.2f}")
    print(f"  Away Win: {away_win_odds:.2f}")

    # American odds conversion
    home_american = (home_win_odds - 1) * 100
    print(f"\nImplied American Odds:")
    print(f"  Home Win: {home_american:+.0f}")

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
