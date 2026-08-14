"""Market Prediction and Smart Order Placement Engine.

This module provides:
- OddsComparison: Compare model predictions to market odds
- ArbitrageDetector: Find market inefficiencies
- GoalMarketOptimizer: Connect xG to goal range bets
- PlayerPropsMapper: Match player analysis to goal scorer contracts
- BettingStrategies: Multi-market strategy implementation

Author: SONNET-3 (Kalshi Market Integration Engineer)
Date: 2026-08-14
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fpl_mcp.kalshi_client import (
    KalshiContract,
    KalshiMarketClient,
    MarketCategory,
    Order,
    OrderSide,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================


class BettingSignal(str, Enum):
    """Trading signal strength."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    SKIP = "skip"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class StrategyType(str, Enum):
    """Betting strategy types."""
    UNDERVALUED_XG = "undervalued_xg"
    BTTS_GRINDER = "btts_grinder"
    PARLAYS = "parlays"
    HEDGING = "hedging"
    ARBITRAGE = "arbitrage"


@dataclass
class PredictionComparison:
    """Comparison between model prediction and market odds."""
    contract_id: str
    market_category: MarketCategory
    model_probability: float  # Model's predicted probability
    market_odds: float  # Decimal odds (Kalshi cents format)
    implied_probability: float  # Market's implied probability
    value: float  # Edge: model_prob - implied_prob
    kelly_fraction: float  # Kelly criterion recommendation
    signal: BettingSignal
    confidence: float  # Our confidence in the prediction (0-1)
    recommended_stake: float  # Recommended position size
    max_position: float  # Position limit due to liquidity
    rationale: str  # Explanation of the signal

    @property
    def edge_percent(self) -> float:
        """Calculate edge as percentage."""
        return self.value * 100

    @property
    def is_valuable(self) -> bool:
        """Check if opportunity has positive expected value."""
        return self.value > 0.02  # At least 2% edge


@dataclass
class ArbitrageOpportunity:
    """Cross-market arbitrage opportunity."""
    market_ids: List[str]  # Contracts involved
    contracts: Dict[str, KalshiContract]
    implied_overround: float  # Sum of implied probabilities > 100%
    profit_potential: float  # Potential profit percentage
    stake_allocation: Dict[str, float]  # How to allocate stake across markets
    exposure: float  # Maximum loss possible
    is_profitable: bool  # Whether arbitrage has positive EV

    @property
    def return_percent(self) -> float:
        """Calculate potential return as percentage."""
        if self.implied_overround <= 0:
            return 0.0
        return (self.implied_overround - 1.0) * 100


@dataclass
class GoalMarketRecommendation:
    """Recommendation for goal-based markets."""
    match_id: str
    home_team: str
    away_team: str
    home_xg: float
    away_xg: float
    over_1_5_prob: float
    over_2_5_prob: float
    over_3_5_prob: float
    btts_probability: float
    recommended_markets: Dict[str, BettingSignal]
    confidence: float
    analysis: str


@dataclass
class PlayerPropRecommendation:
    """Recommendation for player prop markets."""
    player_id: str
    player_name: str
    team: str
    opponent: str
    match_id: str
    model_probability: float
    market_implied_probability: float
    model_xg: float
    expected_xg: float
    confidence: float
    signal: BettingSignal
    rationale: str


# ============================================================================
# ODDS COMPARISON
# ============================================================================


