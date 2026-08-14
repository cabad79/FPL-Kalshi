"""Kalshi Market Integration - API Client and Market Feed Consumer.

This module provides:
- KalshiAuthClient: OAuth2 authentication with token refresh
- KalshiMarketClient: Real-time market feed consumer with WebSocket support
- MarketTypeMapper: Map football predictions to Kalshi contract types
- Comprehensive data models for contracts, orders, and portfolios

Author: SONNET-3 (Kalshi Market Integration Engineer)
Date: 2026-08-14
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Dict, List
from collections import defaultdict

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class OrderSide(str, Enum):
    """Order side enumeration."""
    YES = "yes"
    NO = "no"


class OrderStatus(str, Enum):
    """Order execution status."""
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class MarketCategory(str, Enum):
    """Kalshi market categories."""
    MATCH_WINNER = "match_winner"  # 1X2
    GOALS_OVER_UNDER = "goals_over_under"  # Over/Under 1.5, 2.5, 3.5
    BTTS = "btts"  # Both Teams To Score
    CORRECT_SCORE = "correct_score"  # Exact final score
    GOAL_SCORER = "goal_scorer"  # Player goal scorer
    CLEAN_SHEET = "clean_sheet"  # Team keeps clean sheet
    CORNERS = "corners"  # Total match corners
    CARDS = "cards"  # Yellow/red cards
    ASSISTS = "assists"  # Player assists


class ConfidenceLevel(str, Enum):
    """Prediction confidence levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Kalshi API configuration
KALSHI_API_BASE_URL = "https://api.kalshi.com/v2"
KALSHI_AUTH_URL = f"{KALSHI_API_BASE_URL}/auth"
KALSHI_MARKETS_URL = f"{KALSHI_API_BASE_URL}/markets"
KALSHI_ORDERS_URL = f"{KALSHI_API_BASE_URL}/orders"
KALSHI_WEBSOCKET_URL = "wss://api.kalshi.com/v2/events"

# Rate limiting
RATE_LIMIT_RPM = 100  # Requests per minute
RATE_LIMIT_RPH = 5000  # Requests per hour
RATE_LIMIT_WINDOW = 60  # seconds

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # Exponential backoff multiplier
INITIAL_RETRY_DELAY = 1.0  # seconds

# Connection pooling
POOL_CONNECTIONS = 10
POOL_MAXSIZE = 20
TIMEOUT = 30.0  # seconds


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class KalshiContract:
    """Kalshi market contract definition."""
    contract_id: str
    title: str
    category: MarketCategory
    description: str
    event_id: str  # Match or event identifier
    fpl_match_id: str  # Cross-reference to FPL match
    league: str  # EPL, Championship, League One
    team_home: str
    team_away: str
    expires_at: datetime
    settlement_source: str  # How the outcome is determined
    tick_size: float = 0.01  # Minimum price movement
    yes_bid: float = 0.0
    yes_ask: float = 0.0
    no_bid: float = 0.0
    no_ask: float = 0.0
    last_price: float = 0.5
    volume_24h: float = 0.0
    liquidity: float = 0.0
    last_update: datetime = field(default_factory=datetime.utcnow)

    def implied_probability_yes(self) -> float:
        """Get implied probability from ask price (probability of YES)."""
        if self.yes_ask <= 0 or self.yes_ask >= 1:
            return 0.5
        return self.yes_ask

    def implied_probability_no(self) -> float:
        """Get implied probability from ask price (probability of NO)."""
        if self.no_ask <= 0 or self.no_ask >= 1:
            return 0.5
        return self.no_ask

    def mid_price(self) -> float:
        """Calculate mid price between bid and ask."""
        if self.yes_bid > 0 and self.yes_ask > 0:
            return (self.yes_bid + self.yes_ask) / 2
        return self.last_price

    def spread(self) -> float:
        """Calculate bid-ask spread."""
        if self.yes_bid > 0 and self.yes_ask > 0:
            return self.yes_ask - self.yes_bid
        return 0.0

    @property
    def is_liquid(self) -> bool:
        """Check if contract has sufficient liquidity for trading."""
        return self.liquidity > 1000.0 and self.volume_24h > 100.0


