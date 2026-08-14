# Kalshi MCP - Ejemplos de Implementación

**Fecha:** 2026-08-13  
**Propósito:** Guía de cómo se vería la implementación concreta de nuevas features

---

## 1. Nuevos Clientes HTTP

### Base Client (Refactorizado)

```python
# src/mcp_server_kalshi/clients/base_client.py

from httpx import AsyncClient, HTTPError
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from typing import Any, Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

class BaseKalshiClient:
    """Shared HTTP client with retry logic, caching, and rate limiting"""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.private_key_path = private_key_path
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = None
        self.auth_handler = None
        
    async def __aenter__(self):
        self.client = AsyncClient(timeout=self.timeout)
        if self.api_key:
            from mcp_server_kalshi.auth.kalshi_auth import KalshiAuthHandler
            self.auth_handler = KalshiAuthHandler(
                api_key=self.api_key,
                private_key_path=self.private_key_path
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with automatic retries and error handling"""
        
        url = f"{self.base_url}{path}"
        headers = {}
        
        # Add auth if available
        if self.auth_handler:
            auth_headers = self.auth_handler.get_auth_headers(
                method=method,
                path=path,
                body=body
            )
            headers.update(auth_headers)
        
        headers["Content-Type"] = "application/json"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=body,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except HTTPError as e:
            logger.error(f"HTTP error for {method} {path}: {e}")
            # Specific error handling
            if e.response.status_code == 429:
                logger.warning("Rate limited, retrying...")
                raise  # Will be retried by @retry
            elif e.response.status_code == 401:
                raise ValueError("Authentication failed")
            else:
                raise
    
    async def get(self, path: str, params: Optional[Dict] = None) -> Dict:
        return await self._request("GET", path, params=params)
    
    async def post(self, path: str, body: Optional[Dict] = None) -> Dict:
        return await self._request("POST", path, body=body)
    
    async def patch(self, path: str, body: Optional[Dict] = None) -> Dict:
        return await self._request("PATCH", path, body=body)
    
    async def delete(self, path: str) -> Dict:
        return await self._request("DELETE", path)
```

### Perps Client (NUEVO)

```python
# src/mcp_server_kalshi/clients/perps_client.py

from .base_client import BaseKalshiClient
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime

class PerpsAPIClient(BaseKalshiClient):
    """Kalshi Perps/Margin API client"""
    
    async def list_perps_markets(
        self,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """Get list of perpetual futures markets"""
        response = await self.get(
            "/v1/markets/perps",
            params={"status": status}
        )
        return response.get("markets", [])
    
    async def get_perps_market(self, market_id: str) -> Dict[str, Any]:
        """Get details for a specific perps market"""
        return await self.get(f"/v1/markets/perps/{market_id}")
    
    async def create_perp_order(
        self,
        market_id: str,
        side: str,  # "long" or "short"
        size: float,
        limit_price: Decimal,
        leverage: float,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """Create a margin order with leverage"""
        
        body = {
            "market_id": market_id,
            "side": side,
            "size": float(size),
            "limit_price": str(limit_price),
            "leverage": float(leverage),
            "reduce_only": reduce_only,
            "order_type": "limit"
        }
        
        return await self.post("/v1/orders/perps/create", body=body)
    
    async def get_perp_positions(
        self,
        subaccount_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get margin positions for account/subaccount"""
        
        params = {}
        if subaccount_id:
            params["subaccount_id"] = subaccount_id
        
        response = await self.get("/v1/portfolio/positions/perps", params=params)
        return response.get("positions", [])
    
    async def get_funding_rate(self, market_id: str) -> Dict[str, Any]:
        """Get current and historical funding rates"""
        return await self.get(f"/v1/markets/perps/{market_id}/funding")
    
    async def get_liquidation_price(
        self,
        market_id: str,
        position_size: float,
        leverage: float,
        maintenance_margin_fraction: float = 0.05
    ) -> Decimal:
        """Calculate liquidation price for a position
        
        Formula: Liquidation Price = Entry Price / Leverage + (Position Size / Leverage) * Maintenance Margin
        """
        
        # Get current market data
        market = await self.get_perps_market(market_id)
        current_price = Decimal(str(market["price"]))
        
        # Simplified calculation (would be more complex in production)
        # Assumes position is open at current price
        position_cost = current_price * position_size
        margin_required = position_cost / leverage
        
        # Liquidation occurs when margin < maintenance margin
        liquidation_price = current_price * (
            1 - (1 / leverage) + (maintenance_margin_fraction / leverage)
        )
        
        return max(Decimal(0), liquidation_price)
    
    async def get_margin_requirements(
        self,
        subaccount_id: str = None
    ) -> Dict[str, Any]:
        """Get margin usage and requirements"""
        
        params = {}
        if subaccount_id:
            params["subaccount_id"] = subaccount_id
        
        return await self.get("/v1/portfolio/margin", params=params)
```

