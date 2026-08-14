"""Order Sizing and Kelly Criterion Implementation.

This module provides:
- Kelly Calculator: Optimal bet sizing using Kelly criterion
- PositionManager: Size orders based on probability and odds
- Portfolio Exposure Tracker: Monitor total market exposure
- Stop Loss Monitor: Risk management and alerts

Author: SONNET-3 (Kalshi Market Integration Engineer)
Date: 2026-08-14
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class PositionType(str, Enum):
    """Type of position."""
    LONG = "long"
    SHORT = "short"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Kelly Criterion constants
FULL_KELLY_MAX = 0.25  # Maximum 25% of bankroll on full Kelly
FRACTIONAL_KELLY = 0.25  # Use 1/4 Kelly for safety (recommended)
MINIMUM_KELLY = 0.001  # Minimum position size
MAXIMUM_KELLY = 0.10  # Maximum position size (10% of bankroll)

# Position limits
MAX_SINGLE_POSITION_PERCENT = 0.05  # Max 5% of bankroll on single contract
MAX_MARKET_CATEGORY_PERCENT = 0.20  # Max 20% on single market type
MAX_TEAM_EXPOSURE_PERCENT = 0.15  # Max 15% on single team

# Stop loss
STOP_LOSS_THRESHOLD = 0.05  # Review position if down 5%
AUTO_STOP_LOSS_THRESHOLD = 0.07  # Auto-close if down 7%


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class KellySizing:
    """Kelly criterion calculation result."""
    kelly_percentage: float  # Full Kelly percentage (0.01 = 1%)
    fractional_kelly_percentage: float  # Fractional Kelly (default 1/4)
    recommended_stake: float  # Recommended stake amount
    max_stake: float  # Maximum safe stake
    min_stake: float  # Minimum recommended stake
    kelly_multiplier: float  # Multiplier for Kelly calculation
    expected_value: float  # Expected value of the bet
    edge: float  # Probability edge


@dataclass
class PositionSizing:
    """Position sizing recommendation."""
    contract_id: str
    probability: float
    odds: float
    kelly_sizing: Optional[KellySizing]
    recommended_quantity: int
    max_quantity: int
    min_quantity: int = 1
    position_limit_exceeded: bool = False
    liquidity_limit_exceeded: bool = False
    rationale: str = ""


@dataclass
class Position:
    """Tracked position in a contract."""
    contract_id: str
    market_category: str
    team: Optional[str]
    quantity: int
    entry_price: float
    entry_value: float
    current_price: float
    current_value: float
    entry_time: datetime
    position_type: PositionType = PositionType.LONG


@dataclass
class ExposureMetrics:
    """Portfolio exposure analysis."""
    total_exposure: float  # Total capital at risk
    exposure_percent: float  # As % of bankroll
    market_exposure: Dict[str, float]  # Exposure per market category
    team_exposure: Dict[str, float]  # Exposure per team
    concentration_risk: float  # Herfindahl index (0-1)
    largest_position_percent: float
    num_active_positions: int
    risk_level: RiskLevel
    is_over_limit: bool


@dataclass
class PortfolioGreeks:
    """Portfolio Greeks for risk assessment."""
    delta: float  # Net directional exposure
    gamma: float  # Convexity/acceleration risk
    theta: float  # Time decay
    vega: float  # Volatility exposure
    rho: float  # Interest rate sensitivity


# ============================================================================
# KELLY CALCULATOR
# ============================================================================


class KellyCalculator:
    """Calculate optimal bet sizes using Kelly criterion."""

    @staticmethod
    def calculate(
        probability_win: float,
        odds: float,
        bankroll: float = 1000.0,
        kelly_fraction: float = FRACTIONAL_KELLY,
    ) -> KellySizing:
        """Calculate optimal bet size using Kelly criterion.

        The Kelly criterion formula: f = (bp - q) / b
        where:
            f = fraction of bankroll to bet
            b = odds - 1 (decimal odds minus 1)
            p = probability of win
            q = probability of loss (1 - p)

        Args:
            probability_win: Predicted win probability (0-1)
            odds: Decimal odds (e.g., 2.1 for -110 American)
            bankroll: Total bankroll amount
            kelly_fraction: Fraction of Kelly to use (0.25 = 1/4 Kelly, safer)

        Returns:
            KellySizing with recommendations

        Raises:
            ValueError: If inputs are invalid
        """
        if not 0.0 < probability_win < 1.0:
            raise ValueError(f"Probability must be between 0 and 1, got {probability_win}")

        if odds < 1.0:
            raise ValueError(f"Odds must be >= 1.0, got {odds}")

        if bankroll <= 0:
            raise ValueError(f"Bankroll must be positive, got {bankroll}")

        if not 0.0 < kelly_fraction <= 1.0:
            raise ValueError(f"Kelly fraction must be 0-1, got {kelly_fraction}")

        # Kelly formula: f = (p * b - q) / b
        # where b = odds - 1
        p = probability_win
        q = 1.0 - probability_win
        b = odds - 1.0

        if b <= 0:
            raise ValueError(f"Invalid odds for Kelly calculation: {odds}")

        # Full Kelly percentage
        kelly_percentage = (p * b - q) / b if b > 0 else 0.0

        # Cap Kelly to reasonable limits
        kelly_percentage = max(-0.25, min(FULL_KELLY_MAX, kelly_percentage))

        # Apply fractional Kelly (1/4 Kelly for safety is recommended)
        fractional_kelly = kelly_percentage * kelly_fraction

        # Calculate stakes
        full_kelly_stake = max(MINIMUM_KELLY, kelly_percentage * bankroll)
        fractional_kelly_stake = max(MINIMUM_KELLY, fractional_kelly * bankroll)
        max_stake = min(MAXIMUM_KELLY * bankroll, fractional_kelly_stake * 1.5)
        min_stake = MINIMUM_KELLY * bankroll

        # Expected value
        expected_value = probability_win * odds + q * 0.0 - 1.0

        # Edge (probability advantage)
        implied_probability = 1.0 / odds
        edge = probability_win - implied_probability

        return KellySizing(
            kelly_percentage=kelly_percentage,
            fractional_kelly_percentage=fractional_kelly,
            recommended_stake=fractional_kelly_stake,
            max_stake=max_stake,
            min_stake=min_stake,
            kelly_multiplier=kelly_fraction,
            expected_value=expected_value,
            edge=edge,
        )

    @staticmethod
    def calculate_multiple_outcomes(
        probabilities: Dict[str, float],
        odds: Dict[str, float],
        bankroll: float,
        kelly_fraction: float = FRACTIONAL_KELLY,
    ) -> Dict[str, KellySizing]:
        """Calculate Kelly sizing for multiple outcomes (e.g., 1X2 betting).

        Args:
            probabilities: Dict of outcome -> probability
            odds: Dict of outcome -> decimal odds
            bankroll: Total bankroll
            kelly_fraction: Fraction of Kelly to use

        Returns:
            Dict of outcome -> KellySizing
        """
        result = {}
        for outcome in probabilities:
            prob = probabilities[outcome]
            odd = odds.get(outcome, 1.0)

            try:
                sizing = KellyCalculator.calculate(prob, odd, bankroll, kelly_fraction)
                result[outcome] = sizing
            except ValueError as e:
                logger.warning(f"Could not calculate Kelly for {outcome}: {e}")

        return result


# ============================================================================
# POSITION MANAGER
# ============================================================================


class PositionManager:
    """Manage position sizing and portfolio exposure."""

    def __init__(
        self,
        bankroll: float,
        kelly_fraction: float = FRACTIONAL_KELLY,
        max_single_position: float = MAX_SINGLE_POSITION_PERCENT,
    ):
        """Initialize position manager.

        Args:
            bankroll: Total trading bankroll
            kelly_fraction: Fraction of Kelly to use
            max_single_position: Max % of bankroll per position
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.max_single_position = max_single_position
        self.positions: Dict[str, Position] = {}
        self.cash_available = bankroll

    def size_order(
        self,
        contract_id: str,
        probability: float,
        odds: float,
        available_liquidity: float,
        team: Optional[str] = None,
        market_category: Optional[str] = None,
    ) -> PositionSizing:
        """Size an order using Kelly criterion with risk limits.

        Args:
            contract_id: Contract identifier
            probability: Win probability (0-1)
            odds: Decimal odds
            available_liquidity: Available liquidity in contract
            team: Team involved (for exposure tracking)
            market_category: Market category (for exposure tracking)

        Returns:
            PositionSizing with recommended position
        """
        try:
            kelly = KellyCalculator.calculate(
                probability, odds, self.bankroll, self.kelly_fraction
            )
        except ValueError as e:
            logger.error(f"Kelly calculation failed: {e}")
            return PositionSizing(
                contract_id=contract_id,
                probability=probability,
                odds=odds,
                kelly_sizing=None,
                recommended_quantity=0,
                max_quantity=0,
                position_limit_exceeded=True,
                rationale=f"Invalid input: {e}",
            )

        # Calculate position limits
        # 1. Kelly-based limit
        kelly_stake = kelly.recommended_stake
        kelly_quantity = int(kelly_stake / (odds - 1) / 100)  # Convert cents to shares

        # 2. Single position limit (5% of bankroll max)
        max_position_stake = self.bankroll * self.max_single_position
        position_limit_quantity = int(max_position_stake / (odds - 1) / 100)

        # 3. Liquidity limit (5% of available liquidity)
        max_liquidity_stake = available_liquidity * 0.05
        liquidity_quantity = int(max_liquidity_stake / (odds - 1) / 100)

        # 4. Cash available
        cash_quantity = int(self.cash_available / (odds - 1) / 100)

        # Take the minimum of all constraints
        recommended_quantity = min(
            kelly_quantity,
            position_limit_quantity,
            liquidity_quantity,
            cash_quantity,
        )

        # Final checks
        position_limit_exceeded = kelly_quantity > position_limit_quantity
        liquidity_limit_exceeded = kelly_quantity > liquidity_quantity

        rationale = self._generate_rationale(
            kelly, recommended_quantity, position_limit_exceeded, liquidity_limit_exceeded
        )

        return PositionSizing(
            contract_id=contract_id,
            probability=probability,
            odds=odds,
            kelly_sizing=kelly,
            recommended_quantity=max(0, recommended_quantity),
            max_quantity=max(kelly_quantity, position_limit_quantity),
            position_limit_exceeded=position_limit_exceeded,
            liquidity_limit_exceeded=liquidity_limit_exceeded,
            rationale=rationale,
        )

    def hedge_position(
        self,
        contract_id: str,
        current_position_shares: int,
        current_price: float,
        new_probability: float,
    ) -> List[Dict[str, Any]]:
        """Generate hedge recommendations for exposed position.

        Args:
            contract_id: Contract with position
            current_position_shares: Current number of shares held
            current_price: Current contract price
            new_probability: Updated probability estimate

        Returns:
            List of hedge trade recommendations
        """
        hedges: List[Dict[str, Any]] = []

        if contract_id not in self.positions:
            return hedges

        position = self.positions[contract_id]

        # Check if position has turned against us
        unrealized_pnl = current_position_shares * (current_price - position.entry_price)
        unrealized_pnl_percent = unrealized_pnl / position.entry_value if position.entry_value > 0 else 0

        # If position down >5%, consider hedging
        if unrealized_pnl_percent < -0.05:
            hedge_quantity = current_position_shares // 2

            hedges.append(
                {
                    "action": "reduce_position",
                    "hedge_quantity": hedge_quantity,
                    "reduce_percent": 50,
                    "current_pnl_percent": unrealized_pnl_percent * 100,
                    "reason": "Position loss exceeds 5% threshold",
                }
            )

        # Check if probability has changed significantly
        expected_value_change = new_probability - position.entry_price
        if abs(expected_value_change) > 0.15:
            # Probability moved significantly
            if new_probability < position.entry_price and current_position_shares > 0:
                hedges.append(
                    {
                        "action": "reduce_position",
                        "reduce_percent": 25,
                        "reason": f"Probability decreased from {position.entry_price:.1%} to {new_probability:.1%}",
                    }
                )

        return hedges

    def portfolio_exposure(self) -> ExposureMetrics:
        """Calculate current portfolio exposure metrics.

        Returns:
            ExposureMetrics with exposure analysis
        """
        total_exposure = 0.0
        market_exposure: Dict[str, float] = {}
        team_exposure: Dict[str, float] = {}

        for position in self.positions.values():
            exposure = position.current_value
            total_exposure += exposure

            # Market category exposure
            if position.market_category:
                market_exposure[position.market_category] = (
                    market_exposure.get(position.market_category, 0.0) + exposure
                )

            # Team exposure
            if position.team:
                team_exposure[position.team] = (
                    team_exposure.get(position.team, 0.0) + exposure
                )

        exposure_percent = total_exposure / self.bankroll if self.bankroll > 0 else 0.0

        # Calculate concentration risk (Herfindahl index)
        concentration = sum((v / total_exposure) ** 2 for v in market_exposure.values() if total_exposure > 0)

        # Largest position
        largest_position = max(market_exposure.values()) if market_exposure else 0.0
        largest_position_percent = largest_position / total_exposure if total_exposure > 0 else 0.0

        # Determine risk level
        if exposure_percent > 0.30:
            risk_level = RiskLevel.HIGH
        elif exposure_percent > 0.15:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        is_over_limit = exposure_percent > 0.50  # Over 50% of bankroll is too much

        return ExposureMetrics(
            total_exposure=total_exposure,
            exposure_percent=exposure_percent,
            market_exposure=market_exposure,
            team_exposure=team_exposure,
            concentration_risk=concentration,
            largest_position_percent=largest_position_percent,
            num_active_positions=len(self.positions),
            risk_level=risk_level,
            is_over_limit=is_over_limit,
        )

    def _generate_rationale(
        self,
        kelly: KellySizing,
        recommended_quantity: int,
        position_limit_exceeded: bool,
        liquidity_limit_exceeded: bool,
    ) -> str:
        """Generate explanation for sizing decision."""
        rationale = f"Kelly: {kelly.fractional_kelly_percentage:.2%}, "
        rationale += f"Recommended stake: ${kelly.recommended_stake:.2f}, "
        rationale += f"Quantity: {recommended_quantity} shares. "

        if position_limit_exceeded:
            rationale += "Position limit exceeded, reduced. "
        if liquidity_limit_exceeded:
            rationale += "Liquidity constraint applied. "

        if kelly.edge > 0:
            rationale += f"Edge: {kelly.edge:.2%}"
        else:
            rationale += "No positive edge detected"

        return rationale