class OddsComparison:
    """Compare model predictions to market odds and generate signals."""

    MINIMUM_CONFIDENCE = 0.55  # Only consider predictions >55%
    MAXIMUM_CONFIDENCE = 0.95  # Cap recommendations at 95%
    MINIMUM_EDGE = 0.02  # Need at least 2% edge to consider valuable

    @staticmethod
    def compare(
        contract: KalshiContract,
        model_probability: float,
        confidence: float,
        implied_probability: Optional[float] = None,
    ) -> PredictionComparison:
        """Compare model prediction to market odds.

        Args:
            contract: Kalshi contract
            model_probability: Our predicted probability (0-1)
            confidence: Our confidence in prediction (0-1)
            implied_probability: Optional override for implied probability

        Returns:
            PredictionComparison with signal and recommendation
        """
        if implied_probability is None:
            implied_probability = contract.implied_probability_yes()

        # Clamp to valid ranges
        model_probability = max(0.01, min(0.99, model_probability))
        confidence = max(0.0, min(1.0, confidence))
        implied_probability = max(0.01, min(0.99, implied_probability))

        # Calculate edge
        value = model_probability - implied_probability

        # Generate signal
        signal = OddsComparison._generate_signal(
            value, confidence, model_probability
        )

        # Calculate Kelly recommendation
        kelly_fraction = OddsComparison._calculate_kelly_recommendation(
            value, confidence, model_probability
        )

        # Estimate recommended stake (scaled by confidence and edge)
        recommended_stake = kelly_fraction * 100  # Scale for position sizing

        # Position limit from liquidity
        max_position = contract.liquidity * 0.05  # Use max 5% of available liquidity

        rationale = OddsComparison._generate_rationale(
            value, confidence, signal, model_probability, implied_probability
        )

        return PredictionComparison(
            contract_id=contract.contract_id,
            market_category=contract.category,
            model_probability=model_probability,
            market_odds=contract.yes_ask,
            implied_probability=implied_probability,
            value=value,
            kelly_fraction=kelly_fraction,
            signal=signal,
            confidence=confidence,
            recommended_stake=recommended_stake,
            max_position=max_position,
            rationale=rationale,
        )

    @staticmethod
    def _generate_signal(
        value: float, confidence: float, model_probability: float
    ) -> BettingSignal:
        """Generate trading signal based on edge and confidence."""
        # Must have minimum confidence
        if confidence < OddsComparison.MINIMUM_CONFIDENCE:
            return BettingSignal.SKIP

        # No signal if no edge
        if abs(value) < OddsComparison.MINIMUM_EDGE:
            return BettingSignal.SKIP

        # Buy signals (positive value)
        if value > 0:
            if confidence > 0.85 and value > 0.10:
                return BettingSignal.STRONG_BUY
            elif confidence > 0.75 and value > 0.05:
                return BettingSignal.BUY
            elif value > 0.02:
                return BettingSignal.WEAK_BUY

        # Sell signals (negative value)
        else:
            if confidence > 0.85 and value < -0.10:
                return BettingSignal.STRONG_SELL
            elif confidence > 0.75 and value < -0.05:
                return BettingSignal.SELL
            elif value < -0.02:
                return BettingSignal.WEAK_SELL

        return BettingSignal.SKIP

    @staticmethod
    def _calculate_kelly_recommendation(
        value: float, confidence: float, model_probability: float
    ) -> float:
        """Calculate Kelly criterion recommendation."""
        if value <= 0:
            return 0.0

        # Base Kelly: f = (p * odds - 1) / (odds - 1)
        # For binary outcomes: f = p - q where p + q = 1
        kelly_base = model_probability - (1 - model_probability)

        # Apply confidence scaling
        kelly_scaled = kelly_base * confidence

        # Apply fractional Kelly (1/4) for safety
        kelly_fraction = kelly_scaled * 0.25

        # Clamp to reasonable range
        return max(0.0, min(0.10, kelly_fraction))  # Max 10% of bankroll

    @staticmethod
    def _generate_rationale(
        value: float,
        confidence: float,
        signal: BettingSignal,
        model_probability: float,
        implied_probability: float,
    ) -> str:
        """Generate explanation for the signal."""
        if signal == BettingSignal.SKIP:
            if confidence < OddsComparison.MINIMUM_CONFIDENCE:
                return f"Confidence too low ({confidence:.0%}), need >{OddsComparison.MINIMUM_CONFIDENCE:.0%}"
            return "No significant edge between model and market"

        edge_pct = value * 100
        direction = "overvalued" if value < 0 else "undervalued"

        return (
            f"Market {direction} by {abs(edge_pct):.1f}%. "
            f"Model: {model_probability:.1%}, Market: {implied_probability:.1%}, "
            f"Confidence: {confidence:.0%}"
        )


# ============================================================================
# ARBITRAGE DETECTOR
# ============================================================================


