"""Backtesting Framework for Strategy Validation.

This module provides:
- BacktestEngine: Historical match replay and performance calculation
- StrategyBacktester: Specific strategy backtesting
- PerformanceMetrics: ROI, Sharpe, win rate, max drawdown calculation
- SampleBacktests: Pre-built sample strategies

Author: SONNET-3 (Kalshi Market Integration Engineer)
Date: 2026-08-14
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class BacktestTrade:
    """Single trade executed during backtest."""
    trade_id: str
    contract_id: str
    market_type: str
    entry_time: datetime
    entry_price: float
    entry_quantity: int
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    exit_quantity: int = 0
    profit_loss: float = 0.0
    profit_loss_percent: float = 0.0
    duration_minutes: int = 0


@dataclass
class DailyPerformance:
    """Daily performance metrics."""
    date: datetime
    starting_value: float
    ending_value: float
    daily_return: float
    daily_return_percent: float
    daily_pnl: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_bankroll: float
    final_value: float
    total_return: float
    total_return_percent: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    win_rate: float  # % of winning trades
    profit_factor: float  # Gross profit / Gross loss
    trades_executed: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    average_trade_duration: float  # in minutes
    best_day: DailyPerformance
    worst_day: DailyPerformance
    daily_performance: List[DailyPerformance] = field(default_factory=list)

    @property
    def expectancy(self) -> float:
        """Calculate trade expectancy (avg profit per trade)."""
        if self.trades_executed == 0:
            return 0.0
        return self.total_return / self.trades_executed

    @property
    def return_to_max_drawdown(self) -> float:
        """Calculate return to max drawdown ratio."""
        if self.max_drawdown_percent == 0:
            return 0.0
        return self.total_return_percent / self.max_drawdown_percent


@dataclass
class EdgeAnalysis:
    """Analysis of edge by market type."""
    market_type: str
    num_trades: int
    win_rate: float
    average_edge: float  # Model probability - Market probability
    edge_capture_rate: float  # % of theoretical edge achieved
    profit_factor: float


# ============================================================================
# BACKTEST ENGINE
# ============================================================================


class BacktestEngine:
    """Engine for backtesting strategies on historical data."""

    def __init__(self, initial_bankroll: float = 10000.0):
        """Initialize backtest engine.

        Args:
            initial_bankroll: Starting capital
        """
        self.initial_bankroll = initial_bankroll
        self.current_value = initial_bankroll
        self.trades: List[BacktestTrade] = []
        self.daily_values: Dict[datetime, float] = {}
        self.positions: Dict[str, int] = {}  # contract_id -> quantity

    def reset(self) -> None:
        """Reset engine for new backtest."""
        self.current_value = self.initial_bankroll
        self.trades = []
        self.daily_values = {}
        self.positions = {}

    async def backtest_strategy(
        self,
        strategy_name: str,
        historical_matches: List[Dict[str, Any]],
        strategy_func: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
        start_date: datetime,
        end_date: datetime,
    ) -> PerformanceMetrics:
        """Run backtest for strategy on historical matches.

        Args:
            strategy_name: Name of strategy
            historical_matches: List of historical match data
            strategy_func: Function that takes match and returns trade or None
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            PerformanceMetrics with results
        """
        self.reset()

        daily_performance: Dict[datetime, DailyPerformance] = {}
        trade_id_counter = 0

        # Filter matches within date range
        filtered_matches = [
            m for m in historical_matches
            if start_date <= m.get("date", datetime.utcnow()) <= end_date
        ]

        # Execute strategy on each match
        for match in filtered_matches:
            match_date = match.get("date", datetime.utcnow()).replace(hour=0, minute=0, second=0)

            # Call strategy function
            trade = strategy_func(match)

            if trade:
                # Execute trade
                entry_value = (
                    trade["quantity"] * trade["entry_price"] * 100
                )  # Convert to cents

                # Check if we have enough capital
                if entry_value <= self.current_value:
                    contract_id = trade["contract_id"]
                    trade_id = f"trade_{trade_id_counter}"
                    trade_id_counter += 1

                    backtest_trade = BacktestTrade(
                        trade_id=trade_id,
                        contract_id=contract_id,
                        market_type=trade.get("market_type", "unknown"),
                        entry_time=match_date,
                        entry_price=trade["entry_price"],
                        entry_quantity=trade["quantity"],
                        exit_time=None,
                        exit_price=None,
                    )

                    # Calculate P&L based on actual outcome
                    actual_result = match.get("result", {})
                    won = trade.get("prediction") == actual_result.get("outcome")

                    if won:
                        # Win: payout is quantity * (1 - entry_price)
                        payout = (
                            trade["quantity"] * (1.0 - trade["entry_price"]) * 100
                        )
                        backtest_trade.profit_loss = payout
                    else:
                        # Loss: lose entire stake
                        backtest_trade.profit_loss = -entry_value

                    backtest_trade.profit_loss_percent = (
                        backtest_trade.profit_loss / entry_value
                        if entry_value > 0
                        else 0.0
                    )
                    backtest_trade.exit_price = 1.0 if won else 0.0
                    backtest_trade.exit_time = match_date
                    backtest_trade.exit_quantity = trade["quantity"]

                    # Update portfolio
                    self.current_value += backtest_trade.profit_loss
                    self.trades.append(backtest_trade)

                    # Track daily value
                    if match_date not in self.daily_values:
                        self.daily_values[match_date] = (
                            self.daily_values.get(
                                match_date - timedelta(days=1),
                                self.initial_bankroll,
                            )
                        )
                    self.daily_values[match_date] = self.current_value

        # Calculate metrics
        metrics = self._calculate_metrics(
            strategy_name, start_date, end_date, daily_performance
        )

        return metrics

    def _calculate_metrics(
        self,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime,
        daily_performance: Dict[datetime, DailyPerformance],
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics.

        Args:
            strategy_name: Strategy name
            start_date: Start date
            end_date: End date
            daily_performance: Daily performance dict

        Returns:
            PerformanceMetrics
        """
        total_return = self.current_value - self.initial_bankroll
        total_return_percent = (
            total_return / self.initial_bankroll
            if self.initial_bankroll > 0
            else 0.0
        )

        # Calculate annual return
        days = (end_date - start_date).days
        annualized_return = (
            (1 + total_return_percent) ** (365 / max(days, 1)) - 1
        )

        # Win rate
        winning_trades = sum(1 for t in self.trades if t.profit_loss > 0)
        losing_trades = len(self.trades) - winning_trades
        win_rate = (
            winning_trades / len(self.trades)
            if self.trades else 0.0
        )

        # Profit factor
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(
            sum(t.profit_loss for t in self.trades if t.profit_loss < 0)
        )
        profit_factor = (
            gross_profit / gross_loss if gross_loss > 0 else 0.0
        )

        # Largest win/loss
        all_pnl = [t.profit_loss for t in self.trades]
        largest_win = max(all_pnl) if all_pnl else 0.0
        largest_loss = min(all_pnl) if all_pnl else 0.0

        # Average trade values
        avg_win = (
            gross_profit / winning_trades if winning_trades > 0 else 0.0
        )
        avg_loss = (
            gross_loss / losing_trades if losing_trades > 0 else 0.0
        )

        # Sharpe ratio (simplified)
        returns = [
            (v - self.initial_bankroll) / self.initial_bankroll
            for v in self.daily_values.values()
        ]
        sharpe = self._calculate_sharpe(returns) if returns else 0.0

        # Sortino ratio (only downside deviation)
        sortino = self._calculate_sortino(returns) if returns else 0.0

        # Max drawdown
        max_dd, max_dd_pct = self._calculate_max_drawdown()

        # Average trade duration
        avg_duration = (
            sum(t.duration_minutes for t in self.trades) / len(self.trades)
            if self.trades else 0.0
        )

        # Best and worst days
        daily_perfs = list(daily_performance.values()) if daily_performance else []
        best_day = (
            max(daily_perfs, key=lambda x: x.daily_return)
            if daily_perfs
            else None
        )
        worst_day = (
            min(daily_perfs, key=lambda x: x.daily_return)
            if daily_perfs
            else None
        )

        return PerformanceMetrics(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_bankroll=self.initial_bankroll,
            final_value=self.current_value,
            total_return=total_return,
            total_return_percent=total_return_percent,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_percent=max_dd_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trades_executed=len(self.trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            average_trade_duration=avg_duration,
            best_day=best_day,
            worst_day=worst_day,
            daily_performance=daily_perfs,
        )

    def _calculate_sharpe(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio.

        Args:
            returns: Daily returns
            risk_free_rate: Risk-free rate (annualized)

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return 0.0

        # Annualize
        sharpe = (mean_return * 252 - risk_free_rate) / (std_dev * math.sqrt(252))
        return sharpe

    def _calculate_sortino(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (only downside deviation).

        Args:
            returns: Daily returns
            risk_free_rate: Risk-free rate (annualized)

        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)

        # Only count downside (negative) returns
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            downside_variance = 0.0
        else:
            downside_variance = (
                sum((r - 0) ** 2 for r in downside_returns) / len(returns)
            )

        downside_std = math.sqrt(downside_variance)

        if downside_std == 0:
            return 0.0

        sortino = (mean_return * 252 - risk_free_rate) / (downside_std * math.sqrt(252))
        return sortino

    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown.

        Returns:
            Tuple of (max_drawdown_amount, max_drawdown_percent)
        """
        if not self.daily_values:
            return 0.0, 0.0

        values = sorted(self.daily_values.items())
        peak = values[0][1]
        max_dd = 0.0
        max_dd_pct = 0.0

        for _, value in values:
            dd = peak - value
            dd_pct = dd / peak if peak > 0 else 0.0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

            if value > peak:
                peak = value

        return max_dd, max_dd_pct


# ============================================================================
# SAMPLE BACKTESTS
# ============================================================================


class SampleBacktests:
    """Pre-built sample strategies for backtesting."""

    @staticmethod
    def undervalued_xg_strategy(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy: Only bet when model xG > market implied.

        Args:
            match: Match data

        Returns:
            Trade dict or None
        """
        home_xg = match.get("home_xg", 0.0)
        away_xg = match.get("away_xg", 0.0)
        market_over_2_5 = match.get("market_over_2_5_implied", 0.5)

        # Calculate predicted over 2.5 probability
        total_xg = home_xg + away_xg
        predicted_prob = min(0.95, total_xg * 0.25)  # Heuristic

        if predicted_prob > market_over_2_5 + 0.10:  # 10% edge
            return {
                "contract_id": f"over_2_5_{match.get('id')}",
                "market_type": "goals_over_under",
                "entry_price": 1.0 - market_over_2_5,
                "quantity": 1,
                "prediction": "over_2_5",
            }
        return None

    @staticmethod
    def btts_grinder_strategy(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy: Find consistent BTTS opportunities.

        Args:
            match: Match data

        Returns:
            Trade dict or None
        """
        home_xg = match.get("home_xg", 0.0)
        away_xg = match.get("away_xg", 0.0)
        market_btts_yes = match.get("market_btts_yes_implied", 0.5)

        # Both teams likely to score if both have decent xG
        if home_xg > 0.8 and away_xg > 0.8:
            predicted_btts = 0.50  # Simplified

            if predicted_btts > market_btts_yes + 0.05:
                return {
                    "contract_id": f"btts_{match.get('id')}",
                    "market_type": "btts",
                    "entry_price": 1.0 - market_btts_yes,
                    "quantity": 1,
                    "prediction": "btts_yes",
                }
        return None

    @staticmethod
    def match_outcome_strategy(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy: Predict match outcomes based on Elo.

        Args:
            match: Match data with Elo ratings

        Returns:
            Trade dict or None
        """
        home_elo = match.get("home_elo", 1600)
        away_elo = match.get("away_elo", 1600)
        market_home_win = match.get("market_home_win_implied", 0.5)

        # Simplified Elo calculation
        elo_diff = home_elo - away_elo
        home_win_prob = 1.0 / (1.0 + 10 ** (-elo_diff / 400))

        if home_win_prob > market_home_win + 0.08:
            return {
                "contract_id": f"home_win_{match.get('id')}",
                "market_type": "match_winner",
                "entry_price": 1.0 - market_home_win,
                "quantity": 1,
                "prediction": "home_win",
            }
        return None

    @staticmethod
    def parlay_strategy(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy: Combine 2 high-confidence predictions.

        Args:
            match: Match data

        Returns:
            Trade dict or None
        """
        home_xg = match.get("home_xg", 0.0)
        away_xg = match.get("away_xg", 0.0)
        home_elo = match.get("home_elo", 1600)

        # Parlay: Home win + Over 2.5 goals
        if home_xg > 1.5 and (home_xg + away_xg) > 2.7:
            return {
                "contract_id": f"parlay_{match.get('id')}",
                "market_type": "parlay",
                "entry_price": 0.25,  # Simplified combined odds
                "quantity": 1,
                "prediction": "home_win_and_over_2_5",
            }
        return None

    @staticmethod
    def hedged_strategy(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy: Build position and hedge dynamically.

        Args:
            match: Match data

        Returns:
            Trade dict or None
        """
        # Initial position on match outcome
        home_elo = match.get("home_elo", 1600)
        away_elo = match.get("away_elo", 1600)

        elo_diff = home_elo - away_elo
        home_win_prob = 1.0 / (1.0 + 10 ** (-elo_diff / 400))

        if home_win_prob > 0.60:
            return {
                "contract_id": f"hedge_{match.get('id')}",
                "market_type": "match_winner",
                "entry_price": 1.0 - home_win_prob,
                "quantity": 1,
                "prediction": "home_win",
            }
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Backtest engine module loaded")
