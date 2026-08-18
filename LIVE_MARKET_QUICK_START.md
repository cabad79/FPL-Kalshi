# Live Market Integration - Quick Start (30 minutes)

## Step 1: Update .env (2 minutes)

**File:** `C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi\.env`

**Change these lines:**

```env
# BEFORE:
KALSHI_ENV=demo
KALSHI_SECRET_KEY=

# AFTER:
KALSHI_ENV=live
KALSHI_SECRET_KEY=your_production_secret_key_from_kalshi.com
```

Then restart container:
```powershell
docker-compose -f docker-compose-simple.yml restart kalshi-mcp-v0.4.0
```

---

## Step 2: Update kalshi_client.py (5 minutes)

**File:** `fpl-mcp-v2/src/fpl_mcp/kalshi_client.py`

**Find this method (around line 120):**
```python
async def place_order(self, order: Order) -> dict:
    """Place order"""
    response = await self.api_request('POST', '/orders', order.to_dict())
    return response
```

**Replace with:**
```python
async def place_market_order(
    self, 
    contract_id: str, 
    side: str,  # 'yes' or 'no'
    quantity: int,
    limit_price: float | None = None
) -> dict:
    """Place real money order on live Kalshi"""
    
    # Validate inputs
    if side not in ['yes', 'no']:
        raise ValueError(f"Invalid side: {side}")
    
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive: {quantity}")
    
    # Get current contract
    contract = await self.api_request('GET', f'/contracts/{contract_id}')
    if not contract:
        raise ValueError(f"Contract not found: {contract_id}")
    
    # Get market price
    market_price = contract.get('yes_ask' if side == 'yes' else 'no_ask')
    
    # Check limit price
    if limit_price and market_price > limit_price:
        print(f"⚠️  Skipped: market ${market_price} > limit ${limit_price}")
        return None
    
    # Place order (REAL MONEY!)
    order_data = {
        "contract_id": contract_id,
        "side": side,
        "quantity": quantity,
        "price": market_price,
        "type": "MARKET"
    }
    
    response = await self.api_request('POST', '/orders', order_data)
    
    if response:
        print(f"✅ Order {response.get('order_id')} filled")
    
    return response
```

---

## Step 3: Create live_market_connector.py (15 minutes)

**File:** `fpl-mcp-v2/src/fpl_mcp/live_market_connector.py`

**Create new file with:**
```python
"""Live market connector - real Kalshi integration"""

import asyncio
import httpx
from datetime import datetime, timezone

from .kalshi_client import KalshiAuthClient, KalshiMarketClient
from .services.data_service import apply_kelly_criterion


class LiveMarketConnector:
    """Sync FPL fixtures to Kalshi markets"""
    
    def __init__(self, api_key: str, secret_key: str, bankroll: float = 10000):
        self.auth = KalshiAuthClient(api_key, secret_key)
        self.market = KalshiMarketClient(self.auth)
        self.bankroll = bankroll
        self.http = httpx.AsyncClient(timeout=10)
    
    async def get_upcoming_fixtures(self) -> list[dict]:
        """Get EPL/Championship fixtures from FPL API"""
        
        response = await self.http.get(
            "https://fantasy.premierleague.com/api/fixtures/",
            params={"event__gt": 0}
        )
        fixtures = response.json()
        
        # Only upcoming (not started)
        upcoming = [
            f for f in fixtures
            if not f.get("started") and f.get("kickoff_time")
        ]
        
        return upcoming
    
    async def run_trading_loop(self, min_confidence: float = 0.70):
        """Main trading loop"""
        
        print("🚀 Starting live market connector...")
        
        while True:
            try:
                fixtures = await self.get_upcoming_fixtures()
                print(f"📊 Found {len(fixtures)} upcoming matches")
                
                for fixture in fixtures:
                    # Get Kalshi contracts for this match
                    # TODO: Implement market mapping (FPL team ID -> Kalshi contract)
                    
                    # For now, just log
                    print(f"  - {fixture.get('team_h')} vs {fixture.get('team_a')}")
                
                # Check every 5 minutes
                await asyncio.sleep(300)
            
            except Exception as e:
                print(f"❌ Error in trading loop: {e}")
                await asyncio.sleep(10)


async def main():
    """Run connector"""
    
    import os
    
    api_key = os.getenv('KALSHI_API_KEY')
    secret_key = os.getenv('KALSHI_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Missing KALSHI_API_KEY or KALSHI_SECRET_KEY in .env")
        return
    
    connector = LiveMarketConnector(api_key, secret_key)
    await connector.run_trading_loop()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 4: Test it Works (5 minutes)

**Inside Docker container:**

```bash
# Enter container
docker exec -it kalshi-mcp-v0.4.0 bash

