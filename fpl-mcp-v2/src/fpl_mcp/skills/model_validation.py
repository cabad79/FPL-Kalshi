"""Backtesting and calibration validation for match outcome prediction models.

A model that "looks close to market prices" on a handful of matches is not
validated. Proper validation means: fit on past data only, predict held-out
future matches never seen during fitting, and check whether predicted
probabilities actually match observed outcome frequencies (calibration) and
beat a naive baseline on proper scoring rules (log-loss, Brier score).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .dixon_coles import fit_dixon_coles, predict_match_outcome_dc


@dataclass
class CalibrationBin:
    """One bin of a reliability diagram."""

    predicted_range: tuple[float, float]
    n_predictions: int
    mean_predicted_probability: float
    observed_frequency: float


@dataclass
class BacktestResult:
    """Full backtest output for one model on one holdout set."""

    n_train_matches: int
    n_test_matches: int
    log_loss: float
    brier_score: float
    baseline_log_loss: float
    baseline_brier_score: float
    calibration: list[CalibrationBin]
    per_outcome_accuracy: dict[str, float]


def _log_loss(y_true: np.ndarray, y_prob: np.ndarray, eps: float = 1e-15) -> float:
    """Multiclass log-loss (lower is better; 0 = perfect)."""
    y_prob = np.clip(y_prob, eps, 1 - eps)
    return float(-np.mean(np.sum(y_true * np.log(y_prob), axis=1)))


def _brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Multiclass Brier score (lower is better; 0 = perfect)."""
    return float(np.mean(np.sum((y_prob - y_true) ** 2, axis=1)))


def calibration_check(
    predicted_probs: list[float], outcomes: list[bool], n_bins: int = 10
) -> list[CalibrationBin]:
    """Build a reliability diagram: does predicted probability match reality?

    Args:
        predicted_probs: Model's predicted probability of the event, one per
            observation (e.g. predicted home-win probability for each match).
        outcomes: Whether the event actually happened, same length/order.
        n_bins: Number of equal-width probability bins.

    Returns:
        List of CalibrationBin, one per non-empty bin. A well-calibrated
        model has observed_frequency close to mean_predicted_probability in
        every bin.
    """
    probs = np.array(predicted_probs)
    obs = np.array(outcomes, dtype=float)

    edges = np.linspace(0, 1, n_bins + 1)
    bins: list[CalibrationBin] = []

    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (probs >= lo) & (probs < hi) if i < n_bins - 1 else (probs >= lo) & (probs <= hi)
        if not mask.any():
            continue
        bins.append(
            CalibrationBin(
                predicted_range=(float(lo), float(hi)),
                n_predictions=int(mask.sum()),
                mean_predicted_probability=float(probs[mask].mean()),
                observed_frequency=float(obs[mask].mean()),
            )
        )
    return bins


def backtest_dixon_coles(
    matches: list[dict[str, Any]],
    train_fraction: float = 0.7,
    n_calibration_bins: int = 10,
    xi: float = 0.0,
) -> BacktestResult:
    """Chronological holdout backtest: fit on the past, predict the future.

    Args:
        matches: Full match list, each with home_team, away_team, home_goals,
            away_goals, and utc_date (ISO string). Used both for the
            chronological split and, when xi > 0, to weight training matches
            by real recency (days before the most recent training match).
        xi: Time-decay rate passed to fit_dixon_coles. 0.0 weights every
            training match equally (fine for a single season); a positive
            value (e.g. 0.0018, the Dixon & Coles paper default) down-weights
            older matches — important when pooling multiple seasons, since a
            team's true strength drifts season to season (transfers, managers,
            promotion/relegation of opponents) and equal weighting blurs that.
        train_fraction: Fraction of matches (by chronological order) used to
            fit the model. The remainder is the untouched holdout test set.
        n_calibration_bins: Bins for the home-win reliability diagram.

    Returns:
        BacktestResult with log-loss, Brier score (both vs. a naive baseline
        that always predicts the training set's overall home/draw/away rates),
        and a calibration breakdown for the home-win probability.

    Raises:
        ValueError: If there are too few matches to form a meaningful split.
    """
    if len(matches) < 20:
        raise ValueError("need at least 20 matches for a meaningful backtest")

    ordered = sorted(matches, key=lambda m: m["utc_date"])
    split = int(len(ordered) * train_fraction)
    train, test = ordered[:split], ordered[split:]
    if not test:
        raise ValueError("train_fraction leaves no test matches")

    from datetime import datetime

    def parse_date(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    reference_date = parse_date(train[-1]["utc_date"])
    fit_matches = [
        {
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "home_goals": m["home_goals"],
            "away_goals": m["away_goals"],
            "days_ago": (reference_date - parse_date(m["utc_date"])).days,
        }
        for m in train
    ]
    params = fit_dixon_coles(fit_matches, xi=xi)

    # Naive baseline: training-set overall outcome rates, applied uniformly
    train_outcomes = np.array(
        [
            [m["home_goals"] > m["away_goals"], m["home_goals"] == m["away_goals"], m["home_goals"] < m["away_goals"]]
            for m in train
        ],
        dtype=float,
    )
    baseline_probs = train_outcomes.mean(axis=0)

    y_true, y_pred_dc, y_pred_baseline = [], [], []
    home_win_predicted, home_win_actual = [], []
    correct_by_outcome = {"home_win": [], "draw": [], "away_win": []}

    fitted_teams = set(params.teams)

    for m in test:
        if m["home_team"] not in fitted_teams or m["away_team"] not in fitted_teams:
            continue  # promoted/relegated team with no fitted parameters — skip, don't guess

        pred = predict_match_outcome_dc(params, m["home_team"], m["away_team"])
        probs = [pred["home_win"], pred["draw"], pred["away_win"]]

        if m["home_goals"] > m["away_goals"]:
            actual = [1.0, 0.0, 0.0]
            actual_label = "home_win"
        elif m["home_goals"] == m["away_goals"]:
            actual = [0.0, 1.0, 0.0]
            actual_label = "draw"
        else:
            actual = [0.0, 0.0, 1.0]
            actual_label = "away_win"

        y_true.append(actual)
        y_pred_dc.append(probs)
        y_pred_baseline.append(baseline_probs.tolist())

        home_win_predicted.append(pred["home_win"])
        home_win_actual.append(m["home_goals"] > m["away_goals"])

        predicted_label = ["home_win", "draw", "away_win"][int(np.argmax(probs))]
        correct_by_outcome.setdefault(predicted_label, []).append(predicted_label == actual_label)

    if not y_true:
        raise ValueError("no test matches had both teams present in the training fit")

    y_true_arr = np.array(y_true)
    y_pred_dc_arr = np.array(y_pred_dc)
    y_pred_baseline_arr = np.array(y_pred_baseline)

    per_outcome_accuracy = {
        k: (sum(v) / len(v) if v else float("nan")) for k, v in correct_by_outcome.items()
    }

    return BacktestResult(
        n_train_matches=len(train),
        n_test_matches=len(y_true),
        log_loss=_log_loss(y_true_arr, y_pred_dc_arr),
        brier_score=_brier_score(y_true_arr, y_pred_dc_arr),
        baseline_log_loss=_log_loss(y_true_arr, y_pred_baseline_arr),
        baseline_brier_score=_brier_score(y_true_arr, y_pred_baseline_arr),
        calibration=calibration_check(home_win_predicted, home_win_actual, n_calibration_bins),
        per_outcome_accuracy=per_outcome_accuracy,
    )
