"""Comprehensive tests for goal prediction module."""

from __future__ import annotations

import math
import pytest

from skills.goal_prediction import (
    calculate_poisson_probabilities,
    estimate_goal_distribution,
    estimate_xg_for_match,
    predict_match_goals,
)


class TestCalculatePoissonProbabilities:
    """Test suite for calculate_poisson_probabilities function."""

    def test_basic_lambda_calculation(self) -> None:
        """Test basic Poisson probability calculation with lambda=2.5."""
        probs = calculate_poisson_probabilities(2.5, max_goals=5)

        assert isinstance(probs, dict)
        assert len(probs) == 6  # 0 through 5 goals
        assert all(0 <= p <= 1 for p in probs.values())

    def test_probabilities_sum_to_one(self) -> None:
        """Test that probabilities sum to approximately 1."""
        probs = calculate_poisson_probabilities(1.5, max_goals=10)
        total = sum(probs.values())
        assert 0.99 < total <= 1.01  # Allow small floating point error

    def test_lambda_zero_clamping(self) -> None:
        """Test that lambda=0 is clamped to MIN_LAMBDA."""
        probs = calculate_poisson_probabilities(0.0, max_goals=5)
        # With very small lambda, P(0) should be high
        assert probs[0] > 0.99

    def test_lambda_negative_clamping(self) -> None:
        """Test that negative lambda is clamped to MIN_LAMBDA."""
        probs = calculate_poisson_probabilities(-5.0, max_goals=5)
        assert probs[0] > 0.99

    def test_lambda_large_clamping(self) -> None:
        """Test that large lambda is clamped appropriately."""
        probs = calculate_poisson_probabilities(100.0, max_goals=20)
        # Distribution should be reasonable
        assert len(probs) == 21
        assert sum(probs.values()) < 1.01

    def test_lambda_one(self) -> None:
        """Test Poisson with lambda=1 (e^-1 ≈ 0.368)."""
        probs = calculate_poisson_probabilities(1.0, max_goals=5)
        # P(0) = e^-1 ≈ 0.3679
        assert 0.36 < probs[0] < 0.37
        # P(1) = e^-1 ≈ 0.3679
        assert 0.36 < probs[1] < 0.37

    def test_max_goals_parameter(self) -> None:
        """Test that max_goals parameter is respected."""
        probs_5 = calculate_poisson_probabilities(2.0, max_goals=5)
        probs_10 = calculate_poisson_probabilities(2.0, max_goals=10)

        assert len(probs_5) == 6  # 0 to 5
        assert len(probs_10) == 11  # 0 to 10
        assert all(k in probs_5 for k in range(6))
        assert all(k in probs_10 for k in range(11))

    def test_max_goals_zero(self) -> None:
        """Test with max_goals=0."""
        probs = calculate_poisson_probabilities(1.5, max_goals=0)
        assert len(probs) == 1
        assert 0 in probs

    def test_max_goals_negative_raises_error(self) -> None:
        """Test that negative max_goals raises ValueError."""
        with pytest.raises(ValueError):
            calculate_poisson_probabilities(2.0, max_goals=-1)

    def test_realistic_match_scenario(self) -> None:
        """Test Poisson with realistic match expected goals."""
        # Typical home team xG
        probs = calculate_poisson_probabilities(1.8, max_goals=5)
        # Most likely outcomes should be 1 or 2 goals
        sorted_goals = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        top_outcomes = [goal for goal, _ in sorted_goals[:2]]
        assert 1 in top_outcomes or 2 in top_outcomes

    def test_distribution_shape_low_lambda(self) -> None:
        """Test that distribution shape is correct for low lambda."""
        probs = calculate_poisson_probabilities(0.5, max_goals=5)
        # Should be heavily skewed toward 0
        assert probs[0] > probs[1]
        assert probs[1] > probs[2]

    def test_distribution_shape_high_lambda(self) -> None:
        """Test distribution shape for higher lambda."""
        probs = calculate_poisson_probabilities(5.0, max_goals=10)
        # Distribution should be more spread out
        # Peak should be around lambda
        sorted_probs = sorted(
            [(k, v) for k, v in probs.items()], key=lambda x: x[1], reverse=True
        )
        peak_goal = sorted_probs[0][0]
        assert 4 <= peak_goal <= 6  # Peak around 5


