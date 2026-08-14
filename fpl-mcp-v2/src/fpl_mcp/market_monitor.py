"""Real-time Market Monitoring and Live Portfolio Tracking.

This module provides:
- MarketFeedSubscriber: Real-time WebSocket connection to Kalshi
- LivePortfolioTracker: Real-time PnL calculation and Greeks
- InFlightScoreHandler: Handle live match score updates
- MarketEfficiencyTracker: Monitor pricing inefficiencies

Author: SONNET-3 (Kalshi Market Integration Engineer)
Date: 2026-08-14
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from fpl_mcp.kalshi_client import (
    KalshiMarketClient,
    KalshiContract,
    Order,
    Portfolio,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time."""
    timestamp: datetime
    total_value: float
    cash_balance: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    realized_pnl: float
    total_return_percent: float
    num_open_positions: int
    largest_position: str
    largest_position_percent: float
    delta: float  # Net directional exposure
    gamma: float  # Convexity risk


@dataclass
class LivePriceUpdate:
    """Live price update from market feed."""
    contract_id: str
    timestamp: datetime
    bid_price: float
    ask_price: float
    last_trade_price: float
    volume_1m: float
    volume_1h: float
    bid_volume: float
    ask_volume: float
    open_interest: float


@dataclass
class MatchEvent:
    """Live match event (goal, injury, etc.)."""
    match_id: str
    timestamp: datetime
    event_type: str  # "goal", "card", "injury", "substitution"
    team: str
    player: Optional[str]
    minute: int
    description: str


@dataclass
class PriceMovement:
    """Historical price movement tracking."""
    contract_id: str
    timestamp: datetime
    old_price: float
    new_price: float
    price_change: float
    price_change_percent: float
    movement_reason: Optional[str] = None  # "model_prediction_update", "match_event", etc.


@dataclass
class MarketEfficiency:
    """Market efficiency analysis."""
    contract_id: str
    timestamp: datetime
    model_probability: float
    market_implied_probability: float
    model_market_divergence: float  # Model - Market
    consistency_score: float  # How consistent this mispricing is (0-1)
    occurrence_count: int  # How many times we've seen this mispricing
    total_potential_edge: float  # Cumulative edge if we traded every occurrence


# ============================================================================
# MARKET FEED SUBSCRIBER
# ============================================================================


class MarketFeedSubscriber:
    """Subscribe to real-time market feed updates."""

    def __init__(self, market_client: KalshiMarketClient):
        """Initialize market feed subscriber.

        Args:
            market_client: Kalshi market client
        """
        self.market_client = market_client
        self.price_updates: Dict[str, LivePriceUpdate] = {}
        self.price_history: Dict[str, List[LivePriceUpdate]] = {}
        self.updates_lock = asyncio.Lock()
        self.price_callbacks: List[Callable[[LivePriceUpdate], None]] = []
        self.running = False

    async def start(self) -> None:
        """Start receiving market feed updates."""
        self.running = True
        logger.info("Market feed subscriber started")

        # In production, this would connect to WebSocket
        # For now, we provide a framework for polling
        while self.running:
            await asyncio.sleep(1)
            # Poll for updates (would be replaced by WebSocket)

    async def stop(self) -> None:
        """Stop receiving market feed updates."""
        self.running = False
        logger.info("Market feed subscriber stopped")

    async def subscribe(self, contract_ids: List[str]) -> None:
        """Subscribe to updates for specific contracts.

        Args:
            contract_ids: List of contract IDs
        """
        await self.market_client.subscribe_to_updates(contract_ids)
        logger.info(f"Subscribed to {len(contract_ids)} contracts")

    async def unsubscribe(self, contract_ids: List[str]) -> None:
        """Unsubscribe from contract updates.

        Args:
            contract_ids: List of contract IDs
        """
        await self.market_client.unsubscribe_from_updates(contract_ids)
        logger.info(f"Unsubscribed from {len(contract_ids)} contracts")

    def register_price_callback(
        self, callback: Callable[[LivePriceUpdate], None]
    ) -> None:
        """Register callback for price updates.

        Args:
            callback: Function to call on price update
        """
        self.price_callbacks.append(callback)

    async def on_price_update(self, update: LivePriceUpdate) -> None:
        """Handle incoming price update.

        Args:
            update: Price update from market feed
        """
        async with self.updates_lock:
            self.price_updates[update.contract_id] = update

            # Track history
            if update.contract_id not in self.price_history:
                self.price_history[update.contract_id] = []

            self.price_history[update.contract_id].append(update)

            # Keep only last 1000 updates per contract (memory management)
            if len(self.price_history[update.contract_id]) > 1000:
                self.price_history[update.contract_id] = (
                    self.price_history[update.contract_id][-1000:]
                )

        # Call registered callbacks
        for callback in self.price_callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Price callback error: {e}")

    async def get_latest_price(self, contract_id: str) -> Optional[LivePriceUpdate]:
        """Get latest price for contract.

        Args:
            contract_id: Contract identifier

        Returns:
            Latest LivePriceUpdate or None
        """
        async with self.updates_lock:
            return self.price_updates.get(contract_id)

    async def get_price_history(
        self, contract_id: str, limit: int = 100
    ) -> List[LivePriceUpdate]:
        """Get recent price history for contract.

        Args:
            contract_id: Contract identifier
            limit: Maximum number of updates to return

        Returns:
            List of recent price updates
        """
        async with self.updates_lock:
            history = self.price_history.get(contract_id, [])
            return history[-limit:] if history else []


