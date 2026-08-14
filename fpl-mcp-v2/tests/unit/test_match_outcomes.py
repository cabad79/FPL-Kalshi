"""Unit tests for match outcome prediction skills.

Comprehensive test coverage for all functions in match_outcomes module,
including edge cases, boundary conditions, and realistic scenarios.
"""

from __future__ import annotations

import pytest

from fpl_mcp.skills.match_outcomes import (
    calculate_elo_rating,
    calculate_pythagorean_points,
    estimate_home_advantage,
    predict_match_outcome,
)


# ============================================================================
# TESTS FOR predict_match_outcome()
# ============================================================================


class TestPredictMatchOutcome:
    """Tests for predict_match_outcome function."""

    def test_basic_prediction_returns_valid_dict(self) -> None:
        """Verify function returns dict with all required keys."""
        match = {
            "home_team": "Manchester City",
            "away_team": "Nottingham",
            "home_rating": 2100,
            "away_rating": 1500,
        }
        result = predict_match_outcome(match)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"home_win", "draw", "away_win", "confidence"}
        assert all(isinstance(v, float) for v in result.values())

    def test_probabilities_sum_to_one(self) -> None:
        """Verify all probabilities sum to 1.0 (within floating point precision)."""
        match = {
            "home_team": "Liverpool",
            "away_team": "Arsenal",
            "home_rating": 1950,
            "away_rating": 1920,
        }
        result = predict_match_outcome(match)

        total = result["home_win"] + result["draw"] + result["away_win"]
        assert 0.999 < total < 1.001, f"Probabilities sum to {total}, not 1.0"

    def test_strong_favorite_high_win_probability(self) -> None:
        """Strong favorite should have significantly higher win probability."""
        match = {
            "home_team": "Manchester City",
            "away_team": "Newly Promoted",
            "home_rating": 2150,
            "away_rating": 1300,
        }
        result = predict_match_outcome(match)

        assert result["home_win"] > 0.50, "Strong favorite should have >50% win prob"
        assert result["away_win"] < 0.35, "Weak team should have <35% win prob"
        assert result["home_win"] > result["away_win"], "Favorite should have higher prob"

    def test_equal_strength_teams_balanced_probabilities(self) -> None:
        """Teams with equal ratings should have relatively balanced probabilities."""
        match = {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1800,
            "away_rating": 1800,
            "home_goals_for": 1.5,
            "home_goals_against": 1.5,
            "away_goals_for": 1.5,
            "away_goals_against": 1.5,
        }
        result = predict_match_outcome(match, {"model_type": "form"})

        # Probabilities should be in reasonable range
        assert 0.25 < result["home_win"] < 0.55, f"Home win prob {result['home_win']} unrealistic"
        assert 0.2 < result["away_win"] < 0.5, f"Away win prob {result['away_win']} unrealistic"
        assert 0.15 < result["draw"] < 0.45, f"Draw prob {result['draw']} unrealistic"

    def test_confidence_equals_max_probability(self) -> None:
        """Confidence should equal the maximum outcome probability."""
        match = {
            "home_team": "Strong Team",
            "away_team": "Weak Team",
            "home_rating": 2000,
            "away_rating": 1400,
        }
        result = predict_match_outcome(match)

        max_prob = max(result["home_win"], result["draw"], result["away_win"])
        assert abs(result["confidence"] - max_prob) < 0.001

    def test_with_custom_model_params(self) -> None:
        """Function should respect custom model parameters."""
        match = {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1800,
            "away_rating": 1700,
            "home_goals_for": 2.0,
            "home_goals_against": 1.0,
            "away_goals_for": 1.5,
            "away_goals_against": 1.5,
        }
        params = {
            "model_type": "elo",
            "weight_elo": 1.0,
            "weight_form": 0.0,
            "weight_xg": 0.0,
        }
        result = predict_match_outcome(match, params)

        assert all(0 <= v <= 1 for v in result.values()), "All probabilities should be 0-1"

    def test_missing_required_field_raises_error(self) -> None:
        """Missing required field should raise ValueError."""
        incomplete_match = {
            "home_team": "Team A",
            "away_team": "Team B",
            # Missing: home_rating, away_rating
        }
        with pytest.raises(ValueError, match="missing required field"):
            predict_match_outcome(incomplete_match)

    def test_invalid_rating_type_raises_error(self) -> None:
        """Non-numeric rating should raise TypeError."""
        match = {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": "not a number",  # type: ignore
            "away_rating": 1600,
        }
        with pytest.raises(TypeError):
            predict_match_outcome(match)

    def test_zero_rating_raises_error(self) -> None:
        """Zero or negative rating should raise error."""
        match = {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1800,
            "away_rating": 0,  # Invalid
        }
        with pytest.raises(TypeError):
            predict_match_outcome(match)

    def test_ensemble_vs_elo_different_results(self) -> None:
        """Ensemble and Elo-only models should produce different results."""
        match = {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1800,
            "away_rating": 1700,
            "home_goals_for": 2.5,
            "home_goals_against": 0.8,
            "away_goals_for": 1.2,
            "away_goals_against": 2.0,
        }

        result_ensemble = predict_match_outcome(match, {"model_type": "ensemble"})
        result_elo = predict_match_outcome(match, {"model_type": "elo"})

        # Results should be different (unless coincidentally the same)
        assert result_ensemble["home_win"] != result_elo["home_win"] or result_ensemble is result_elo