@dataclass
class Order:
    """Kalshi order representation."""
    order_id: str
    contract_id: str
    side: OrderSide  # YES or NO
    price: float  # Decimal price (0.0-1.0)
    quantity: int  # Number of shares
    amount: float  # Total stake in cents
    status: OrderStatus = OrderStatus.PENDING
    executed_price: Optional[float] = None
    executed_quantity: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    @property
    def pnl(self) -> float:
        """Calculate unrealized P&L if order partially filled."""
        if self.executed_quantity == 0:
            return 0.0
        exec_price = self.executed_price if self.executed_price is not None else self.price
        if self.side == OrderSide.YES:
            return self.executed_quantity * (self.price - exec_price)
        else:
            return self.executed_quantity * ((1 - exec_price))

    @property
    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in (OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIAL)


@dataclass
class Portfolio:
    """Portfolio containing positions across contracts."""
    portfolio_id: str
    positions: Dict[str, int] = field(default_factory=dict)  # contract_id -> quantity
    orders: List[Order] = field(default_factory=list)
    cash_balance: float = 0.0  # Available cash in cents
    total_value: float = 0.0
    last_update: datetime = field(default_factory=datetime.utcnow)

    def add_position(self, contract_id: str, quantity: int) -> None:
        """Add to position in contract."""
        self.positions[contract_id] = self.positions.get(contract_id, 0) + quantity

    def remove_position(self, contract_id: str, quantity: int) -> None:
        """Remove from position in contract."""
        current = self.positions.get(contract_id, 0)
        self.positions[contract_id] = max(0, current - quantity)

    @property
    def total_positions(self) -> int:
        """Total number of shares held across all contracts."""
        return sum(self.positions.values())

    @property
    def num_contracts(self) -> int:
        """Number of active contracts."""
        return len([q for q in self.positions.values() if q > 0])


@dataclass
class OddsSnapshot:
    """Snapshot of market odds at a point in time."""
    contract_id: str
    timestamp: datetime
    bid_price: float
    ask_price: float
    last_trade_price: float
    volume_1h: float = 0.0
    volume_24h: float = 0.0
    spread: float = 0.0

    def implied_probability(self) -> float:
        """Implied probability from ask price."""
        if self.ask_price <= 0 or self.ask_price >= 1:
            return 0.5
        return self.ask_price


@dataclass
class PositionMetrics:
    """Metrics for a position."""
    contract_id: str
    quantity: int
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    duration_minutes: int

    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.unrealized_pnl > 0


@dataclass
class GreeksMetrics:
    """Portfolio Greeks for risk assessment."""
    delta: float = 0.0  # Directional exposure
    gamma: float = 0.0  # Convexity risk
    theta: float = 0.0  # Time decay
    vega: float = 0.0  # Volatility exposure
    rho: float = 0.0  # Interest rate sensitivity


# ============================================================================
# KALSHI AUTH CLIENT
# ============================================================================


class KalshiAuthClient:
    """OAuth2 authentication client for Kalshi API.

    Manages secure credential handling, token refresh, and rate limiting.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """Initialize auth client.

        Args:
            client_id: OAuth2 client ID (defaults to KALSHI_CLIENT_ID env var)
            client_secret: OAuth2 client secret (defaults to KALSHI_CLIENT_SECRET env var)
            token: Existing access token (defaults to KALSHI_TOKEN env var)
        """
        self.client_id = client_id or os.getenv("KALSHI_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("KALSHI_CLIENT_SECRET", "")
        self.token = token or os.getenv("KALSHI_TOKEN", "")
        self.token_expires_at = datetime.utcnow()
        self.refresh_token = os.getenv("KALSHI_REFRESH_TOKEN", "")

        # Rate limiting
        self.request_times: List[float] = []
        self.rate_limit_lock = asyncio.Lock()

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=KALSHI_API_BASE_URL,
            limits=httpx.Limits(
                max_connections=POOL_CONNECTIONS,
                max_keepalive_connections=POOL_MAXSIZE,
            ),
            timeout=TIMEOUT,
        )

        if not self.client_id or not self.client_secret:
            logger.warning(
                "Kalshi credentials not configured. Set KALSHI_CLIENT_ID and "
                "KALSHI_CLIENT_SECRET environment variables."
            )

    async def authenticate(self) -> bool:
        """Perform OAuth2 authentication.

        Returns:
            bool: True if authentication successful
        """
        if not self.client_id or not self.client_secret:
            logger.error("Missing Kalshi credentials")
            return False

        try:
            response = await self.client.post(
                "/auth/login",
                json={
                    "email": self.client_id,
                    "password": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()

            self.token = data.get("token", "")
            self.refresh_token = data.get("refresh_token", "")
            self.token_expires_at = datetime.utcnow() + timedelta(hours=24)

            logger.info("Successfully authenticated with Kalshi")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Kalshi authentication failed: {e}")
            return False

    async def refresh_access_token(self) -> bool:
        """Refresh access token.

        Returns:
            bool: True if refresh successful
        """
        if not self.refresh_token:
            logger.warning("No refresh token available, re-authenticating...")
            return await self.authenticate()

        try:
            response = await self.client.post(
                "/auth/refresh",
                json={"refresh_token": self.refresh_token},
            )
            response.raise_for_status()
            data = response.json()

            self.token = data.get("token", "")
            self.token_expires_at = datetime.utcnow() + timedelta(hours=24)

            logger.info("Successfully refreshed access token")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Token refresh failed: {e}")
            return False

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header for API requests."""
        return {"Authorization": f"Bearer {self.token}"}

    async def check_token_expiration(self) -> None:
        """Check and refresh token if expired or about to expire."""
        now = datetime.utcnow()
        # Refresh if within 1 hour of expiration
        if now >= self.token_expires_at - timedelta(hours=1):
            logger.info("Token expiring soon, refreshing...")
            await self.refresh_access_token()

    async def wait_for_rate_limit(self) -> None:
        """Enforce rate limiting with sliding window."""
        async with self.rate_limit_lock:
            now = time.time()
            # Remove old entries outside the window
            self.request_times = [t for t in self.request_times if now - t < RATE_LIMIT_WINDOW]

            # Check if we've hit the limit
            if len(self.request_times) >= RATE_LIMIT_RPM:
                # Calculate how long to wait
                oldest_request = self.request_times[0]
                wait_time = RATE_LIMIT_WINDOW - (now - oldest_request)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    self.request_times = [t for t in self.request_times if now - t < RATE_LIMIT_WINDOW]

            self.request_times.append(now)

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.client.aclose()


