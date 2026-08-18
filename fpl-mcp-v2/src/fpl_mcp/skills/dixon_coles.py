"""Dixon-Coles bivariate Poisson model with Monte Carlo scoreline simulation.

Replaces the naive PPG-derived Elo heuristic (which was shown to systematically
underestimate draw probability, a documented failure mode of skill-gap-only
rating models) with a model fitted on match-level goal data.

Reference: Dixon, M.J. and Coles, S.G. (1997), "Modelling Association Football
Scores and Inefficiencies in the Football Betting Market", Journal of the Royal
Statistical Society: Series C, 46(2), 265-280.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.optimize import minimize

DEFAULT_MAX_GOALS = 10
DEFAULT_XI = 0.0018  # time-decay rate (per day); 0 disables decay


@dataclass
class DixonColesParams:
    """Fitted Dixon-Coles parameters."""

    teams: list[str]
    attack: dict[str, float]
    defense: dict[str, float]
    home_advantage: float
    rho: float
    log_likelihood: float


def _tau(x: int, y: int, lambda_: float, mu: float, rho: float) -> float:
    """Dixon-Coles low-score correlation adjustment.

    Corrects the independent-Poisson assumption for the four scorelines where
    real matches deviate most from it: 0-0, 1-0, 0-1, 1-1. This is precisely
    the mechanism that fixes draw-probability underestimation, since plain
    independent Poisson gets low, draw-heavy scorelines wrong.
    """
    if x == 0 and y == 0:
        return 1 - (lambda_ * mu * rho)
    if x == 0 and y == 1:
        return 1 + (lambda_ * rho)
    if x == 1 and y == 0:
        return 1 + (mu * rho)
    if x == 1 and y == 1:
        return 1 - rho
    return 1.0


def fit_dixon_coles(
    matches: list[dict[str, Any]],
    xi: float = DEFAULT_XI,
    max_days_ago: float | None = None,
) -> DixonColesParams:
    """Fit team attack/defense strengths and rho via maximum likelihood.

    Args:
        matches: List of dicts with keys: home_team, away_team, home_goals,
            away_goals, and optionally days_ago (for time-decay weighting;
            more recent matches weighted more heavily via exp(-xi * days_ago)).
        xi: Time-decay rate. 0.0018/day matches Dixon & Coles' original paper
            (half-life ~1 year). Set to 0 to weight all matches equally.
        max_days_ago: If set, matches older than this are dropped entirely.

    Returns:
        Fitted DixonColesParams.

    Raises:
        ValueError: If matches is empty or fewer than 2 teams are present.
    """
    if not matches:
        raise ValueError("matches must not be empty")

    if max_days_ago is not None:
        matches = [m for m in matches if m.get("days_ago", 0) <= max_days_ago]
        if not matches:
            raise ValueError("no matches remain after max_days_ago filter")

    teams = sorted({m["home_team"] for m in matches} | {m["away_team"] for m in matches})
    if len(teams) < 2:
        raise ValueError("at least 2 distinct teams are required")

    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}

    weights = np.array(
        [math.exp(-xi * m.get("days_ago", 0)) for m in matches]
    )
    home_idx = np.array([idx[m["home_team"]] for m in matches])
    away_idx = np.array([idx[m["away_team"]] for m in matches])
    home_goals = np.array([m["home_goals"] for m in matches], dtype=float)
    away_goals = np.array([m["away_goals"] for m in matches], dtype=float)

    def unpack(params: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, float]:
        attack = params[:n]
        defense = params[n : 2 * n]
        home_adv = params[2 * n]
        rho = params[2 * n + 1]
        return attack, defense, home_adv, rho

    def neg_log_likelihood(params: np.ndarray) -> float:
        attack, defense, home_adv, rho = unpack(params)

        lam = np.exp(attack[home_idx] - defense[away_idx] + home_adv)
        mu = np.exp(attack[away_idx] - defense[home_idx])

        # Poisson log-pmf for each match
        log_p_home = home_goals * np.log(lam) - lam - np.array(
            [math.lgamma(g + 1) for g in home_goals]
        )
        log_p_away = away_goals * np.log(mu) - mu - np.array(
            [math.lgamma(g + 1) for g in away_goals]
        )

        tau_vals = np.array(
            [
                _tau(int(hg), int(ag), lam[i], mu[i], rho)
                for i, (hg, ag) in enumerate(zip(home_goals, away_goals))
            ]
        )
        tau_vals = np.clip(tau_vals, 1e-10, None)  # guard against invalid rho region

        log_likelihood = weights * (log_p_home + log_p_away + np.log(tau_vals))
        return -np.sum(log_likelihood)

    # Initial guess: zero attack/defense (average team), small home advantage, rho=0
    x0 = np.zeros(2 * n + 2)
    x0[2 * n] = 0.3  # home advantage prior

    # Constraint: mean attack = 0 (identifiability; otherwise attack/defense
    # can drift by an arbitrary additive constant against each other)
    constraints = [
        {"type": "eq", "fun": lambda p, n=n: np.sum(p[:n]) / n}
    ]

    result = minimize(
        neg_log_likelihood,
        x0,
        method="SLSQP",
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-8},
    )

    attack, defense, home_adv, rho = unpack(result.x)

    return DixonColesParams(
        teams=teams,
        attack=dict(zip(teams, attack.tolist())),
        defense=dict(zip(teams, defense.tolist())),
        home_advantage=float(home_adv),
        rho=float(rho),
        log_likelihood=float(-result.fun),
    )


def score_matrix(
    params: DixonColesParams,
    home_team: str,
    away_team: str,
    max_goals: int = DEFAULT_MAX_GOALS,
) -> np.ndarray:
    """Compute the full P(home=i, away=j) matrix for a fixture.

    Args:
        params: Fitted Dixon-Coles parameters.
        home_team: Home team name (must be in params.teams).
        away_team: Away team name (must be in params.teams).
        max_goals: Grid size (0..max_goals for each side).

    Returns:
        (max_goals+1) x (max_goals+1) matrix of joint probabilities.

    Raises:
        KeyError: If either team was not in the fitted data.
    """
    lam = math.exp(
        params.attack[home_team] - params.defense[away_team] + params.home_advantage
    )
    mu = math.exp(params.attack[away_team] - params.defense[home_team])

    home_probs = np.array(
        [math.exp(-lam) * lam**k / math.factorial(k) for k in range(max_goals + 1)]
    )
    away_probs = np.array(
        [math.exp(-mu) * mu**k / math.factorial(k) for k in range(max_goals + 1)]
    )

    matrix = np.outer(home_probs, away_probs)

    for x in range(2):
        for y in range(2):
            matrix[x, y] *= _tau(x, y, lam, mu, params.rho)

    matrix = np.clip(matrix, 0, None)
    matrix /= matrix.sum()  # renormalize after tau adjustment and clipping
    return matrix


def predict_match_outcome_dc(
    params: DixonColesParams,
    home_team: str,
    away_team: str,
    max_goals: int = DEFAULT_MAX_GOALS,
) -> dict[str, float]:
    """1X2 probabilities directly from the fitted score matrix (exact, no sampling)."""
    matrix = score_matrix(params, home_team, away_team, max_goals)
    home_win = float(np.tril(matrix, -1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, 1).sum())
    return {
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "confidence": max(home_win, draw, away_win),
    }


def monte_carlo_markets(
    params: DixonColesParams,
    home_team: str,
    away_team: str,
    n_simulations: int = 100_000,
    max_goals: int = DEFAULT_MAX_GOALS,
    seed: int | None = None,
) -> dict[str, Any]:
    """Simulate scorelines by sampling from the fitted joint distribution.

    Useful beyond simple 1X2 for markets that combine multiple conditions
    (e.g. "Arsenal win AND over 2.5 goals" parlays) where the correlation
    between markets matters and can't be derived by multiplying independent
    market probabilities together.

    Args:
        params: Fitted Dixon-Coles parameters.
        home_team: Home team name.
        away_team: Away team name.
        n_simulations: Number of Monte Carlo draws.
        max_goals: Grid size used to build the sampling distribution.
        seed: Optional RNG seed for reproducibility.

    Returns:
        Dict with 1X2, BTTS, over/under 0.5-4.5, and correct-score
        probabilities, all estimated from the same simulated sample set
        (so they're mutually consistent, unlike combining separate formulas).
    """
    matrix = score_matrix(params, home_team, away_team, max_goals)
    flat = matrix.flatten()
    flat = flat / flat.sum()

    rng = np.random.default_rng(seed)
    draws = rng.choice(len(flat), size=n_simulations, p=flat)
    home_goals_sim = draws // (max_goals + 1)
    away_goals_sim = draws % (max_goals + 1)

    total_goals = home_goals_sim + away_goals_sim
    both_scored = (home_goals_sim > 0) & (away_goals_sim > 0)

    outcome_probs = {
        "home_win": float(np.mean(home_goals_sim > away_goals_sim)),
        "draw": float(np.mean(home_goals_sim == away_goals_sim)),
        "away_win": float(np.mean(home_goals_sim < away_goals_sim)),
    }

    over_under = {
        f"over_{t}": float(np.mean(total_goals > t)) for t in (0.5, 1.5, 2.5, 3.5, 4.5)
    }

    btts = {
        "btts_yes": float(np.mean(both_scored)),
        "btts_no": float(np.mean(~both_scored)),
    }

    # Top correct scores by simulated frequency
    scores, counts = np.unique(
        list(zip(home_goals_sim.tolist(), away_goals_sim.tolist())),
        axis=0,
        return_counts=True,
    )
    order = np.argsort(-counts)[:5]
    top_scores = [
        {"score": f"{int(scores[i][0])}-{int(scores[i][1])}", "probability": float(counts[i] / n_simulations)}
        for i in order
    ]

    return {
        "n_simulations": n_simulations,
        "outcome": outcome_probs,
        "over_under": over_under,
        "btts": btts,
        "top_correct_scores": top_scores,
        "confidence": max(outcome_probs.values()),
    }