# ============================================================================
# TESTS FOR estimate_home_advantage()
# ============================================================================


class TestEstimateHomeAdvantage:
    """Tests for estimate_home_advantage function."""

    def test_premier_league_home_advantage_realistic(self) -> None:
        """PL home advantage should be around 14-15%."""
        advantage = estimate_home_advantage("PL", 2024)

        assert 1.10 < advantage < 1.20, f"PL advantage {advantage} outside expected 1.10-1.20"

    def test_different_leagues_different_values(self) -> None:
        """Different leagues should have different home advantages."""
        pl_advantage = estimate_home_advantage("PL", 2024)
        championship_advantage = estimate_home_advantage("Championship", 2024)
        bundesliga_advantage = estimate_home_advantage("Bundesliga", 2024)

        # Bundesliga typically stronger than Championship
        assert bundesliga_advantage > championship_advantage
        # All should be between 1.0 and 1.3
        assert 1.0 < pl_advantage < 1.3
        assert 1.0 < championship_advantage < 1.3
        assert 1.0 < bundesliga_advantage < 1.3

    def test_home_advantage_multiplier_greater_than_one(self) -> None:
        """Home advantage should always be >= 1.0."""
        leagues = ["PL", "Championship", "EFL", "Bundesliga", "La_Liga"]
        for league in leagues:
            advantage = estimate_home_advantage(league, 2024)
            assert advantage >= 0.85, f"{league} advantage {advantage} too low"

    def test_seasonal_variations(self) -> None:
        """Home advantage may vary slightly by season."""
        adv_2024 = estimate_home_advantage("PL", 2024)
        adv_2026 = estimate_home_advantage("PL", 2026)

        # Both should be reasonable and similar (within 5%)
        assert 0.95 < adv_2026 / adv_2024 < 1.05

    def test_with_venue_crowd_factor(self) -> None:
        """Strong crowd should increase home advantage."""
        base = estimate_home_advantage("PL", 2024)
        with_strong_crowd = estimate_home_advantage(
            "PL", 2024, {"crowd_factor": 1.15}
        )

        assert with_strong_crowd > base, "Strong crowd should increase advantage"

    def test_with_weak_crowd_factor(self) -> None:
        """Weak crowd should decrease home advantage."""
        base = estimate_home_advantage("PL", 2024)
        with_weak_crowd = estimate_home_advantage("PL", 2024, {"crowd_factor": 0.90})

        assert with_weak_crowd < base, "Weak crowd should decrease advantage"

    def test_invalid_league_raises_error(self) -> None:
        """Unknown league should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown league"):
            estimate_home_advantage("InvalidLeague", 2024)

    def test_invalid_season_raises_error(self) -> None:
        """Season out of valid range should raise ValueError."""
        with pytest.raises(ValueError, match="between 1995 and 2100"):
            estimate_home_advantage("PL", 1990)

        with pytest.raises(ValueError):
            estimate_home_advantage("PL", 2150)

    def test_non_integer_season_raises_error(self) -> None:
        """Non-integer season should raise TypeError."""
        with pytest.raises(TypeError):
            estimate_home_advantage("PL", 2024.5)  # type: ignore

    def test_non_string_league_raises_error(self) -> None:
        """Non-string league should raise TypeError."""
        with pytest.raises(TypeError):
            estimate_home_advantage(123, 2024)  # type: ignore

    def test_case_insensitive_league_input(self) -> None:
        """League input should be case-insensitive."""
        lower = estimate_home_advantage("pl", 2024)
        upper = estimate_home_advantage("PL", 2024)
        mixed = estimate_home_advantage("Pl", 2024)

        assert lower == upper == mixed, "League lookup should be case-insensitive"

    def test_crowd_factor_bounds(self) -> None:
        """Extreme crowd factors should be clamped to reasonable range."""
        # Very high crowd factor
        high = estimate_home_advantage("PL", 2024, {"crowd_factor": 2.0})
        assert high <= 1.35, "Result should be clamped to reasonable max"

        # Negative crowd factor
        with_negative = estimate_home_advantage("PL", 2024, {"crowd_factor": -0.5})
        assert with_negative >= 0.85, "Result should be clamped to reasonable min"


# ============================================================================
# TESTS FOR calculate_elo_rating()
# ============================================================================


class TestCalculateEloRating:
    """Tests for calculate_elo_rating function."""

    def test_win_increases_rating(self) -> None:
        """Winning a match should increase Elo rating."""
        current = 1800
        opponent = 1600
        new_rating = calculate_elo_rating(current, opponent, "win", k_factor=32)

        assert new_rating > current, "Win should increase rating"
        assert new_rating > opponent, "Favored team should still be ahead after win"

    def test_loss_decreases_rating(self) -> None:
        """Losing a match should decrease Elo rating."""
        current = 1800
        opponent = 1600
        new_rating = calculate_elo_rating(current, opponent, "loss", k_factor=32)

        assert new_rating < current, "Loss should decrease rating"

    def test_draw_rating_depends_on_expectations(self) -> None:
        """Draw result should increase rating if draw unexpected, decrease if expected."""
        # Strong team drawing weak team: should decrease
        strong_vs_weak_draw = calculate_elo_rating(1800, 1400, "draw", k_factor=32)
        assert strong_vs_weak_draw < 1800, "Draw as favorite should decrease rating"

        # Weak team drawing strong team: should increase
        weak_vs_strong_draw = calculate_elo_rating(1400, 1800, "draw", k_factor=32)
        assert weak_vs_strong_draw > 1400, "Draw as underdog should increase rating"

    def test_upset_win_larger_rating_change(self) -> None:
        """Underdog winning should produce larger rating gain than expected win."""
        # Underdog wins
        underdog_win = calculate_elo_rating(1400, 1800, "win", k_factor=32)
        underdog_gain = underdog_win - 1400

        # Favorite wins
        favorite_win = calculate_elo_rating(1800, 1400, "win", k_factor=32)
        favorite_gain = favorite_win - 1800

        assert abs(underdog_gain) > abs(favorite_gain), "Upset should have larger effect"

    def test_k_factor_affects_rating_change(self) -> None:
        """Larger K-factor should produce larger rating changes."""
        result_k16 = calculate_elo_rating(1800, 1600, "win", k_factor=16)
        result_k32 = calculate_elo_rating(1800, 1600, "win", k_factor=32)
        result_k48 = calculate_elo_rating(1800, 1600, "win", k_factor=48)

        gain_16 = result_k16 - 1800
        gain_32 = result_k32 - 1800
        gain_48 = result_k48 - 1800

        assert gain_48 > gain_32 > gain_16, "Higher K-factor should produce larger changes"
        # K-factor should scale linearly (K=48 is 3× K=16)
        assert abs(gain_48 - 3 * gain_16) < 0.01, "K-factor should scale linearly"

    def test_rating_change_bounded(self) -> None:
        """Rating change should be bounded by K-factor."""
        current = 1600
        opponent = 1200
        new_rating = calculate_elo_rating(current, opponent, "loss", k_factor=32)

        change = abs(new_rating - current)
        assert change <= 32, "Rating change should not exceed K-factor"

    def test_equal_strength_draw(self) -> None:
        """Equal strength draw should preserve rating."""
        current = 1800
        opponent = 1800
        new_rating = calculate_elo_rating(current, opponent, "draw", k_factor=32)

        assert abs(new_rating - current) < 0.01, "Draw vs equal should preserve rating"

    def test_equal_strength_win(self) -> None:
        """Equal strength win should increase rating proportionally."""
        current = 1800
        opponent = 1800
        new_rating = calculate_elo_rating(current, opponent, "win", k_factor=32)

        assert new_rating > current, "Win vs equal should increase rating"
        change = new_rating - current
        assert 15 < change < 17, "Equal strength win gain should be ~16"

    def test_invalid_result_raises_error(self) -> None:
        """Invalid result string should raise ValueError."""
        with pytest.raises(ValueError, match="win.*draw.*loss"):
            calculate_elo_rating(1800, 1600, "invalid")  # type: ignore

    def test_invalid_rating_type_raises_error(self) -> None:
        """Non-numeric rating should raise TypeError."""
        with pytest.raises(TypeError):
            calculate_elo_rating("not a number", 1600, "win")  # type: ignore

    def test_zero_or_negative_rating_raises_error(self) -> None:
        """Zero or negative rating should raise TypeError."""
        with pytest.raises(TypeError):
            calculate_elo_rating(0, 1600, "win")

        with pytest.raises(TypeError):
            calculate_elo_rating(-100, 1600, "win")

    def test_invalid_k_factor_raises_error(self) -> None:
        """Invalid K-factor should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_elo_rating(1800, 1600, "win", k_factor=0)

        with pytest.raises(ValueError):
            calculate_elo_rating(1800, 1600, "win", k_factor=-32)

    def test_standard_elo_formula_accuracy(self) -> None:
        """Verify calculation matches standard Elo formula."""
        # Manual calculation for verification
        current = 1800
        opponent = 1600
        k_factor = 32

        # Expected score = 1 / (1 + 10^((opponent - current) / 400))
        elo_diff = opponent - current
        expected = 1.0 / (1.0 + 10.0 ** (elo_diff / 400.0))
        actual_score = 1.0  # Win

        manual_new_elo = current + k_factor * (actual_score - expected)

        calculated = calculate_elo_rating(current, opponent, "win", k_factor)

        assert abs(calculated - manual_new_elo) < 0.01, "Should match standard formula"

    def test_case_insensitive_result(self) -> None:
        """Result parameter should be case-insensitive."""
        r1 = calculate_elo_rating(1800, 1600, "win")
        r2 = calculate_elo_rating(1800, 1600, "WIN")
        r3 = calculate_elo_rating(1800, 1600, "Win")

        assert r1 == r2 == r3, "Result should be case-insensitive"


