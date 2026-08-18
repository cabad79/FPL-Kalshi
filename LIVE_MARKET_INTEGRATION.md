# v0.4.0 MVP - Live Market Integration Roadmap

Your current v0.4.0 deployment is **demo-only**. Here's exactly what to change for live market trading.

---

## Current Status (Demo)

```
✅ Predictions: Working (95K predictions/sec)
✅ Goal modeling: Working (Poisson)
✅ Match outcomes: Working (ELO + Pythagorean)
✅ Data sources: Working (FPL + Football-Data APIs)
✅ Docker deployment: Working
❌ Live trading: Disabled (demo-only API key)
❌ Real order placement: Not enabled
❌ Live market data: Not enabled
```

---

## Phase 1: Swap Credentials (5 minutes)

### Step 1: Get Live Kalshi Keys

1. Go to https://kalshi.com/account/api
2. Generate **API Key** and **Secret Key** for production
3. Keep them safe (don't commit to git!)

### Step 2: Update .env

**Before:**
```env
KALSHI_ENV=demo
KALSHI_API_URL=https://api.kalshi.com
KALSHI_API_KEY=23ec9891-abf2-47f3-aa4a-867476ed03bf  # Demo key
KALSHI_SECRET_KEY=                                    # Empty
```

**After:**
```env
KALSHI_ENV=live
KALSHI_API_URL=https://api.kalshi.com
KALSHI_API_KEY=your_production_api_key_here
KALSHI_SECRET_KEY=your_production_secret_key_here
```

### Step 3: Restart Container

```bash
# Reload environment variables
docker-compose -f docker-compose-simple.yml restart kalshi-mcp-v0.4.0

# Verify
docker logs kalshi-mcp-v0.4.0 | grep -i "kalshi\|api"
```

✅ **Result:** Now connecting to live Kalshi API (no real trades yet)

---

## Phase 2: Enable Live Market Data (30 minutes)

### Current Implementation
```python
# File: fpl-mcp-v2/src/fpl_mcp/services/data_service.py

# Using hardcoded test fixtures
test_fixtures = [
    {"name": "Manchester City vs Liverpool", "home_xg": 2.1, ...}
]
```

### What You Need

Create new file: `fpl-mcp-v2/src/fpl_mcp/live_market_connector.py`

```python
"""Live market connector - syncs FPL fixtures with Kalshi markets"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncIterator
import httpx

from .kalshi_client import KalshiAuthClient, KalshiMarketClient
from .skills.goal_prediction import predict_match_goals
from .skills.match_outcomes import predict_match_outcome
from .services.data_service import apply_kelly_criterion


class LiveMarketConnector:
    """Sync live FPL fixtures to Kalshi prediction markets"""
    
    def __init__(self, kalshi_auth: KalshiAuthClient, bankroll: float = 10000):
        self.kalshi_auth = kalshi_auth
        self.kalshi_market = KalshiMarketClient(kalshi_auth)
        self.bankroll = bankroll
        self.http_client = httpx.AsyncClient()
    
    async def get_live_fixtures(self) -> list[dict]:
        """Fetch upcoming EPL/Championship/League One fixtures from FPL API"""
        
        # FPL API endpoint for fixtures
        response = await self.http_client.get(
            "https://fantasy.premierleague.com/api/fixtures/",
            params={"event__gt": 0}  # All remaining gameweeks
        )
        fixtures = response.json()
        
        # Filter for upcoming matches only (not started)
        upcoming = [
            f for f in fixtures 
            if not f.get("started") and f.get("team_h") and f.get("team_a")
        ]
        
        return upcoming
    
    async def sync_predictions_to_markets(self) -> AsyncIterator[dict]:
        """
        Main loop: get fixtures → predict → size → yield order
        Call this in your trading loop
        """
        
        fixtures = await self.get_live_fixtures()
        
        for fixture in fixtures:
            # Get team data
            home_team = fixture["team_h"]
            away_team = fixture["team_a"]
            kickoff = fixture["kickoff_time"]
            
            # Skip if match already started
            if datetime.fromisoformat(kickoff) < datetime.now(tz=datetime.timezone.utc):
                continue
            
            # Predict match outcome
            prediction = predict_match_outcome({
                "home_rating": 1900,  # TODO: fetch from ELO cache
                "away_rating": 1700,
                "home_goals_for": 1.8,
                "home_goals_against": 0.9,
                "away_goals_for": 1.2,
                "away_goals_against": 1.4,
            })
            
            # Get current odds from Kalshi
            contracts = await self.kalshi_market.get_contracts()
            market = self._find_matching_market(contracts, home_team, away_team)
            
            if not market:
                continue
            
            # Size order using Kelly criterion
            kelly = apply_kelly_criterion(
                probability=prediction["home_win"],
                odds=market["yes_ask"],
                bankroll=self.bankroll,
                kelly_fraction=0.25
            )
            
            yield {
                "fixture_id": fixture["id"],
                "market_id": market["id"],
                "prediction": prediction,
                "kelly_sizing": kelly,
                "contract": market
            }
    
    def _find_matching_market(self, contracts: list[dict], home_id: int, away_id: int) -> dict | None:
        """Find Kalshi contract matching FPL fixture"""
        # This requires mapping FPL team IDs to Kalshi market IDs
        # Kalshi uses market titles like "EPL_20250110_MANU_vs_CITY_1X2"
        # TODO: Build FPL<->Kalshi team ID mapping
        pass


async def main():
    """Run live market connector"""
    
    # Initialize clients
    auth = KalshiAuthClient(
        api_key="your_production_api_key",
        secret_key="your_production_secret_key"
    )
    
    connector = LiveMarketConnector(auth, bankroll=10000)
    
    # Stream predictions
    async for order in connector.sync_predictions_to_markets():
        print(f"Opportunity: {order['fixture_id']}")
        print(f"  Kelly sizing: ${order['kelly_sizing']['recommended_stake']:.2f}")
        print(f"  Expected value: ${order['kelly_sizing']['expected_value']:.2f}")
        
        # TODO: Execute order if edge exceeds threshold


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Phase 3: Enable Real Order Placement (45 minutes)

### Current Order Placement (Demo)

```python
# File: fpl-mcp-v2/src/fpl_mcp/kalshi_client.py

async def place_order(self, order: Order) -> dict:
    """This currently creates orders but doesn't execute them"""
    
    # Just creates order object, doesn't call Kalshi API
    response = await self.api_request(
        'POST',
        '/orders',
        order.to_dict()
    )
    return response
```

### Enable Real Order Placement

Replace with:

```python
async def place_market_order(
    self, 
    contract_id: str, 
    side: str,  # 'yes' or 'no'
    quantity: int,
    limit_price: float | None = None
) -> dict:
    """
    Place real money order on live Kalshi markets
    
    Args:
        contract_id: Kalshi contract ID (e.g., "test_abc123")
        side: 'yes' or 'no'
        quantity: Number of contracts to buy
        limit_price: Max price to pay (None = market order)
    
    Returns:
        Order confirmation with order_id, status, fill price
    """
    
    # Get current contract state
    contract = await self.api_request('GET', f'/contracts/{contract_id}')
    
    if not contract:
        raise ValueError(f"Contract {contract_id} not found")
    
    # Determine best price
    if side == 'yes':
        market_price = contract['yes_ask']  # Seller's asking price
    else:
        market_price = contract['no_ask']
    
    # Limit price protection
    if limit_price and market_price > limit_price:
        print(f"⚠️ Market price {market_price} exceeds limit {limit_price}")
        return None
    
    # Create order - REAL MONEY!
    order_payload = {
        "contract_id": contract_id,
        "side": side,
        "quantity": quantity,
        "price": market_price,
        "type": "MARKET"  # Execute immediately
    }
    
    # Execute on Kalshi
    response = await self.api_request('POST', '/orders', order_payload)
    
    if response.get('status') == 'filled':
        print(f"✅ Order {response['order_id']} FILLED")
        print(f"   Quantity: {response['quantity']}")
        print(f"   Fill price: {response['filled_price']}")
        print(f"   Cost: ${response['quantity'] * response['filled_price']:.2f}")
    
    return response
```

### Add to Your Trading Loop

```python
async def execute_live_trade(order_opportunity: dict):
    """Execute real trade if edge is large enough"""
    
    kelly = order_opportunity['kelly_sizing']
    confidence = order_opportunity['prediction']['confidence']
    
    # Only trade if edge > 5% AND confidence > 75%
    if confidence < 0.75:
        print(f"⏭️  Skipping: confidence {confidence:.1%} too low")
        return
    
    # Kelly tells us how much to stake
    stake = kelly['recommended_stake']
    
    # Convert stake to contract quantity
    # (If contract YES price is 0.45, then stake=$100 = ~222 contracts)
    contract = order_opportunity['contract']
    quantity = int(stake / contract['yes_ask'])
    
    # Place real order
    result = await kalshi_market.place_market_order(
        contract_id=contract['contract_id'],
        side='yes',
        quantity=quantity,
        limit_price=contract['yes_ask'] * 1.01  # 1% slippage protection
    )
    
    if result['status'] == 'filled':
        print(f"🎯 Trade executed!")
        return result['order_id']
```

---

## Phase 4: Live Portfolio Monitoring (30 minutes)

Create new file: `fpl-mcp-v2/src/fpl_mcp/portfolio_monitor.py`

```python
"""Real-time portfolio monitoring for live trading"""

import asyncio
from datetime import datetime
from typing import TypedDict


class PortfolioSnapshot(TypedDict):
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    positions_count: int
    portfolio_exposure: float  # % of bankroll at risk
    largest_position: float


class LivePortfolioMonitor:
    """Monitor portfolio P&L in real-time"""
    
    def __init__(self, kalshi_market: KalshiMarketClient, max_daily_loss: float = -1000):
        self.kalshi_market = kalshi_market
        self.max_daily_loss = max_daily_loss
        self.trading_enabled = True
    
    async def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Get current portfolio state"""
        
        # Fetch open positions from Kalshi
        portfolio = await self.kalshi_market.get_portfolio()
        
        total_unrealized = 0.0
        total_realized = 0.0
        positions = []
        
        for position in portfolio.get('positions', []):
            # Get current contract price
            contract = await self.kalshi_market.get_contract(
                position['contract_id']
            )
            
            # Calculate unrealized P&L
            current_price = contract['yes_ask']
            entry_price = position['entry_price']
            quantity = position['quantity']
            
            if position['side'] == 'yes':
                unrealized = (current_price - entry_price) * quantity
            else:  # 'no' position
                unrealized = (1 - current_price - (1 - entry_price)) * quantity
            
            total_unrealized += unrealized
            positions.append({
                'contract_id': position['contract_id'],
                'side': position['side'],
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'unrealized_pnl': unrealized
            })
        
        # Get realized P&L from closed positions
        total_realized = portfolio.get('realized_pnl', 0.0)
        
        return {
            'total_pnl': total_realized + total_unrealized,
            'unrealized_pnl': total_unrealized,
            'realized_pnl': total_realized,
            'positions_count': len(positions),
            'portfolio_exposure': sum(p['unrealized_pnl'] for p in positions),
            'largest_position': max(
                (p['quantity'] for p in positions), 
                default=0
            )
        }
    
    async def check_stop_loss(self) -> bool:
        """Check if stop loss triggered"""
        
        snapshot = await self.get_portfolio_snapshot()
        
        if snapshot['total_pnl'] < self.max_daily_loss:
            print(f"⚠️  STOP LOSS TRIGGERED!")
            print(f"   Current P&L: ${snapshot['total_pnl']:.2f}")
            print(f"   Max loss: ${self.max_daily_loss:.2f}")
            self.trading_enabled = False
            return False
        
        return True
    
    async def monitor_live(self, check_interval_seconds: int = 30):
        """Continuously monitor portfolio"""
        
        while True:
            try:
                snapshot = await self.get_portfolio_snapshot()
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Portfolio Update")
                print(f"  P&L: ${snapshot['total_pnl']:+.2f}")
                print(f"  Unrealized: ${snapshot['unrealized_pnl']:+.2f}")
                print(f"  Positions: {snapshot['positions_count']}")
                
                # Check stop loss
                if not await self.check_stop_loss():
                    print("⛔ Trading halted due to stop loss")
                    break
                
                await asyncio.sleep(check_interval_seconds)
            
            except Exception as e:
                print(f"❌ Portfolio monitor error: {e}")
                await asyncio.sleep(5)
```

---

## Phase 5: Dry-Run in Demo Mode (1-2 days)

### Before Switching to Live Trading

**CRITICAL:** Run 50+ test trades in demo mode first!

```bash
# Keep KALSHI_ENV=demo for now
cat .env | grep KALSHI_ENV
# Should show: KALSHI_ENV=demo

# Run test execution
cd fpl-mcp-v2
python3 tests/integration/test_live_trading_simulation.py -v
```

### Test Checklist

- [ ] Predictions accurate within 5% of model
- [ ] Kelly sizing calculates correctly
- [ ] Orders place and fill in < 500ms
- [ ] Portfolio tracking accurate
- [ ] Stop loss works correctly
- [ ] Logging captures all trades
- [ ] Error handling for network failures
- [ ] Recovery from API timeouts

---

## Phase 6: Go Live (After validation)

### Final Pre-Flight Checklist

```
BEFORE changing KALSHI_ENV to "live":

☐ All unit tests pass (292/292)
☐ 50+ successful demo trades executed
☐ Prediction accuracy validated vs actual results
☐ Kelly sizing tested with different odds
☐ Order execution tested end-to-end
☐ Portfolio tracking verified with real positions
☐ Stop-loss mechanism tested
☐ Error handling for all failure modes
☐ Network resilience verified (test timeouts)
☐ Logging configured and tested
☐ Position size limits set (5% max per position)
☐ Daily loss limit set (-$1,000)
☐ WebSocket connection stable
☐ Real-time price feed operational
☐ Monitoring dashboard accessible
☐ Alert system configured
```

### Step 1: Update .env

```env
KALSHI_ENV=live  # Switch to production

# Risk management
MAX_POSITION_SIZE=100          # Start conservative
MAX_DAILY_LOSS=-1000           # Auto-halt at $1k loss
MAX_CONCURRENT_POSITIONS=5     # Don't overtrade
```

### Step 2: Start Trading

```bash
# Restart container
docker-compose -f docker-compose-simple.yml restart kalshi-mcp-v0.4.0

# Monitor logs in real-time
docker logs -f kalshi-mcp-v0.4.0 | grep -E "Order|FILLED|Error|STOP"
```

### Step 3: Monitor Continuously

```bash
# Check portfolio P&L every 30 seconds
docker exec kalshi-mcp-v0.4.0 python3 -c "
from fpl_mcp.portfolio_monitor import LivePortfolioMonitor
import asyncio

async def monitor():
    monitor = LivePortfolioMonitor()
    await monitor.monitor_live(check_interval_seconds=30)

asyncio.run(monitor())
"
```

### Step 4: Emergency Shutdown

If something goes wrong:

```bash
# Immediate stop
docker-compose -f docker-compose-simple.yml down

# Check position status
docker exec kalshi-mcp-v0.4.0 python3 -c "
from fpl_mcp.kalshi_client import KalshiAuthClient
client = KalshiAuthClient()
portfolio = client.get_portfolio()
print(f'Open positions: {len(portfolio.get(\"positions\", []))}')
"

# Review error logs
docker logs kalshi-mcp-v0.4.0 | tail -100 | grep -i error
```

---

## Files to Create/Modify

| File | Action | Impact |
|------|--------|--------|
| `.env` | Update credentials | Connects to live API |
| `kalshi_client.py` | Add `place_market_order()` | Real order placement |
| `live_market_connector.py` | Create new | Sync fixtures to markets |
| `portfolio_monitor.py` | Create new | Real-time monitoring |
| `docker-compose.yml` | Update env vars | Load live credentials |

---

## Timeline

| Phase | Action | Effort | Pre-requisites |
|-------|--------|--------|---|
| 1 | Swap credentials | 5 min | Kalshi account |
| 2 | Live market data | 30 min | FPL API access |
| 3 | Order placement | 45 min | Phase 2 complete |
| 4 | Monitoring | 30 min | Phase 3 complete |
| 5 | Dry-run testing | 1-2 days | Phase 4 complete |
| 6 | Go live | 30 min | Phase 5 validated |
| **Total** | - | **3-4 days** | - |

---

## Key Differences: Demo vs Live

| Aspect | Demo | Live |
|--------|------|------|
| API Endpoint | demo-api.kalshi.com | api.kalshi.com |
| Money | Fake | **Real** |
| Order Execution | Simulated | Real-time |
| Market Data | Historical | Live streaming |
| Risk | None | $$ ⚠️ |
| Stop Loss | Optional | **Required** |
| Monitoring | Optional | **Required** |

---

## Support

**If anything fails:**

1. Check logs: `docker logs kalshi-mcp-v0.4.0`
2. Verify credentials: `echo $KALSHI_API_KEY` (inside container)
3. Test API connectivity: `curl https://api.kalshi.com/health`
4. Review recent trades: `docker exec kalshi-mcp grep "FILLED" live_trading.log`

---

**Start with Phase 1 (credentials) - takes 5 minutes and is completely safe** ✅