---

## 2. Nuevas Tools

### Perps Trading Tool

```python
# src/mcp_server_kalshi/tools/perps_trading.py

from mcp.server.models import Tool
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import json
from ..clients.perps_client import PerpsAPIClient
from ..config import KalshiSettings

class PerpOrderRequest(BaseModel):
    market_id: str = Field(..., description="Market ID for the perpetual futures")
    side: str = Field(..., description="'long' or 'short'")
    size: float = Field(..., description="Position size in contracts")
    limit_price: str = Field(..., description="Limit price as decimal string")
    leverage: float = Field(default=1.0, description="Leverage multiplier (1x-10x)")

class CreatePerpOrder(BaseModel):
    request: PerpOrderRequest
    confirm: bool = Field(default=False, description="Set to true to actually execute")

def get_perps_trading_tools(
    client: PerpsAPIClient,
    settings: KalshiSettings
) -> list[Tool]:
    """Get list of perps trading tools"""
    
    async def create_perp_order(
        market_id: str,
        side: str,
        size: float,
        limit_price: str,
        leverage: float = 1.0,
        confirm: bool = False
    ) -> dict:
        """Create a margin order
        
        Args:
            market_id: Market identifier
            side: 'long' or 'short'
            size: Position size
            limit_price: Price limit as string
            leverage: Leverage multiplier (1x-10x)
            confirm: Set to true to execute (default: preview only)
        
        Returns:
            Order preview or execution result
        """
        
        # Validation
        if side not in ["long", "short"]:
            return {"error": "side must be 'long' or 'short'"}
        
        if leverage < 1.0 or leverage > 10.0:
            return {"error": "leverage must be between 1x and 10x"}
        
        if size <= 0:
            return {"error": "size must be positive"}
        
        try:
            limit_price_decimal = Decimal(limit_price)
        except:
            return {"error": "limit_price must be a valid decimal"}
        
        # Get market info for preview
        try:
            market = await client.get_perps_market(market_id)
            current_price = Decimal(str(market["price"]))
        except Exception as e:
            return {"error": f"Could not fetch market: {str(e)}"}
        
        # Calculate preview data
        position_value = current_price * size
        margin_required = position_value / leverage
        liquidation_price = await client.get_liquidation_price(
            market_id, size, leverage
        )
        
        # Build order preview
        order_preview = {
            "type": "perp_order_preview",
            "market_id": market_id,
            "side": side,
            "size": size,
            "limit_price": limit_price,
            "leverage": leverage,
            "position_value_usd": float(position_value),
            "margin_required_usd": float(margin_required),
            "liquidation_price": float(liquidation_price),
            "current_market_price": float(current_price),
            "price_distance_pct": float(abs(limit_price_decimal - current_price) / current_price * 100),
            "estimated_fees_usd": float(position_value * Decimal("0.002")),  # 0.2% taker fee
            "note": "This is a preview. Set confirm=true to execute.",
            "required_action": "Confirm order execution" if not confirm else "Order will be executed"
        }
        
        if not confirm and not settings.order_preview_only:
            return order_preview
        
        if not confirm:
            return order_preview
        
        # Execute order if confirm=true
        if settings.sandbox_mode:
            # In sandbox, simulate execution
            return {
                **order_preview,
                "status": "SIMULATED_EXECUTION",
                "order_id": f"SIM_{market_id}_{side}_{size}",
                "created_at": "2026-08-13T10:00:00Z",
                "message": "Order executed in sandbox mode"
            }
        
        # Production: actually execute
        try:
            result = await client.create_perp_order(
                market_id=market_id,
                side=side,
                size=size,
                limit_price=limit_price_decimal,
                leverage=leverage
            )
            
            return {
                "status": "EXECUTED",
                "order_id": result.get("order_id"),
                "created_at": result.get("created_at"),
                "preview": order_preview,
                "execution_result": result
            }
        except Exception as e:
            return {"error": f"Failed to create order: {str(e)}"}
    
    return [
        Tool(
            name="create_perp_order",
            description="Create a margin/perpetual futures order with leverage",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_id": {
                        "type": "string",
                        "description": "Market ID (e.g., 'BITCOIN-PERP')"
                    },
                    "side": {
                        "type": "string",
                        "enum": ["long", "short"],
                        "description": "Position direction"
                    },
                    "size": {
                        "type": "number",
                        "description": "Position size in contracts"
                    },
                    "limit_price": {
                        "type": "string",
                        "description": "Limit price as decimal (e.g., '45000.50')"
                    },
                    "leverage": {
                        "type": "number",
                        "description": "Leverage multiplier (1-10x). Default: 1x",
                        "default": 1.0
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Set to true to execute order (default: preview only)",
                        "default": False
                    }
                },
                "required": ["market_id", "side", "size", "limit_price"]
            }
        )
    ]
```