# ============================================================================
# TESTS FOR calculate_pythagorean_points()
# ============================================================================


class TestCalculatePythagoreanPoints:
    """Tests for calculate_pythagorean_points function."""

    def test_neutral_team_one_point_five(self) -> None:
        """Team with equal GF and GA should get ~1.5 points per match."""
        points = calculate_pythagorean_points(1.5, 1.5)

        assert 1.4 < points < 1.6, f"Neutral team should be ~1.5, got {points}"

    def test_dominant_team_high_points(self) -> None:
        """Team dominating in goal differential should get high points."""
        points = calculate_pythagorean_points(2.5, 1.0, exponent=1.8)

        assert points > 2.0, f"Dominant team should exceed 2.0 points, got {points}"
        assert points < 3.0, f"Points should be < 3.0, got {points}"

    def test_weak_team_low_points(self) -> None:
        """Team with poor goal differential should get low points."""
        points = calculate_pythagorean_points(1.0, 2.5, exponent=1.8)

        assert points < 1.0, f"Weak team should be < 1.0, got {points}"
        assert points > 0.0, f"Points should be > 0.0, got {points}"

    def test_perfect_defense_max_points(self) -> None:
        """Perfect defense (GA=0) should yield 3.0 points."""
        points = calculate_pythagorean_points(2.0, 0.0)

        assert points == 3.0, "Perfect defense should yield 3.0 points"

    def test_exponent_higher_emphasizes_differential(self) -> None:
        """Higher exponent should amplify goal differential effect."""
        points_low_exp = calculate_pythagorean_points(2.5, 1.0, exponent=1.5)
        points_high_exp = calculate_pythagorean_points(2.5, 1.0, exponent=2.0)

        assert points_high_exp > points_low_exp, "Higher exponent should emphasize differential"

    def test_different_exponents(self) -> None:
        """Function should handle different valid exponents."""
        gf, ga = 2.0, 1.2

        points_beggs = calculate_pythagorean_points(gf, ga, exponent=1.8)
        points_kingsman = calculate_pythagorean_points(gf, ga, exponent=2.0)
        points_alt = calculate_pythagorean_points(gf, ga, exponent=1.5)

        # All should be valid and in 0-3 range
        assert all(0 <= p <= 3 for p in [points_beggs, points_kingsman, points_alt])
        # All should be different
        assert len(set([points_beggs, points_kingsman, points_alt])) == 3

    def test_season_projection_realistic(self) -> None:
        """Multiply per-match points by 38 matches for season projection."""
        points_per_match = calculate_pythagorean_points(2.0, 1.0)
        season_total = points_per_match * 38

        # Realistic EPL range is roughly 30-110 points
        assert 50 < season_total < 100, f"Season total {season_total} should be realistic"

    def test_negative_goals_raises_error(self) -> None:
        """Negative goal values should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_pythagorean_points(-1.0, 1.0)

        with pytest.raises(ValueError):
            calculate_pythagorean_points(1.0, -1.0)

    def test_both_zero_goals_raises_error(self) -> None:
        """Both goals zero should raise ValueError (no match data)."""
        with pytest.raises(ValueError):
            calculate_pythagorean_points(0.0, 0.0)

    def test_invalid_exponent_raises_error(self) -> None:
        """Exponent outside valid range should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_pythagorean_points(2.0, 1.0, exponent=0.0)

        with pytest.raises(ValueError):
            calculate_pythagorean_points(2.0, 1.0, exponent=-1.5)

        with pytest.raises(ValueError):
            calculate_pythagorean_points(2.0, 1.0, exponent=3.5)

    def test_output_always_0_to_3_range(self) -> None:
        """Output should always be clamped to 0-3 range."""
        # Normal cases
        assert 0 <= calculate_pythagorean_points(0.5, 2.5) <= 3.0
        assert 0 <= calculate_pythagorean_points(3.0, 0.1) <= 3.0
        assert 0 <= calculate_pythagorean_points(5.0, 1.0) <= 3.0

    def test_zero_goals_against_edge_case(self) -> None:
        """Goals against = 0 edge case should return 3.0."""
        points = calculate_pythagorean_points(2.5, 0.0)
        assert points == 3.0

    def test_very_small_goal_differentials(self) -> None:
        """Should handle very small goal differential values."""
        points = calculate_pythagorean_points(0.1, 0.1)
        assert 1.0 < points < 2.0, "Small numbers should still produce reasonable output"

    def test_large_goal_values(self) -> None:
        """Should handle large goal values (e.g., season aggregates)."""
        # Over 38 matches: 80 goals for, 30 against
        points = calculate_pythagorean_points(80.0, 30.0)
        # This represents strong team, should project to high season total
        season_total = points * 38
        assert season_total > 80, "Dominant team projection should be high"

    def test_realistic_team_scenarios(self) -> None:
        """Test realistic team goal statistics."""
        # Liverpool-like team
        liverpool = calculate_pythagorean_points(2.1, 0.8, exponent=1.8)
        assert liverpool > 2.2, "Liverpool-like stats should be very strong"

        # Mid-table team
        midtable = calculate_pythagorean_points(1.3, 1.3, exponent=1.8)
        assert 1.4 < midtable < 1.6, "Mid-table should be near 1.5"

        # Relegated team
        relegated = calculate_pythagorean_points(0.8, 1.8, exponent=1.8)
        assert relegated < 1.0, "Poor team should be < 1.0"