class ArbitrageDetector:
    """Find arbitrage opportunities across related markets."""

    @staticmethod
    def detect_three_way_arbitrage(
        home_contract: KalshiContract,
        draw_contract: KalshiContract,
        away_contract: KalshiContract,
    ) -> Optional[ArbitrageOpportunity]:
        """Detect arbitrage in 1X2 (three-way) markets.

        Args:
            home_contract: Contract for home win
            draw_contract: Contract for draw
            away_contract: Contract for away win

        Returns:
            ArbitrageOpportunity if arbitrage exists, None otherwise
        """
        # Get implied probabilities
        p_home = home_contract.implied_probability_yes()
        p_draw = draw_contract.implied_probability_yes()
        p_away = away_contract.implied_probability_yes()

        # Calculate total implied probability (overround)
        total_implied = p_home + p_draw + p_away

        if total_implied > 1.0:
            # Arbitrage exists - sum of probabilities > 100%
            profit_potential = 1.0 / total_implied - 1.0

            # Find which market is most overpriced
            # We want to bet on each outcome proportionally to eliminate risk
            stake_allocation = {
                home_contract.contract_id: p_home / total_implied,
                draw_contract.contract_id: p_draw / total_implied,
                away_contract.contract_id: p_away / total_implied,
            }

            return ArbitrageOpportunity(
                market_ids=[
                    home_contract.contract_id,
                    draw_contract.contract_id,
                    away_contract.contract_id,
                ],
                contracts={
                    "home": home_contract,
                    "draw": draw_contract,
                    "away": away_contract,
                },
                implied_overround=total_implied,
                profit_potential=profit_potential * 100,  # Convert to percentage
                stake_allocation=stake_allocation,
                exposure=0.0,  # No exposure with perfect arbitrage
                is_profitable=profit_potential > 0.005,  # At least 0.5% profit
            )

        return None

    @staticmethod
    def detect_goal_market_arbitrage(
        over_1_5: KalshiContract,
        over_2_5: KalshiContract,
        over_3_5: KalshiContract,
    ) -> List[ArbitrageOpportunity]:
        """Detect arbitrage in sequential goal markets.

        Args:
            over_1_5: Over 1.5 goals contract
            over_2_5: Over 2.5 goals contract
            over_3_5: Over 3.5 goals contract

        Returns:
            List of detected arbitrage opportunities
        """
        opportunities = []

        # Check: Over 2.5 should be cheaper than Over 1.5
        # If not, there's arbitrage
        p_over_1_5 = over_1_5.implied_probability_yes()
        p_over_2_5 = over_2_5.implied_probability_yes()

        if p_over_2_5 >= p_over_1_5:
            # Arbitrage: buy under 1.5, sell over 2.5
            opportunities.append(
                ArbitrageOpportunity(
                    market_ids=[over_1_5.contract_id, over_2_5.contract_id],
                    contracts={"over_1_5": over_1_5, "over_2_5": over_2_5},
                    implied_overround=(p_over_1_5 + (1 - p_over_2_5)),
                    profit_potential=abs(p_over_1_5 - p_over_2_5) * 100,
                    stake_allocation={
                        over_1_5.contract_id: 0.5,
                        over_2_5.contract_id: 0.5,
                    },
                    exposure=0.0,
                    is_profitable=(p_over_1_5 - p_over_2_5) > 0.01,
                )
            )

        return opportunities


# ============================================================================
# GOAL MARKET OPTIMIZER
# ============================================================================