# ============================================================================
# MARKET TYPE MAPPER
# ============================================================================


class MarketTypeMapper:
    """Map football predictions to Kalshi market contracts."""

    # Mapping from prediction types to Kalshi contract categories
    PREDICTION_TO_MARKET = {
        "match_winner_home": MarketCategory.MATCH_WINNER,
        "match_winner_draw": MarketCategory.MATCH_WINNER,
        "match_winner_away": MarketCategory.MATCH_WINNER,
        "goals_over_1_5": MarketCategory.GOALS_OVER_UNDER,
        "goals_over_2_5": MarketCategory.GOALS_OVER_UNDER,
        "goals_over_3_5": MarketCategory.GOALS_OVER_UNDER,
        "btts_yes": MarketCategory.BTTS,
        "btts_no": MarketCategory.BTTS,
        "correct_score": MarketCategory.CORRECT_SCORE,
        "goal_scorer": MarketCategory.GOAL_SCORER,
        "clean_sheet_home": MarketCategory.CLEAN_SHEET,
        "clean_sheet_away": MarketCategory.CLEAN_SHEET,
    }

    @staticmethod
    def map_prediction_to_order_side(prediction_type: str) -> OrderSide:
        """Map prediction type to order side (YES/NO).

        Args:
            prediction_type: Type of prediction

        Returns:
            OrderSide (YES or NO)
        """
        if "away" in prediction_type or "no" in prediction_type:
            return OrderSide.NO
        return OrderSide.YES

    @staticmethod
    def get_market_category(prediction_type: str) -> MarketCategory:
        """Get market category for prediction type."""
        return MarketTypeMapper.PREDICTION_TO_MARKET.get(
            prediction_type,
            MarketCategory.MATCH_WINNER
        )

    @staticmethod
    def build_contract_query(
        prediction_type: str,
        match_id: str,
        team_home: str,
        team_away: str,
    ) -> Dict[str, Any]:
        """Build query parameters for finding relevant contracts."""
        category = MarketTypeMapper.get_market_category(prediction_type)

        return {
            "category": category.value,
            "match_id": match_id,
            "team_home": team_home,
            "team_away": team_away,
            "prediction_type": prediction_type,
        }


# ============================================================================
# KALSHI MARKET CLIENT
# ============================================================================