# ============================================================================
# STOP LOSS MONITOR
# ============================================================================


class StopLossMonitor:
    """Monitor positions for stop loss triggers."""

    def __init__(self, review_threshold: float = STOP_LOSS_THRESHOLD):
        """Initialize stop loss monitor.

        Args:
            review_threshold: Threshold for position review (e.g., 0.05 = 5% loss)
        """
        self.review_threshold = review_threshold
        self.auto_close_threshold = AUTO_STOP_LOSS_THRESHOLD
        self.alerts: List[Dict[str, Any]] = []

    def check_position(
        self,
        contract_id: str,
        entry_price: float,
        current_price: float,
        quantity: int,
    ) -> Optional[Dict[str, Any]]:
        """Check position for stop loss triggers.

        Args:
            contract_id: Contract identifier
            entry_price: Entry price
            current_price: Current market price
            quantity: Quantity held

        Returns:
            Alert dict if threshold exceeded, None otherwise
        """
        if quantity == 0 or entry_price == 0:
            return None

        pnl = quantity * (current_price - entry_price)
        pnl_percent = (current_price - entry_price) / entry_price

        if pnl_percent < -self.review_threshold:
            alert = {
                "contract_id": contract_id,
                "pnl_percent": pnl_percent,
                "pnl": pnl,
                "entry_price": entry_price,
                "current_price": current_price,
                "action": "review" if pnl_percent > -self.auto_close_threshold else "auto_close",
                "timestamp": datetime.utcnow(),
            }

            self.alerts.append(alert)
            return alert

        return None

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts.

        Returns:
            List of alerts
        """
        return self.alerts.copy()

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self.alerts.clear()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test Kelly calculator
    print("Testing Kelly Calculator...")
    kelly = KellyCalculator.calculate(0.65, 2.1, 10000.0)
    print(f"Kelly percentage: {kelly.kelly_percentage:.2%}")
    print(f"Recommended stake: ${kelly.recommended_stake:.2f}")