### Advanced Analytics Tool

```python
# src/mcp_server_kalshi/tools/advanced_analytics.py

from mcp.server.models import Tool
from ..clients.predictions_client import PredictionsAPIClient
from typing import Dict, List, Any
import statistics
from decimal import Decimal

def get_advanced_analytics_tools(
    client: PredictionsAPIClient
) -> list[Tool]:
    """Get list of advanced analytics tools"""
    
    async def detect_arbitrage_opportunities(
        max_spread_pct: float = 2.0
    ) -> Dict[str, Any]:
        """Find market arbitrage opportunities
        
        Args:
            max_spread_pct: Maximum spread percentage to consider (default 2%)
        
        Returns:
            List of arbitrage opportunities with entry/exit strategies
        """
        
        # Get all active markets
        markets = await client.list_markets(status="active")
        
        opportunities = []
        
        # Check each market for arbitrage (simplified example)
        for market in markets:
            market_id = market["id"]
            ticker = market["ticker"]
            
            try:
                # Get orderbook
                orderbook = await client.get_market_orderbook(market_id)
                
                # Calculate spread
                best_bid = Decimal(str(orderbook["bids"][0]["price"]))
                best_ask = Decimal(str(orderbook["asks"][0]["price"]))
                
                spread_pct = ((best_ask - best_bid) / best_bid) * 100
                
                if spread_pct > max_spread_pct:
                    # Get recent trades to understand volume
                    trades = await client.get_market_trades(market_id, limit=50)
                    trade_volumes = [t["size"] for t in trades]
                    avg_volume = statistics.mean(trade_volumes) if trade_volumes else 0
                    
                    # Consider it an opportunity
                    if avg_volume > 10:  # Minimum volume requirement
                        opportunities.append({
                            "market_id": market_id,
                            "ticker": ticker,
                            "spread_pct": float(spread_pct),
                            "best_bid": float(best_bid),
                            "best_ask": float(best_ask),
                            "strategy": f"Buy at {best_bid}, sell at {best_ask}",
                            "avg_volume": avg_volume,
                            "estimated_profit_per_contract": float(best_ask - best_bid),
                            "confidence": "HIGH" if spread_pct > 5 else "MEDIUM"
                        })
            except Exception as e:
                continue
        
        # Sort by spread descending
        opportunities.sort(key=lambda x: x["spread_pct"], reverse=True)
        
        return {
            "total_opportunities": len(opportunities),
            "max_spread_filter_pct": max_spread_pct,
            "opportunities": opportunities[:20],  # Top 20
            "summary": f"Found {len(opportunities)} potential arbitrage opportunities"
        }
    
    async def correlate_markets(
        market_ids: List[str],
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate correlation matrix between markets
        
        Args:
            market_ids: List of market IDs to correlate
            days: Number of days of historical data (default 30)
        
        Returns:
            Correlation matrix and interpretation
        """
        
        # Fetch historical data for each market
        price_data = {}
        
        for market_id in market_ids:
            try:
                candlesticks = await client.get_market_candlesticks(
                    market_id,
                    interval="1h",  # Hourly data
                    since_timestamp=None  # Last 30 days
                )
                prices = [c["close"] for c in candlesticks]
                price_data[market_id] = prices
            except Exception as e:
                continue
        
        # Calculate correlations (simplified)
        correlation_matrix = {}
        market_list = list(price_data.keys())
        
        for i, m1 in enumerate(market_list):
            correlation_matrix[m1] = {}
            for j, m2 in enumerate(market_list):
                if i == j:
                    correlation_matrix[m1][m2] = 1.0
                elif m1 in correlation_matrix and m2 in correlation_matrix[m1]:
                    continue
                else:
                    # Simplified correlation (would use numpy in production)
                    try:
                        prices1 = price_data[m1]
                        prices2 = price_data[m2]
                        
                        # Calculate Pearson correlation
                        from statistics import stdev, mean
                        x_mean = mean(prices1)
                        y_mean = mean(prices2)
                        
                        numerator = sum((prices1[i] - x_mean) * (prices2[i] - y_mean) 
                                      for i in range(min(len(prices1), len(prices2))))
                        denominator = (stdev(prices1) * stdev(prices2)) if stdev(prices1) and stdev(prices2) else 1
                        
                        correlation = numerator / denominator if denominator else 0
                        correlation = max(-1, min(1, correlation))  # Clamp to [-1, 1]
                        
                        correlation_matrix[m1][m2] = round(float(correlation), 3)
                    except:
                        correlation_matrix[m1][m2] = 0.0
        
        # Interpret
        strong_correlations = [
            (m1, m2, corr) 
            for m1 in correlation_matrix 
            for m2, corr in correlation_matrix[m1].items() 
            if 0.7 < corr < 1.0 or -1.0 < corr < -0.7
        ]
        
        return {
            "correlation_matrix": correlation_matrix,
            "period_days": days,
            "markets_analyzed": market_list,
            "strong_correlations": strong_correlations,
            "diversification_score": 1 - (len(strong_correlations) / len(market_list) if market_list else 0)
        }
    
    return [
        Tool(
            name="detect_arbitrage_opportunities",
            description="Find profitable arbitrage opportunities across markets",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_spread_pct": {
                        "type": "number",
                        "description": "Maximum spread % to consider as opportunity",
                        "default": 2.0
                    }
                }
            }
        ),
        Tool(
            name="correlate_markets",
            description="Calculate correlation matrix between multiple markets",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of market IDs to analyze"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data",
                        "default": 30
                    }
                },
                "required": ["market_ids"]
            }
        )
    ]
```