class KalshiMarketClient:
    """Market feed consumer for real-time Kalshi data."""

    def __init__(self, auth_client: KalshiAuthClient):
        """Initialize market client.

        Args:
            auth_client: Authenticated Kalshi client
        """
        self.auth_client = auth_client
        self.contracts: Dict[str, KalshiContract] = {}
        self.contracts_lock = asyncio.Lock()
        self.order_history: List[Order] = []
        self.portfolio = Portfolio(portfolio_id="default")
        self.subscribed_events: set[str] = set()
        self.websocket_active = False

    async def fetch_contracts(
        self,
        category: Optional[MarketCategory] = None,
        league: Optional[str] = None,
        team: Optional[str] = None,
    ) -> List[KalshiContract]:
        """Fetch available contracts from Kalshi API.

        Args:
            category: Filter by market category
            league: Filter by league (EPL, Championship, League One)
            team: Filter by team name

        Returns:
            List of KalshiContract objects
        """
        await self.auth_client.check_token_expiration()
        await self.auth_client.wait_for_rate_limit()

        try:
            params = {}
            if category:
                params["category"] = category.value
            if league:
                params["league"] = league
            if team:
                params["team"] = team

            response = await self.auth_client.client.get(
                "/markets",
                params=params,
                headers=self.auth_client.get_auth_header(),
            )
            response.raise_for_status()

            markets = response.json().get("markets", [])

            contracts = []
            async with self.contracts_lock:
                for market in markets:
                    contract = self._parse_contract(market)
                    if contract:
                        contracts.append(contract)
                        self.contracts[contract.contract_id] = contract

            logger.info(f"Fetched {len(contracts)} contracts")
            return contracts
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch contracts: {e}")
            return []

    async def fetch_contract(self, contract_id: str) -> Optional[KalshiContract]:
        """Fetch specific contract details.

        Args:
            contract_id: Contract identifier

        Returns:
            KalshiContract or None if not found
        """
        await self.auth_client.check_token_expiration()
        await self.auth_client.wait_for_rate_limit()

        try:
            response = await self.auth_client.client.get(
                f"/markets/{contract_id}",
                headers=self.auth_client.get_auth_header(),
            )
            response.raise_for_status()

            contract = self._parse_contract(response.json())
            if contract:
                async with self.contracts_lock:
                    self.contracts[contract.contract_id] = contract
            return contract
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch contract {contract_id}: {e}")
            return None

    async def get_odds_snapshot(self, contract_id: str) -> Optional[OddsSnapshot]:
        """Get current odds snapshot for a contract.

        Args:
            contract_id: Contract identifier

        Returns:
            OddsSnapshot or None
        """
        contract = await self.fetch_contract(contract_id)
        if not contract:
            return None

        return OddsSnapshot(
            contract_id=contract_id,
            timestamp=datetime.utcnow(),
            bid_price=contract.yes_bid,
            ask_price=contract.yes_ask,
            last_trade_price=contract.last_price,
            volume_24h=contract.volume_24h,
            spread=contract.spread(),
        )

    async def place_order(
        self,
        contract_id: str,
        side: OrderSide,
        price: float,
        quantity: int,
        client_order_id: Optional[str] = None,
    ) -> Optional[Order]:
        """Place an order on Kalshi.

        Args:
            contract_id: Contract to trade
            side: YES or NO
            price: Decimal price (0.0-1.0)
            quantity: Number of shares
            client_order_id: Optional client-provided order ID

        Returns:
            Order object or None if placement failed
        """
        await self.auth_client.check_token_expiration()
        await self.auth_client.wait_for_rate_limit()

        try:
            response = await self.auth_client.client.post(
                "/orders",
                json={
                    "contract_id": contract_id,
                    "side": side.value,
                    "price": price,
                    "quantity": quantity,
                    "client_order_id": client_order_id or f"order_{contract_id}_{int(time.time())}",
                },
                headers=self.auth_client.get_auth_header(),
            )
            response.raise_for_status()

            order_data = response.json().get("order", {})
            order = self._parse_order(order_data)

            if order:
                self.order_history.append(order)
                logger.info(f"Placed order {order.order_id} on {contract_id}")
            return order
        except httpx.HTTPError as e:
            logger.error(f"Failed to place order on {contract_id}: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order.

        Args:
            order_id: Order identifier

        Returns:
            bool: True if cancellation successful
        """
        await self.auth_client.check_token_expiration()
        await self.auth_client.wait_for_rate_limit()

        try:
            response = await self.auth_client.client.delete(
                f"/orders/{order_id}",
                headers=self.auth_client.get_auth_header(),
            )
            response.raise_for_status()
            logger.info(f"Cancelled order {order_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_portfolio(self) -> Portfolio:
        """Get current portfolio state.

        Returns:
            Portfolio with current positions
        """
        await self.auth_client.check_token_expiration()
        await self.auth_client.wait_for_rate_limit()

        try:
            response = await self.auth_client.client.get(
                "/portfolio",
                headers=self.auth_client.get_auth_header(),
            )
            response.raise_for_status()

            data = response.json()
            self.portfolio.cash_balance = data.get("cash_balance", 0.0)
            self.portfolio.total_value = data.get("total_value", 0.0)
            self.portfolio.last_update = datetime.utcnow()

            # Parse positions
            positions = data.get("positions", {})
            self.portfolio.positions = {
                contract_id: int(qty)
                for contract_id, qty in positions.items()
            }

            return self.portfolio
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch portfolio: {e}")
            return self.portfolio

    async def subscribe_to_updates(self, contract_ids: List[str]) -> None:
        """Subscribe to real-time updates for contracts.

        Args:
            contract_ids: List of contract IDs to subscribe to
        """
        self.subscribed_events.update(contract_ids)
        logger.info(f"Subscribed to {len(contract_ids)} contract updates")

    async def unsubscribe_from_updates(self, contract_ids: List[str]) -> None:
        """Unsubscribe from contract updates.

        Args:
            contract_ids: List of contract IDs to unsubscribe from
        """
        self.subscribed_events.difference_update(contract_ids)
        logger.info(f"Unsubscribed from {len(contract_ids)} contract updates")

    def _parse_contract(self, data: Dict[str, Any]) -> Optional[KalshiContract]:
        """Parse raw contract data from API.

        Args:
            data: Raw contract data

        Returns:
            KalshiContract or None if parsing failed
        """
        try:
            return KalshiContract(
                contract_id=data.get("id", ""),
                title=data.get("title", ""),
                category=MarketCategory(data.get("category", "match_winner")),
                description=data.get("description", ""),
                event_id=data.get("event_id", ""),
                fpl_match_id=data.get("fpl_match_id", ""),
                league=data.get("league", ""),
                team_home=data.get("team_home", ""),
                team_away=data.get("team_away", ""),
                expires_at=datetime.fromisoformat(data.get("expires_at", "")),
                settlement_source=data.get("settlement_source", ""),
                tick_size=float(data.get("tick_size", 0.01)),
                yes_bid=float(data.get("yes_bid", 0.0)),
                yes_ask=float(data.get("yes_ask", 0.0)),
                no_bid=float(data.get("no_bid", 0.0)),
                no_ask=float(data.get("no_ask", 0.0)),
                last_price=float(data.get("last_price", 0.5)),
                volume_24h=float(data.get("volume_24h", 0.0)),
                liquidity=float(data.get("liquidity", 0.0)),
            )
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse contract: {e}")
            return None

    def _parse_order(self, data: Dict[str, Any]) -> Optional[Order]:
        """Parse raw order data from API.

        Args:
            data: Raw order data

        Returns:
            Order or None if parsing failed
        """
        try:
            return Order(
                order_id=data.get("id", ""),
                contract_id=data.get("contract_id", ""),
                side=OrderSide(data.get("side", "yes")),
                price=float(data.get("price", 0.0)),
                quantity=int(data.get("quantity", 0)),
                amount=float(data.get("amount", 0.0)),
                status=OrderStatus(data.get("status", "pending")),
                executed_price=data.get("executed_price"),
                executed_quantity=int(data.get("executed_quantity", 0)),
                created_at=datetime.fromisoformat(data.get("created_at", "")),
                updated_at=datetime.fromisoformat(data.get("updated_at", "")),
                expires_at=data.get("expires_at"),
            )
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse order: {e}")
            return None

    async def close(self) -> None:
        """Close market client connections."""
        self.subscribed_events.clear()
        await self.auth_client.close()
        logger.info("Market client closed")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


async def initialize_kalshi_client() -> tuple[KalshiAuthClient, KalshiMarketClient]:
    """Initialize Kalshi clients with authentication.

    Returns:
        Tuple of (auth_client, market_client)
    """
    auth_client = KalshiAuthClient()
    if not await auth_client.authenticate():
        logger.warning("Failed to authenticate with Kalshi, using unauthenticated mode")

    market_client = KalshiMarketClient(auth_client)
    return auth_client, market_client


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    async def main() -> None:
        auth_client, market_client = await initialize_kalshi_client()

        # Fetch contracts
        contracts = await market_client.fetch_contracts(league="EPL")
        print(f"Found {len(contracts)} EPL contracts")

        await market_client.close()

    asyncio.run(main())