class GoalMarketOptimizer:
    """Connect xG predictions to goal range markets."""

    @staticmethod
    def recommend_goal_markets(
        match_id: str,
        home_team: str,
        away_team: str,
        home_xg: float,
        away_xg: float,
        model_confidence: float = 0.75,
    ) -> GoalMarketRecommendation:
        """Generate recommendations for goal range markets using xG.

        Args:
            match_id: Match identifier
            home_team: Home team name
            away_team: Away team name
            home_xg: Home team expected goals
            away_xg: Away team expected goals
            model_confidence: Our confidence in xG prediction

        Returns:
            GoalMarketRecommendation with market suggestions
        """
        # Use Poisson to estimate goal probabilities
        # P(X > k) = 1 - P(X <= k) where X ~ Poisson(λ)

        # Simplified Poisson calculation for common thresholds
        total_xg = home_xg + away_xg

        # Estimate probabilities
        over_1_5_prob = GoalMarketOptimizer._poisson_over(total_xg, 1.5)
        over_2_5_prob = GoalMarketOptimizer._poisson_over(total_xg, 2.5)
        over_3_5_prob = GoalMarketOptimizer._poisson_over(total_xg, 3.5)

        # BTTS probability (both teams score)
        p_home_scores = GoalMarketOptimizer._poisson_over(home_xg, 0.5)
        p_away_scores = GoalMarketOptimizer._poisson_over(away_xg, 0.5)
        btts_prob = p_home_scores * p_away_scores

        # Generate recommendations
        recommended_markets = {}

        if over_1_5_prob > 0.60 and model_confidence > 0.65:
            recommended_markets["over_1_5"] = BettingSignal.BUY
        if over_2_5_prob > 0.50 and model_confidence > 0.70:
            recommended_markets["over_2_5"] = BettingSignal.BUY
        if over_3_5_prob > 0.35 and model_confidence > 0.75:
            recommended_markets["over_3_5"] = BettingSignal.BUY
        if btts_prob > 0.45 and model_confidence > 0.70:
            recommended_markets["btts"] = BettingSignal.BUY

        # Under recommendations
        if over_1_5_prob < 0.40:
            recommended_markets["under_1_5"] = BettingSignal.BUY
        if over_2_5_prob < 0.45:
            recommended_markets["under_2_5"] = BettingSignal.BUY

        analysis = (
            f"xG prediction: {total_xg:.2f} total ({home_xg:.2f} home, {away_xg:.2f} away). "
            f"Over 1.5: {over_1_5_prob:.1%}, Over 2.5: {over_2_5_prob:.1%}, "
            f"BTTS: {btts_prob:.1%}"
        )

        return GoalMarketRecommendation(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            home_xg=home_xg,
            away_xg=away_xg,
            over_1_5_prob=over_1_5_prob,
            over_2_5_prob=over_2_5_prob,
            over_3_5_prob=over_3_5_prob,
            btts_probability=btts_prob,
            recommended_markets=recommended_markets,
            confidence=model_confidence,
            analysis=analysis,
        )

    @staticmethod
    def _poisson_over(lambda_param: float, threshold: float) -> float:
        """Simplified Poisson P(X > threshold) calculation."""
        import math

        if lambda_param <= 0:
            return 0.0 if threshold >= 0 else 1.0

        # Simplified for common thresholds
        exp_neg_lambda = math.exp(-lambda_param)
        cumulative = 0.0

        for k in range(int(threshold) + 1):
            prob_k = (lambda_param ** k) * exp_neg_lambda / math.factorial(k)
            cumulative += prob_k

        return 1.0 - cumulative


# ============================================================================
# PLAYER PROPS MAPPER
# ============================================================================


class PlayerPropsMapper:
    """Map player analysis to goal scorer and other player prop markets."""

    @staticmethod
    def map_goal_scorer(
        player_id: str,
        player_name: str,
        team: str,
        opponent: str,
        match_id: str,
        model_xg: float,
        market_implied_probability: float,
        confidence: float,
    ) -> PlayerPropRecommendation:
        """Map player analysis to goal scorer market recommendation.

        Args:
            player_id: Player identifier
            player_name: Player name
            team: Player's team
            opponent: Opposing team
            match_id: Match identifier
            model_xg: Model's expected goals for player
            market_implied_probability: Market's implied probability
            confidence: Our confidence in the prediction

        Returns:
            PlayerPropRecommendation
        """
        # Convert xG to probability (simplified)
        model_probability = min(0.99, model_xg * 0.3 + 0.05)  # Heuristic conversion

        # Calculate signal
        value = model_probability - market_implied_probability
        signal = BettingSignal.SKIP

        if confidence > 0.65:
            if value > 0.05:
                signal = BettingSignal.BUY
            elif value > 0.02:
                signal = BettingSignal.WEAK_BUY

        rationale = (
            f"xG: {model_xg:.2f} → Probability: {model_probability:.1%} "
            f"vs Market: {market_implied_probability:.1%}. "
            f"Edge: {value * 100:+.1f}%. Confidence: {confidence:.0%}"
        )

        return PlayerPropRecommendation(
            player_id=player_id,
            player_name=player_name,
            team=team,
            opponent=opponent,
            match_id=match_id,
            model_probability=model_probability,
            market_implied_probability=market_implied_probability,
            model_xg=model_xg,
            expected_xg=model_xg,
            confidence=confidence,
            signal=signal,
            rationale=rationale,
        )