---

## 3. Pydantic Models

```python
# src/mcp_server_kalshi/models.py (additions)

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class PerpMarket(BaseModel):
    market_id: str
    ticker: str
    description: str
    base_asset: str
    quote_asset: str = "USD"
    price: Decimal
    impact_bid_price: Decimal
    impact_ask_price: Decimal
    open_interest: float
    funding_rate_current: float
    funding_rate_annual: float
    max_leverage: float
    next_funding_payment: datetime

class PerpPosition(BaseModel):
    market_id: str
    side: str  # "long" or "short"
    size: float
    entry_price: Decimal
    current_price: Decimal
    current_value: Decimal
    leverage: float
    unrealized_pnl: Decimal
    unrealized_pnl_pct: float
    maintenance_margin: Decimal
    liquidation_price: Decimal
    liquidation_distance_pct: float
    margin_usage_pct: float

class PerpOrder(BaseModel):
    order_id: str
    market_id: str
    side: str
    size: float
    limit_price: Decimal
    leverage: float
    order_type: str
    status: str
    filled_size: float
    created_at: datetime
    updated_at: datetime

class ArbitrageOpportunity(BaseModel):
    market_id: str
    ticker: str
    spread_pct: float
    best_bid: Decimal
    best_ask: Decimal
    avg_volume: float
    estimated_profit_per_contract: Decimal
    strategy: str
    confidence: str

class MarketCorrelation(BaseModel):
    market_id_1: str
    market_id_2: str
    correlation_coefficient: float
    period_days: int
    interpretation: str
```