class TestPredictMatchGoals:
    """Test suite for predict_match_goals function."""

    def test_basic_prediction(self) -> None:
        """Test basic match goal prediction."""
        result = predict_match_goals(1.5, 1.2)

        assert isinstance(result, dict)
        assert "home_goals" in result
        assert "away_goals" in result
        assert "probability" in result
        assert "confidence" in result

        assert isinstance(result["home_goals"], int)
        assert isinstance(result["away_goals"], int)
        assert 0 <= result["probability"] <= 1
        assert 0 <= result["confidence"] <= 1

    def test_xg_validation_home_high(self) -> None:
        """Test that home_xg > 5.0 raises ValueError."""
        with pytest.raises(ValueError):
            predict_match_goals(5.5, 1.0)

    def test_xg_validation_home_negative(self) -> None:
        """Test that negative home_xg raises ValueError."""
        with pytest.raises(ValueError):
            predict_match_goals(-0.5, 1.0)

    def test_xg_validation_away_high(self) -> None:
        """Test that away_xg > 5.0 raises ValueError."""
        with pytest.raises(ValueError):
            predict_match_goals(1.0, 5.5)

    def test_xg_validation_away_negative(self) -> None:
        """Test that negative away_xg raises ValueError."""
        with pytest.raises(ValueError):
            predict_match_goals(1.0, -0.5)

    def test_correlation_factor_validation_high(self) -> None:
        """Test that correlation_factor > 1 raises ValueError."""
        with pytest.raises(ValueError):
            predict_match_goals(1.5, 1.2, correlation_factor=1.5)

    def test_correlation_factor_validation_negative(self) -> None:
        """Test that negative correlation_factor raises ValueError."""
        with pytest.raises(ValueError):
            predict_match_goals(1.5, 1.2, correlation_factor=-0.1)

    def test_zero_correlation_factor(self) -> None:
        """Test prediction with zero correlation (independent)."""
        result = predict_match_goals(1.5, 1.2, correlation_factor=0.0)
        assert result["probability"] > 0

    def test_high_correlation_factor(self) -> None:
        """Test prediction with high correlation."""
        result_low = predict_match_goals(1.5, 1.2, correlation_factor=0.0)
        result_high = predict_match_goals(1.5, 1.2, correlation_factor=0.9)

        # High correlation with extreme scores should have lower probability
        if result_high["home_goals"] + result_high["away_goals"] > 4:
            assert result_high["probability"] < result_low["probability"]

    def test_very_high_xg_prediction(self) -> None:
        """Test prediction with high xG values."""
        result = predict_match_goals(4.0, 3.5)
        assert result["confidence"] > 0.5
        assert result["home_goals"] >= 0

    def test_very_low_xg_prediction(self) -> None:
        """Test prediction with low xG values."""
        result = predict_match_goals(0.2, 0.3)
        # More likely to be 0 goals
        assert result["confidence"] >= 0.3

    def test_confidence_increases_with_xg(self) -> None:
        """Test that confidence increases with higher xG."""
        result_low = predict_match_goals(0.5, 0.5)
        result_high = predict_match_goals(2.0, 2.0)
        assert result_high["confidence"] > result_low["confidence"]

    def test_equal_xg_teams(self) -> None:
        """Test prediction when teams have equal xG."""
        result = predict_match_goals(1.5, 1.5)
        # Should predict realistic goal counts
        assert result["home_goals"] >= 0
        assert result["away_goals"] >= 0