# ============================================================================
# LIVE PORTFOLIO TRACKER
# ============================================================================


class LivePortfolioTracker:
    """Track real-time portfolio P&L and Greeks."""

    def __init__(self, market_client: KalshiMarketClient):
        """Initialize portfolio tracker.

        Args:
            market_client: Kalshi market client
        """
        self.market_client = market_client
        self.portfolio_history: List[PortfolioSnapshot] = []
        self.initial_bankroll = 10000.0
        self.starting_cash = 10000.0
        self.realized_pnl = 0.0
        self.trades_executed: List[Order] = []

    async def update_portfolio_state(self) -> PortfolioSnapshot:
        """Update portfolio state and calculate current PnL.

        Returns:
            Current PortfolioSnapshot
        """
        portfolio = await self.market_client.get_portfolio()

        # Calculate unrealized PnL
        unrealized_pnl = 0.0
        delta = 0.0
        largest_position = ""
        largest_position_value = 0.0

        for contract_id, quantity in portfolio.positions.items():
            contract = self.market_client.contracts.get(contract_id)
            if not contract or quantity == 0:
                continue

            # Estimate position value
            position_value = quantity * contract.mid_price()
            unrealized_pnl += position_value

            # Track largest position
            if abs(position_value) > largest_position_value:
                largest_position = contract_id
                largest_position_value = abs(position_value)

            # Update delta
            delta += quantity * contract.mid_price()

        total_value = portfolio.cash_balance + portfolio.total_value
        unrealized_pnl_percent = (
            unrealized_pnl / total_value if total_value > 0 else 0.0
        )

        total_return = (total_value - self.starting_cash)
        total_return_percent = total_return / self.starting_cash if self.starting_cash > 0 else 0.0

        largest_position_percent = (
            largest_position_value / total_value if total_value > 0 else 0.0
        )

        snapshot = PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            total_value=total_value,
            cash_balance=portfolio.cash_balance,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            realized_pnl=self.realized_pnl,
            total_return_percent=total_return_percent,
            num_open_positions=len([q for q in portfolio.positions.values() if q > 0]),
            largest_position=largest_position,
            largest_position_percent=largest_position_percent,
            delta=delta,
            gamma=0.0,  # Simplified for now
        )

        self.portfolio_history.append(snapshot)

        # Keep only last 1000 snapshots (memory management)
        if len(self.portfolio_history) > 1000:
            self.portfolio_history = self.portfolio_history[-1000:]

        return snapshot

    async def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Get current portfolio snapshot.

        Returns:
            Current PortfolioSnapshot
        """
        return await self.update_portfolio_state()

    async def get_portfolio_history(
        self, minutes: int = 60
    ) -> List[PortfolioSnapshot]:
        """Get portfolio history for time period.

        Args:
            minutes: Look back period in minutes

        Returns:
            List of portfolio snapshots
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            s for s in self.portfolio_history
            if s.timestamp >= cutoff_time
        ]

    async def calculate_portfolio_Greeks(self) -> Dict[str, float]:
        """Calculate portfolio Greeks (simplified).

        Returns:
            Dict with delta, gamma, theta, vega, rho
        """
        portfolio = await self.market_client.get_portfolio()

        delta = 0.0
        gamma = 0.0
        theta = 0.0

        for contract_id, quantity in portfolio.positions.items():
            contract = self.market_client.contracts.get(contract_id)
            if not contract or quantity == 0:
                continue

            # Delta: directional exposure
            mid_price = contract.mid_price()
            delta += quantity * mid_price

            # Gamma: convexity (simplified as curvature of bid-ask)
            spread = contract.spread()
            gamma += spread * abs(quantity)

            # Theta: time decay (contracts lose value as expiration approaches)
            time_to_expiry = (contract.expires_at - datetime.utcnow()).total_seconds() / 86400
            if time_to_expiry < 1:
                theta -= 0.10 * quantity  # Accelerating decay

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": 0.0,  # Binary options have minimal vega
            "rho": 0.0,  # Interest rate insensitive
        }