# ============================================================================
# BETTING STRATEGIES
# ============================================================================


class BettingStrategies:
    """Multi-market strategy implementations."""

    @staticmethod
    def undervalued_xg_strategy(
        matches: List[Dict[str, Any]],
        market_client: KalshiMarketClient,
        min_edge: float = 0.05,
    ) -> List[PredictionComparison]:
        """Strategy: Only bet when model xG > market implied goals.

        Args:
            matches: List of match data with xG
            market_client: Kalshi market client
            min_edge: Minimum edge required

        Returns:
            List of recommendations
        """
        recommendations = []

        for match in matches:
            home_xg = match.get("home_xg", 0.0)
            away_xg = match.get("away_xg", 0.0)
            total_xg = home_xg + away_xg

            # Find over/under markets
            # Filter for valuable opportunities
            if total_xg > 2.7:  # High-scoring match likely
                # Look for undervalued "over 2.5" bets
                pass  # Would integrate with market data

        return recommendations

    @staticmethod
    def btts_grinder_strategy(
        matches: List[Dict[str, Any]],
        btts_threshold: float = 0.45,
    ) -> List[Dict[str, Any]]:
        """Strategy: Find consistent BTTS opportunities.

        Args:
            matches: List of match data
            btts_threshold: Minimum BTTS probability

        Returns:
            List of match recommendations
        """
        recommendations = []

        for match in matches:
            home_xg = match.get("home_xg", 0.0)
            away_xg = match.get("away_xg", 0.0)

            # Simplified BTTS: both teams likely to score if both have decent xG
            if home_xg > 0.8 and away_xg > 0.8:
                btts_prob = 0.5  # Simplified

                if btts_prob > btts_threshold:
                    recommendations.append(
                        {
                            "match_id": match.get("id"),
                            "strategy": "btts_grinder",
                            "btts_probability": btts_prob,
                            "confidence": 0.65,
                        }
                    )

        return recommendations

    @staticmethod
    def parlay_strategy(
        recommendations: List[PredictionComparison],
        max_legs: int = 3,
        min_confidence: float = 0.75,
    ) -> List[List[PredictionComparison]]:
        """Strategy: Combine high-confidence predictions into parlays.

        Args:
            recommendations: List of individual recommendations
            max_legs: Maximum number of legs in parlay
            min_confidence: Minimum confidence for inclusion

        Returns:
            List of parlay combinations
        """
        # Filter to high-confidence recommendations
        high_confidence = [
            r for r in recommendations
            if r.confidence >= min_confidence and r.signal in (
                BettingSignal.BUY,
                BettingSignal.STRONG_BUY,
            )
        ]

        parlays = []

        # Combine into 2-3 leg parlays
        for i, rec1 in enumerate(high_confidence):
            for rec2 in high_confidence[i + 1:]:
                if len(parlays) < 5:  # Limit to 5 parlays
                    parlays.append([rec1, rec2])

        return parlays

    @staticmethod
    def hedging_strategy(
        current_position: Dict[str, Any],
        new_information: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Strategy: Hedge exposed positions with new information.

        Args:
            current_position: Current position details
            new_information: New market or team information

        Returns:
            List of hedge trade recommendations
        """
        hedges = []

        # Example: If key player injured, hedge by reducing exposure
        if new_information.get("key_injury"):
            loss_estimate = current_position.get("exposure", 0.0) * 0.15

            hedges.append(
                {
                    "action": "reduce_position",
                    "reduction_percent": 0.5,
                    "reason": "Key player injury detected",
                    "estimated_risk_reduction": loss_estimate,
                }
            )

        return hedges

    @staticmethod
    def arbitrage_strategy(
        arbitrage_opportunities: List[ArbitrageOpportunity],
        min_profit_percent: float = 0.5,
    ) -> List[ArbitrageOpportunity]:
        """Strategy: Execute risk-free arbitrage opportunities.

        Args:
            arbitrage_opportunities: Available arbitrage opportunities
            min_profit_percent: Minimum profit percentage to execute

        Returns:
            Filtered list of executable arbitrage opportunities
        """
        return [
            opp for opp in arbitrage_opportunities
            if opp.is_profitable and opp.profit_potential >= min_profit_percent
        ]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test odds comparison
    print("Testing OddsComparison...")
    # Would need actual contract object