class TestEstimateGoalDistribution:
    """Test suite for estimate_goal_distribution function."""

    @pytest.fixture
    def valid_team_stats(self) -> dict:
        """Fixture for valid team statistics."""
        return {
            "goals_for": 1.8,
            "goals_against": 1.2,
            "matches_played": 5,
            "form_factor": 1.1,
        }

    @pytest.fixture
    def valid_opponent_stats(self) -> dict:
        """Fixture for valid opponent statistics."""
        return {
            "goals_for": 1.5,
            "goals_against": 1.4,
            "defense_rating": 0.95,
        }

    @pytest.fixture
    def valid_context(self) -> dict:
        """Fixture for valid context."""
        return {
            "home_away": "home",
            "injury_status": "normal",
            "head_to_head": {},
        }

    def test_basic_distribution(
        self, valid_team_stats, valid_opponent_stats, valid_context
    ) -> None:
        """Test basic goal distribution estimation."""
        distribution, confidence = estimate_goal_distribution(
            valid_team_stats, valid_opponent_stats, valid_context
        )

        assert isinstance(distribution, dict)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        # Check probabilities sum to ~1
        total_prob = sum(distribution.values())
        assert 0.95 < total_prob <= 1.05

    def test_missing_team_stats_key(self, valid_opponent_stats, valid_context) -> None:
        """Test KeyError when team_stats missing required key."""
        incomplete_stats = {"goals_for": 1.8, "goals_against": 1.2}
        with pytest.raises(KeyError):
            estimate_goal_distribution(
                incomplete_stats, valid_opponent_stats, valid_context
            )

    def test_missing_opponent_stats_key(self, valid_team_stats, valid_context) -> None:
        """Test KeyError when opponent_stats missing required key."""
        incomplete_stats = {"goals_for": 1.5}
        with pytest.raises(KeyError):
            estimate_goal_distribution(valid_team_stats, incomplete_stats, valid_context)

    def test_missing_context_key(self, valid_team_stats, valid_opponent_stats) -> None:
        """Test KeyError when context missing required key."""
        incomplete_context = {"home_away": "home"}
        with pytest.raises(KeyError):
            estimate_goal_distribution(
                valid_team_stats, valid_opponent_stats, incomplete_context
            )

    def test_negative_goals_for_raises_error(
        self, valid_opponent_stats, valid_context
    ) -> None:
        """Test ValueError for negative goals_for."""
        bad_stats = {
            "goals_for": -1.0,
            "goals_against": 1.2,
            "matches_played": 5,
            "form_factor": 1.0,
        }
        with pytest.raises(ValueError):
            estimate_goal_distribution(bad_stats, valid_opponent_stats, valid_context)

    def test_zero_matches_played_raises_error(
        self, valid_opponent_stats, valid_context
    ) -> None:
        """Test ValueError for zero matches_played."""
        bad_stats = {
            "goals_for": 1.8,
            "goals_against": 1.2,
            "matches_played": 0,
            "form_factor": 1.0,
        }
        with pytest.raises(ValueError):
            estimate_goal_distribution(bad_stats, valid_opponent_stats, valid_context)

    def test_home_advantage_boost(
        self, valid_team_stats, valid_opponent_stats, valid_context
    ) -> None:
        """Test that home_away context affects distribution."""
        valid_context["home_away"] = "home"
        dist_home, conf_home = estimate_goal_distribution(
            valid_team_stats, valid_opponent_stats, valid_context
        )

        valid_context["home_away"] = "away"
        dist_away, conf_away = estimate_goal_distribution(
            valid_team_stats, valid_opponent_stats, valid_context
        )

        # Home team should have higher probability of scoring more goals
        # at higher goal counts
        home_higher_goals = sum(
            v for k, v in dist_home.items() if k >= 2
        )
        away_higher_goals = sum(
            v for k, v in dist_away.items() if k >= 2
        )
        assert home_higher_goals > away_higher_goals

    def test_injury_status_major(
        self, valid_team_stats, valid_opponent_stats, valid_context
    ) -> None:
        """Test that major injuries reduce expected goals."""
        valid_context["injury_status"] = "normal"
        dist_normal, _ = estimate_goal_distribution(
            valid_team_stats, valid_opponent_stats, valid_context
        )

        valid_context["injury_status"] = "major"
        dist_injured, _ = estimate_goal_distribution(
            valid_team_stats, valid_opponent_stats, valid_context
        )

        # Injured team should have lower expected goals
        normal_expected = sum(k * v for k, v in dist_normal.items())
        injured_expected = sum(k * v for k, v in dist_injured.items())
        assert injured_expected < normal_expected

    def test_confidence_increases_with_matches(
        self, valid_opponent_stats, valid_context
    ) -> None:
        """Test that confidence increases with more matches played."""
        stats_few = {
            "goals_for": 1.8,
            "goals_against": 1.2,
            "matches_played": 2,
            "form_factor": 1.0,
        }
        _, conf_few = estimate_goal_distribution(
            stats_few, valid_opponent_stats, valid_context
        )

        stats_many = {
            "goals_for": 1.8,
            "goals_against": 1.2,
            "matches_played": 20,
            "form_factor": 1.0,
        }
        _, conf_many = estimate_goal_distribution(
            stats_many, valid_opponent_stats, valid_context
        )

        assert conf_many > conf_few

    def test_form_factor_impact(self, valid_opponent_stats, valid_context) -> None:
        """Test that form_factor affects expected goals."""
        stats_poor_form = {
            "goals_for": 1.8,
            "goals_against": 1.2,
            "matches_played": 5,
            "form_factor": 0.7,
        }
        dist_poor, _ = estimate_goal_distribution(
            stats_poor_form, valid_opponent_stats, valid_context
        )

        stats_good_form = {
            "goals_for": 1.8,
            "goals_against": 1.2,
            "matches_played": 5,
            "form_factor": 1.5,
        }
        dist_good, _ = estimate_goal_distribution(
            stats_good_form, valid_opponent_stats, valid_context
        )

        poor_expected = sum(k * v for k, v in dist_poor.items())
        good_expected = sum(k * v for k, v in dist_good.items())
        assert good_expected > poor_expected