# ============================================================================
# IN-FLIGHT SCORE HANDLER
# ============================================================================


class InFlightScoreHandler:
    """Handle live match updates and adjust positions/predictions."""

    def __init__(self, market_client: KalshiMarketClient, portfolio_tracker: LivePortfolioTracker):
        """Initialize score handler.

        Args:
            market_client: Kalshi market client
            portfolio_tracker: Portfolio tracker for P&L monitoring
        """
        self.market_client = market_client
        self.portfolio_tracker = portfolio_tracker
        self.live_matches: Dict[str, Dict[str, Any]] = {}

    async def handle_match_event(self, event: MatchEvent) -> List[Dict[str, Any]]:
        """Handle live match event (goal, injury, etc.).

        Args:
            event: Match event information

        Returns:
            List of recommended actions
        """
        actions = []

        # Update live match state
        if event.match_id not in self.live_matches:
            self.live_matches[event.match_id] = {
                "goals": {},
                "injuries": [],
                "events": [],
            }

        match_state = self.live_matches[event.match_id]

        if event.event_type == "goal":
            # Track goal
            if event.team not in match_state["goals"]:
                match_state["goals"][event.team] = 0
            match_state["goals"][event.team] += 1

            # Evaluate impact on related markets
            actions.extend(await self._evaluate_goal_impact(event))

        elif event.event_type == "injury":
            # Track injury
            match_state["injuries"].append({
                "player": event.player,
                "minute": event.minute,
            })

            # Key player injury might require hedging
            actions.extend(await self._evaluate_injury_impact(event))

        match_state["events"].append(event)

        return actions

    async def _evaluate_goal_impact(self, goal_event: MatchEvent) -> List[Dict[str, Any]]:
        """Evaluate impact of goal on related markets."""
        actions = []

        # Update goal probabilities
        match_state = self.live_matches.get(goal_event.match_id, {})
        current_goals = sum(match_state.get("goals", {}).values())

        # Check BTTS market
        if current_goals >= 2:  # Both teams have scored
            actions.append({
                "action": "review_btts",
                "match_id": goal_event.match_id,
                "reason": "Both teams have scored, BTTS contract should expire ITM",
                "current_goals": current_goals,
            })

        # Check over/under markets
        if current_goals == 2:
            actions.append({
                "action": "close_under_2_5",
                "match_id": goal_event.match_id,
                "reason": "2 goals scored, over 2.5 likely wins",
            })

        return actions

    async def _evaluate_injury_impact(self, injury_event: MatchEvent) -> List[Dict[str, Any]]:
        """Evaluate impact of injury on related markets."""
        actions = []

        # Check if this is a key player
        key_players = ["Haaland", "Kane", "Salah", "De Bruyne"]

        if injury_event.player in key_players:
            actions.append({
                "action": "hedge_goal_scorer",
                "player": injury_event.player,
                "reason": "Key player injured, goal scorer odds should shift",
                "recommended_action": "reduce_position",
            })

        return actions

    def get_live_match_state(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of live match.

        Args:
            match_id: Match identifier

        Returns:
            Match state dict or None
        """
        return self.live_matches.get(match_id)


# ============================================================================
# MARKET EFFICIENCY TRACKER
# ============================================================================


class MarketEfficiencyTracker:
    """Track market pricing efficiency and identify consistent mispricings."""

    def __init__(self):
        """Initialize efficiency tracker."""
        self.efficiency_samples: Dict[str, List[MarketEfficiency]] = {}
        self.mispricing_patterns: Dict[str, Dict[str, Any]] = {}
        self.last_analysis_time = datetime.utcnow()

    async def record_efficiency(
        self,
        contract_id: str,
        model_probability: float,
        market_implied_probability: float,
    ) -> None:
        """Record market efficiency observation.

        Args:
            contract_id: Contract identifier
            model_probability: Our model's probability
            market_implied_probability: Market's implied probability
        """
        if contract_id not in self.efficiency_samples:
            self.efficiency_samples[contract_id] = []

        efficiency = MarketEfficiency(
            contract_id=contract_id,
            timestamp=datetime.utcnow(),
            model_probability=model_probability,
            market_implied_probability=market_implied_probability,
            model_market_divergence=model_probability - market_implied_probability,
            consistency_score=0.0,  # Will be calculated
            occurrence_count=len(self.efficiency_samples[contract_id]) + 1,
            total_potential_edge=0.0,
        )

        self.efficiency_samples[contract_id].append(efficiency)

        # Keep only last 100 samples per contract
        if len(self.efficiency_samples[contract_id]) > 100:
            self.efficiency_samples[contract_id] = (
                self.efficiency_samples[contract_id][-100:]
            )

        # Update consistency score
        await self._update_consistency(contract_id)

    async def _update_consistency(self, contract_id: str) -> None:
        """Calculate consistency of mispricing pattern."""
        samples = self.efficiency_samples.get(contract_id, [])
        if len(samples) < 5:
            return

        # Calculate consistency as standard deviation of divergence
        divergences = [s.model_market_divergence for s in samples[-20:]]
        avg_divergence = sum(divergences) / len(divergences)
        variance = sum((d - avg_divergence) ** 2 for d in divergences) / len(divergences)
        std_dev = variance ** 0.5

        # High consistency = low std dev (consistent mispricing)
        consistency = 1.0 / (1.0 + std_dev)

        # Update pattern
        if consistency > 0.7:  # Consistent pattern detected
            self.mispricing_patterns[contract_id] = {
                "average_divergence": avg_divergence,
                "consistency_score": consistency,
                "sample_size": len(samples),
                "last_updated": datetime.utcnow(),
                "direction": "model_overvalued" if avg_divergence < 0 else "model_undervalued",
            }

    def get_efficiency_analysis(self) -> Dict[str, Any]:
        """Get overall market efficiency analysis.

        Returns:
            Dict with efficiency metrics
        """
        total_samples = sum(len(s) for s in self.efficiency_samples.values())
        num_contracts = len(self.efficiency_samples)
        num_patterns = len(self.mispricing_patterns)

        avg_divergence = 0.0
        if num_contracts > 0:
            for samples in self.efficiency_samples.values():
                if samples:
                    avg_divergence += sum(s.model_market_divergence for s in samples)
            avg_divergence /= total_samples if total_samples > 0 else 1

        return {
            "total_samples": total_samples,
            "num_contracts_tracked": num_contracts,
            "num_consistent_patterns": num_patterns,
            "average_model_market_divergence": avg_divergence,
            "consistent_patterns": self.mispricing_patterns,
            "last_analysis": datetime.utcnow(),
        }

    def get_top_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top market opportunities based on consistency and divergence.

        Args:
            limit: Maximum number of opportunities

        Returns:
            List of top opportunities
        """
        opportunities = []

        for contract_id, pattern in self.mispricing_patterns.items():
            if pattern["consistency_score"] > 0.65:
                opportunities.append({
                    "contract_id": contract_id,
                    "divergence": pattern["average_divergence"],
                    "consistency": pattern["consistency_score"],
                    "direction": pattern["direction"],
                    "samples": pattern["sample_size"],
                })

        # Sort by consistency score
        opportunities.sort(
            key=lambda x: x["consistency"],
            reverse=True
        )

        return opportunities[:limit]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Market monitoring module loaded")