# Test Kalshi connection
python3 -c "
import os
from fpl_mcp.kalshi_client import KalshiAuthClient

api_key = os.getenv('KALSHI_API_KEY')
secret_key = os.getenv('KALSHI_SECRET_KEY')

auth = KalshiAuthClient(api_key, secret_key)
print('✅ Kalshi client initialized')

# Try to authenticate
try:
    token = auth.get_access_token()
    print(f'✅ Authentication successful')
    print(f'   Token: {token[:20]}...')
except Exception as e:
    print(f'❌ Auth failed: {e}')
"
```

**Expected output:**
```
✅ Kalshi client initialized
✅ Authentication successful
   Token: eyJhbGciOiJIUzI1NiIs...
```

---

## Step 5: Verify Market Access (3 minutes)

**Inside container:**

```bash
python3 << 'EOF'
import asyncio
from fpl_mcp.kalshi_client import KalshiAuthClient, KalshiMarketClient
import os

async def test():
    auth = KalshiAuthClient(
        os.getenv('KALSHI_API_KEY'),
        os.getenv('KALSHI_SECRET_KEY')
    )
    market = KalshiMarketClient(auth)
    
    # Get available contracts
    contracts = await market.get_contracts()
    print(f"✅ Found {len(contracts)} available contracts")
    
    # Show first 5
    for contract in contracts[:5]:
        print(f"  - {contract.get('title')}")
        print(f"    YES: {contract.get('yes_bid')}-{contract.get('yes_ask')}")

asyncio.run(test())
EOF
```

**Expected output:**
```
✅ Found 247 available contracts
  - EPL_20250120_MANU_vs_CITY_1X2
    YES: 0.38-0.40
  - EPL_20250120_MANU_vs_CITY_OVER_2_5_GOALS
    YES: 0.65-0.67
  ...
```

---

## Success Criteria Checklist

After these 5 steps:

- [ ] `.env` has `KALSHI_ENV=live` (not `demo`)
- [ ] Container restarted successfully
- [ ] `place_market_order()` method exists in `kalshi_client.py`
- [ ] `live_market_connector.py` created
- [ ] Authentication test passes ✅
- [ ] Can fetch live contracts ✅

**Then you're ready for Phase 2: Risk Management & Testing**

---

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'fpl_mcp'"
**Solution:** Inside container, reinstall:
```bash
cd /app/fpl-mcp-v2
pip install -e "."
```

### Issue: "Authentication failed"
**Solution:** Check credentials:
```bash
echo $KALSHI_API_KEY
echo $KALSHI_SECRET_KEY
```

### Issue: "Connection refused"
**Solution:** Verify Kalshi API is up:
```bash
curl https://api.kalshi.com/health
```

---

## Next Steps

1. **Phase 2:** Add portfolio monitoring
2. **Phase 3:** Implement Kelly criterion sizing
3. **Phase 4:** Run 50+ demo trades
4. **Phase 5:** Go live with real money ⚠️

**Estimated time: 30 minutes to get live market data streaming**