class TestEstimateXgForMatch:
    """Test suite for estimate_xg_for_match function."""

    @pytest.fixture
    def valid_season_data(self) -> dict:
        """Fixture for valid season data."""
        return {
            "teams": {
                "MAN": {
                    "goals_for": 2.1,
                    "goals_against": 0.8,
                    "matches_played": 5,
                    "form_factor": 1.1,
                },
                "LIV": {
                    "goals_for": 1.9,
                    "goals_against": 1.0,
                    "matches_played": 5,
                    "form_factor": 0.95,
                },
            },
            "matches": [],
            "gameweek": 1,
        }

    def test_basic_xg_estimation(self, valid_season_data) -> None:
        """Test basic xG estimation."""
        result = estimate_xg_for_match("MAN", "LIV", valid_season_data)

        assert isinstance(result, dict)
        assert "home_xg" in result
        assert "away_xg" in result
        assert 0 <= result["home_xg"] <= 5.0
        assert 0 <= result["away_xg"] <= 5.0

    def test_missing_teams_key(self, valid_season_data) -> None:
        """Test ValueError when 'teams' key missing."""
        bad_data = {"matches": [], "gameweek": 1}
        with pytest.raises(ValueError):
            estimate_xg_for_match("MAN", "LIV", bad_data)

    def test_missing_matches_key(self, valid_season_data) -> None:
        """Test ValueError when 'matches' key missing."""
        bad_data = {"teams": valid_season_data["teams"], "gameweek": 1}
        with pytest.raises(ValueError):
            estimate_xg_for_match("MAN", "LIV", bad_data)

    def test_missing_gameweek_key(self, valid_season_data) -> None:
        """Test ValueError when 'gameweek' key missing."""
        bad_data = {"teams": valid_season_data["teams"], "matches": []}
        with pytest.raises(ValueError):
            estimate_xg_for_match("MAN", "LIV", bad_data)

    def test_home_team_not_found(self, valid_season_data) -> None:
        """Test KeyError when home team not in season_data."""
        with pytest.raises(KeyError):
            estimate_xg_for_match("UNKNOWN", "LIV", valid_season_data)

    def test_away_team_not_found(self, valid_season_data) -> None:
        """Test KeyError when away team not in season_data."""
        with pytest.raises(KeyError):
            estimate_xg_for_match("MAN", "UNKNOWN", valid_season_data)

    def test_missing_team_data_key(self, valid_season_data) -> None:
        """Test ValueError when team data missing required key."""
        valid_season_data["teams"]["MAN"] = {"goals_for": 2.1}
        with pytest.raises(ValueError):
            estimate_xg_for_match("MAN", "LIV", valid_season_data)

    def test_home_advantage_in_xg(self, valid_season_data) -> None:
        """Test that home team gets xG advantage."""
        result_home = estimate_xg_for_match("MAN", "LIV", valid_season_data)

        # Swap teams to make LIV home
        result_away = estimate_xg_for_match("LIV", "MAN", valid_season_data)

        # MAN home xG should be higher than MAN away xG
        assert result_home["home_xg"] > result_away["away_xg"]

    def test_stronger_team_higher_xg(self, valid_season_data) -> None:
        """Test that stronger attacking team gets higher xG."""
        # MAN has 2.1 goals_for, LIV has 1.9
        result = estimate_xg_for_match("MAN", "LIV", valid_season_data)

        # MAN should have higher xG
        assert result["home_xg"] > result["away_xg"]

    def test_better_defense_reduces_opponent_xg(self, valid_season_data) -> None:
        """Test that better defense reduces opponent xG."""
        # MAN has 0.8 goals_against, LIV has 1.0
        # So LIV (away) should score less against MAN's defense
        result = estimate_xg_for_match("MAN", "LIV", valid_season_data)

        assert result["away_xg"] < 1.5  # Against stronger defense

    def test_form_factor_impact_on_xg(self, valid_season_data) -> None:
        """Test that form_factor affects xG calculation."""
        # MAN has 1.1 form (good form), LIV has 0.95 (slightly bad)
        result = estimate_xg_for_match("MAN", "LIV", valid_season_data)

        # MAN with good form should have higher xG
        assert result["home_xg"] > result["away_xg"]

    def test_xg_values_in_realistic_range(self, valid_season_data) -> None:
        """Test that xG values are in realistic range."""
        result = estimate_xg_for_match("MAN", "LIV", valid_season_data)

        # Realistic match xG should be between 0 and 4
        assert 0 <= result["home_xg"] <= 4.0
        assert 0 <= result["away_xg"] <= 4.0
        # Some difference expected for match balance
        assert abs(result["home_xg"] - result["away_xg"]) < 2.0

    def test_symmetric_teams_similar_xg(self) -> None:
        """Test that identical teams produce similar xG."""
        season_data = {
            "teams": {
                "TEAM_A": {
                    "goals_for": 1.8,
                    "goals_against": 1.2,
                    "matches_played": 5,
                    "form_factor": 1.0,
                },
                "TEAM_B": {
                    "goals_for": 1.8,
                    "goals_against": 1.2,
                    "matches_played": 5,
                    "form_factor": 1.0,
                },
            },
            "matches": [],
            "gameweek": 1,
        }

        result = estimate_xg_for_match("TEAM_A", "TEAM_B", season_data)

        # Home team should have slight advantage
        assert result["home_xg"] > result["away_xg"]
        # But difference should be small (~0.2-0.4)
        assert 0.1 < (result["home_xg"] - result["away_xg"]) < 0.5