---

## 4. Configuration

```python
# src/mcp_server_kalshi/config.py (enhanced)

from pydantic_settings import BaseSettings
from typing import Optional

class KalshiSettings(BaseSettings):
    # Environment
    kalshi_env: str = "demo"  # demo | prod
    
    # Authentication
    kalshi_api_key: Optional[str] = None
    kalshi_private_key_path: Optional[str] = None
    
    # Client Configuration
    base_url: Optional[str] = None  # Auto-determined from env
    timeout: int = 30
    max_retries: int = 3
    
    # Rate Limiting
    rate_limit_per_second: int = 50
    rate_limit_per_hour: int = 10000
    burst_capacity: int = 10  # +10% above per-second limit
    
    # WebSocket
    websocket_enabled: bool = False
    websocket_heartbeat: int = 30
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size_mb: int = 100
    
    # Features
    enable_perps: bool = True
    enable_block_trades: bool = True
    enable_rfq: bool = True
    enable_batch_orders: bool = True
    
    # Safety
    sandbox_mode: bool = True
    require_confirmation: bool = True
    order_preview_only: bool = False  # Always preview unless confirm=true
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Auto-determine base_url if not set
        if not self.base_url:
            if self.kalshi_env == "prod":
                self.base_url = "https://api.kalshi.com"
            else:
                self.base_url = "https://demo-api.kalshi.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## 5. Uso desde Claude

```python
# Ejemplo: Cómo se vería desde Claude

# Request 1: Preview
tools.create_perp_order(
    market_id="BTC-PERP",
    side="long",
    size=0.5,
    limit_price="45000.50",
    leverage=2.0,
    confirm=False
)

# Response: Preview con detalles
{
    "type": "perp_order_preview",
    "market_id": "BTC-PERP",
    "side": "long",
    "size": 0.5,
    "position_value_usd": 22500.25,
    "margin_required_usd": 11250.125,
    "liquidation_price": 43200.00,
    "current_market_price": 45001.00,
    "price_distance_pct": 0.001,
    "estimated_fees_usd": 45.00,
    "note": "This is a preview. Set confirm=true to execute."
}

# Request 2: Confirm execution
tools.create_perp_order(
    market_id="BTC-PERP",
    side="long",
    size=0.5,
    limit_price="45000.50",
    leverage=2.0,
    confirm=True  # ← Only now it actually executes
)

# Response: Execution result
{
    "status": "EXECUTED",
    "order_id": "ORDER_12345",
    "created_at": "2026-08-13T10:00:00Z",
    "preview": {...},  # Same as above
    "execution_result": {
        "filled_size": 0.5,
        "average_fill_price": 45000.50,
        "position_opened": true
    }
}

# Request 3: Analytics
tools.detect_arbitrage_opportunities(max_spread_pct=2.0)

# Response
{
    "total_opportunities": 15,
    "opportunities": [
        {
            "market_id": "ELECTION-2026",
            "ticker": "TRUMP-2026",
            "spread_pct": 3.5,
            "best_bid": 0.55,
            "best_ask": 0.57,
            "strategy": "Buy at 0.55, sell at 0.57",
            "avg_volume": 500,
            "confidence": "HIGH"
        },
        {...}
    ]
}
```

---

**Ejemplos Creados:** 2026-08-13  
**Propósito:** Guía de implementación concreta