class TestIntegration:
    """Integration tests across multiple functions."""

    def test_pipeline_estimation_to_prediction(self) -> None:
        """Test full pipeline from xG estimation to goal prediction."""
        # Step 1: Estimate xG for match
        season_data = {
            "teams": {
                "HOME": {
                    "goals_for": 2.0,
                    "goals_against": 0.9,
                    "matches_played": 5,
                    "form_factor": 1.1,
                },
                "AWAY": {
                    "goals_for": 1.6,
                    "goals_against": 1.3,
                    "matches_played": 5,
                    "form_factor": 0.95,
                },
            },
            "matches": [],
            "gameweek": 1,
        }

        xg_result = estimate_xg_for_match("HOME", "AWAY", season_data)
        assert "home_xg" in xg_result
        assert "away_xg" in xg_result

        # Step 2: Predict goals using xG
        prediction = predict_match_goals(
            xg_result["home_xg"], xg_result["away_xg"], correlation_factor=0.2
        )
        assert "home_goals" in prediction
        assert "away_goals" in prediction
        assert "probability" in prediction
        assert "confidence" in prediction

        # Step 3: Get goal distribution
        team_stats = {
            "goals_for": 2.0,
            "goals_against": 0.9,
            "matches_played": 5,
            "form_factor": 1.1,
        }
        opponent_stats = {
            "goals_for": 1.6,
            "goals_against": 1.3,
            "defense_rating": 0.95,
        }
        context = {
            "home_away": "home",
            "injury_status": "normal",
            "head_to_head": {},
        }

        distribution, confidence = estimate_goal_distribution(
            team_stats, opponent_stats, context
        )
        assert len(distribution) > 0
        assert 0 <= confidence <= 1

    def test_multiple_predictions_consistency(self) -> None:
        """Test that predictions with same input are consistent."""
        result1 = predict_match_goals(1.5, 1.2)
        result2 = predict_match_goals(1.5, 1.2)

        # Should produce same goal counts (deterministic for most likely outcome)
        assert result1["home_goals"] == result2["home_goals"]
        assert result1["away_goals"] == result2["away_goals"]
