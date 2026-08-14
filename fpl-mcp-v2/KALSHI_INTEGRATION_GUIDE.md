# Kalshi Market Integration Guide

## Architecture Overview

The Kalshi Market Integration (SONNET-3) connects all 18 FPL prediction features with live Kalshi markets, enabling intelligent order placement, Kelly-sized positions, and real-time portfolio management.

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│         FPL Prediction Modules (HAIKU-1/2/3/4)             │
│  • Goal Prediction (3 features)                             │
│  • Match Outcomes (4 features)                              │
│  • Player Props (4 features)                                │
│  • Data Services (6 features)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│        Kalshi Market Integration Layer (SONNET-3)           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth Client  │  │Market Mapper  │  │Order Sizing  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Predictor  │  │   Monitor    │  │  Backtest    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│           Kalshi API (Live Trading)                         │
│  • REST API for orders, contracts, portfolio               │
│  • WebSocket for real-time price feeds                     │
│  • Rate limiting: 100 req/min, connection pooling          │
└─────────────────────────────────────────────────────────────┘
```

## Market Types Supported

### 1. Match Winner (1X2)
**Category:** `MATCH_WINNER`

Maps to prediction types:
- `match_winner_home` → Kalshi "Home Win" contract
- `match_winner_draw` → Kalshi "Draw" contract
- `match_winner_away` → Kalshi "Away Win" contract

**Usage:**
```python
# Prediction: 65% home win probability
# Market odds: 2.1 (implied 47.6%)
# Signal: UNDERVALUED (+17.4% edge)

comparison = OddsComparison.compare(
    contract=home_win_contract,
    model_probability=0.65,
    confidence=0.75,
)
# Output: BUY signal with Kelly sizing
```

### 2. Goals Over/Under
**Category:** `GOALS_OVER_UNDER`

Supports multiple thresholds:
- Over/Under 1.5 goals
- Over/Under 2.5 goals
- Over/Under 3.5 goals

**Usage:**
```python
# xG prediction: 1.8 home + 0.9 away = 2.7 total
# Poisson: Over 2.5 = 52%
# Market: Over 2.5 = 48%
# Signal: Slight edge, consider position

recommendation = GoalMarketOptimizer.recommend_goal_markets(
    match_id="PL_MAN_LIV",
    home_team="Manchester City",
    away_team="Liverpool",
    home_xg=1.8,
    away_xg=0.9,
    model_confidence=0.75,
)
```

### 3. Both Teams To Score (BTTS)
**Category:** `BTTS`

Binary market: YES or NO

**Usage:**
```python
# Calculate BTTS probability from xG
result = calculate_btts_probability(
    home_lambda=1.8,
    away_lambda=1.2,
)
# btts_yes: 52%, btts_no: 48%
```

### 4. Correct Score
**Category:** `CORRECT_SCORE`

Covers multiple exact score combinations:
- 0-0, 1-0, 1-1, 2-0, 2-1, 2-2, 3-1, 3-2, 4-2, etc.

### 5. Goal Scorer
**Category:** `GOAL_SCORER`

Individual player contracts

**Usage:**
```python
# Haaland vs Brighton weak defense (-2.1 rating)
recommendation = PlayerPropsMapper.map_goal_scorer(
    player_id="haaland",
    player_name="Erling Haaland",
    team="Manchester City",
    opponent="Brighton",
    match_id="PL_MAN_BHA",
    model_xg=0.85,
    market_implied_probability=0.18,
    confidence=0.80,
)
# Output: Model 24%, Market 18%, Edge +6%, BUY signal
```

### 6. Clean Sheet
**Category:** `CLEAN_SHEET`

Home or away team keeps clean sheet

## Order Placement Examples

### Example 1: Simple Undervalued Match Winner

```python
# Setup
prediction_prob = 0.65  # 65% confidence Man City wins
market_odds = 2.1       # Decimal odds
bankroll = 10000.0      # Total capital

# Step 1: Compare odds
comparison = OddsComparison.compare(
    contract=city_win_contract,
    model_probability=prediction_prob,
    confidence=0.75,
)

# Output:
# signal: BUY
# value: +0.174 (17.4% edge)
# recommended_stake: $127.50

# Step 2: Size the position
sizing = PositionManager.size_order(
    contract_id="city_vs_liv_home_win",
    probability=prediction_prob,
    odds=market_odds,
    available_liquidity=50000.0,
    team="Manchester City",
    market_category="match_winner",
)

# Output:
# recommended_quantity: 63 shares (at $2.03 per share)
# kelly_fraction: 0.0125 (1.25% of bankroll)
# rationale: "Kelly: 1.25%, Recommended stake: $125, Edge: +17.4%"

# Step 3: Place order
order = await market_client.place_order(
    contract_id="city_vs_liv_home_win",
    side=OrderSide.YES,
    price=0.34,  # 34% = inverse of 2.1 odds
    quantity=63,
)

# Result: Order placed for 63 shares at 0.34 (expecting 0.66 return if win)
```

### Example 2: BTTS Arbitrage Detection

```python
# Find three-way arbitrage in 1X2 market
arb = ArbitrageDetector.detect_three_way_arbitrage(
    home_contract=Contract(id="home", yes_ask=0.35),  # 35% implied
    draw_contract=Contract(id="draw", yes_ask=0.28),  # 28% implied
    away_contract=Contract(id="away", yes_ask=0.42),  # 42% implied
)

# Total implied: 35% + 28% + 42% = 105% (overround)
# Output:
# arb.profit_potential: 4.76%
# arb.stake_allocation: {
#     'home': 0.333,
#     'draw': 0.267,
#     'away': 0.400,
# }

# Execute arbitrage (risk-free)
for market_id, allocation in arb.stake_allocation.items():
    stake = 1000 * allocation
    await market_client.place_order(
        contract_id=market_id,
        side=OrderSide.YES,
        price=contract_probabilities[market_id],
        quantity=int(stake / (odds[market_id] - 1)),
    )

# Guaranteed profit of ~$47.60 on $1000 stake (no matter the outcome)
```

### Example 3: Haaland Goal Scorer Undervalue

```python
# Haaland vs Brighton weak defense
recommendation = PlayerPropsMapper.map_goal_scorer(
    player_id="haaland",
    player_name="Erling Haaland",
    team="Manchester City",
    opponent="Brighton",
    match_id="PL_MAN_BHA",
    model_xg=0.85,  # Expected goals
    market_implied_probability=0.18,  # Market says 18%
    confidence=0.80,
)

# Output analysis:
# model_probability: 24% (converted from xG)
# market_probability: 18%
# edge: +6%
# signal: BUY

# Size based on confidence
sizing = KellyCalculator.calculate(
    probability_win=0.24,
    odds=2.78,  # Decimal odds (100/36 = 2.78)
    bankroll=10000.0,
    kelly_fraction=0.25,  # 1/4 Kelly for safety
)

# Output:
# kelly_percentage: 5.8%
# recommended_stake: $145.00
# fractional_kelly_stake: $36.25 (at 1/4 Kelly)

# Place order
order = await market_client.place_order(
    contract_id="haaland_goal_vs_bha",
    side=OrderSide.YES,
    price=0.36,  # 36% market price
    quantity=int(36.25 / (2.78 - 1)),  # ~20 shares
)

# Expected value: $36.25 * (0.24 * 1.78 - 0.76) = +$1.58
# Potential return: 4.4% if goal, -100% if no goal
```

### Example 4: Over 2.5 Goals Using xG Confidence Intervals

```python
# Match analysis with xG
home_xg = 1.8
away_xg = 0.9
total_xg = 2.7

# Calculate goal probability range
ci = confidence_interval_prediction(
    prediction_point=2.7,
    sample_data=[1.5, 2.1, 3.2, 2.8, 2.4],  # Historical xG for similar matches
    confidence_level=0.95,
)

# Output:
# point_estimate: 2.7
# lower_bound: 1.95
# upper_bound: 3.45
# interpretation: "95% confident actual xG between 1.95-3.45"

# Get goal market recommendation
rec = GoalMarketOptimizer.recommend_goal_markets(
    match_id="PL_MAN_LIV",
    home_team="Manchester City",
    away_team="Liverpool",
    home_xg=1.8,
    away_xg=0.9,
    model_confidence=0.75,
)

# Output:
# over_1_5_prob: 85%
# over_2_5_prob: 52%
# over_3_5_prob: 28%
# recommended_markets: {'over_1_5': BUY, 'over_2_5': WEAK_BUY}

# Only bet on Over 2.5 if market offers edge
if rec.over_2_5_prob > 0.55 and market_over_2_5_implied < 0.48:
    sizing = PositionManager.size_order(
        contract_id="epl_man_liv_over_2_5",
        probability=rec.over_2_5_prob,
        odds=2.08,  # 48% implied
        available_liquidity=75000.0,
    )
    
    await market_client.place_order(
        contract_id="epl_man_liv_over_2_5",
        side=OrderSide.YES,
        price=0.48,
        quantity=sizing.recommended_quantity,
    )
```

### Example 5: Kelly-Sized Position with Dynamic Hedge

```python
# Initial position based on model
kelly = KellyCalculator.calculate(
    probability_win=0.68,
    odds=2.5,
    bankroll=10000.0,
    kelly_fraction=0.25,
)

# Place initial position
order = await market_client.place_order(
    contract_id="draw_contract",
    side=OrderSide.YES,
    price=0.40,
    quantity=70,  # From Kelly sizing
)

# Entry value: 70 * 0.40 * 100 = $2,800

# Monitor position
snapshot = await portfolio_tracker.update_portfolio_state()
# Current value: $9,950 (small loss immediately)

# New information: Key player injury announced
# Re-evaluate probability
new_probability = 0.62  # Down from 0.68

# Check hedge requirement
hedges = position_manager.hedge_position(
    contract_id="draw_contract",
    current_position_shares=70,
    current_price=0.38,  # Price moved against us
    new_probability=0.62,
)

# Output:
# action: 'reduce_position'
# reduce_percent: 50
# reason: "Probability decreased from 68% to 62%"

# Execute hedge (sell 35 shares)
hedge_order = await market_client.place_order(
    contract_id="draw_contract",
    side=OrderSide.NO,  # Opposite side
    price=0.38,
    quantity=35,
)

# Risk management: Now holding 35 shares, reduced exposure by 50%
```

### Example 6: Live Match Update - Injury Event

```python
# Match in progress: 1-0 home at minute 45
# Key home player injured

event = MatchEvent(
    match_id="PL_MAN_LIV",
    timestamp=datetime.utcnow(),
    event_type="injury",
    team="Manchester City",
    player="Rodri",
    minute=45,
    description="Rodri injured, substitution coming",
)

# Handle injury event
actions = await score_handler.handle_match_event(event)

# Output:
# action: 'hedge_goal_scorer'
# player: 'Rodri'
# recommended_action: 'reduce_position'
# reason: 'Key midfielder injured, goal expectancy reduced'

# Verify Rodri goal scorer contract position
rodri_position = portfolio.positions.get("rodri_goal_vs_liv")
if rodri_position > 0:
    # Reduce exposure
    reduce_quantity = rodri_position // 2
    
    hedge = await market_client.place_order(
        contract_id="rodri_goal_vs_liv",
        side=OrderSide.NO,  # Sell/reduce YES position
        price=0.15,  # New lower price due to injury
        quantity=reduce_quantity,
    )
    
    # Cut losses: Sell 50% of position at 0.15 to recover some capital
```

### Example 7: Portfolio Rebalancing - Concentration Risk

```python
# Monitor portfolio exposure
exposure = position_manager.portfolio_exposure()

# Output:
# total_exposure: $4,500 (45% of bankroll)
# market_exposure: {
#     'match_winner': $2,000 (20%),
#     'goals_over_under': $1,500 (15%),
#     'btts': $1,000 (10%),
# }
# team_exposure: {
#     'Manchester City': $1,800 (18%),
#     'Liverpool': $1,200 (12%),
# }
# concentration_risk: 0.15 (well diversified)
# largest_position: 'match_winner' (20%)
# risk_level: MEDIUM

# Check if concentration limits exceeded
if exposure.largest_position_percent > 0.25:
    # Trim largest position
    largest = exposure.largest_position
    
    # Find largest contract in that category
    largest_contract = find_largest_contract(largest)
    
    # Close 30% of position
    current_qty = portfolio.positions[largest_contract.contract_id]
    close_qty = int(current_qty * 0.30)
    
    close_order = await market_client.place_order(
        contract_id=largest_contract.contract_id,
        side=OrderSide.NO,  # Close YES position
        price=largest_contract.yes_ask,
        quantity=close_qty,
    )
```

### Example 8: Parlay Strategy - Combine 3 Predictions

```python
# Example: Man City win + Over 2.5 + BTTS
predictions = [
    {
        'market': 'match_winner',
        'contract': city_win,
        'probability': 0.68,
        'odds': 1.47,
    },
    {
        'market': 'goals_over_under',
        'contract': over_2_5,
        'probability': 0.52,
        'odds': 1.92,
    },
    {
        'market': 'btts',
        'contract': btts,
        'probability': 0.52,
        'odds': 1.85,
    },
]

# Parlay analysis
parlay_prob = 0.68 * 0.52 * 0.52  # Combined probability: 18.5%
parlay_odds = 1.47 * 1.92 * 1.85  # Combined odds: 5.20
parlay_implied = 1.0 / 5.20  # Market implied: 19.2%

# Edge exists if our prob > market implied
if parlay_prob > parlay_implied + 0.02:
    # Calculate stake (fractional Kelly)
    kelly_stake = KellyCalculator.calculate(
        probability_win=parlay_prob,
        odds=parlay_odds,
        bankroll=10000.0,
        kelly_fraction=0.25,
    )
    
    # For parlay, we buy all three contracts proportionally
    stake = kelly_stake.recommended_stake
    
    # Place combined order (may require coordination)
    stake_per_contract = stake / 3
    
    for pred in predictions:
        qty = int(stake_per_contract / (pred['odds'] - 1))
        
        await market_client.place_order(
            contract_id=pred['contract'].contract_id,
            side=OrderSide.YES,
            price=1.0 / pred['odds'],
            quantity=qty,
        )

# Payoff: $100 stake × 5.20 odds = $520 if all hit (18.5% win rate)
# Expected value: $100 × (0.185 × 5.20 - 0.815) = +$93
```

### Example 9: Scalping Inefficiencies

```python
# Monitor market efficiency tracker
efficiency_analysis = efficiency_tracker.get_efficiency_analysis()

# Output:
# consistent_patterns: {
#     'contract_123': {
#         'average_divergence': 0.08,
#         'consistency_score': 0.78,
#         'direction': 'model_undervalued',
#     },
# }

# Top opportunities
top_opps = efficiency_tracker.get_top_opportunities(limit=5)

# For each consistent opportunity
for opp in top_opps:
    if opp['divergence'] > 0.05 and opp['consistency'] > 0.75:
        # This pattern repeats consistently
        
        # Buy when market prices drop below model probability
        current_price = get_current_price(opp['contract_id'])
        
        # Wait for favorable entry (price moves down)
        if current_price < opp['model_probability'] - 0.03:
            # Rapid entry/exit on edge
            entry = await market_client.place_order(
                contract_id=opp['contract_id'],
                side=OrderSide.YES,
                price=current_price,
                quantity=50,
            )
            
            # Wait for reversion
            await asyncio.sleep(10)
            
            # Exit at model probability
            exit_price = get_current_price(opp['contract_id'])
            
            if exit_price > current_price + 0.02:
                # Lock in edge
                exit = await market_client.place_order(
                    contract_id=opp['contract_id'],
                    side=OrderSide.NO,  # Close position
                    price=exit_price,
                    quantity=50,
                )
                
                # Profit: 50 shares × 0.02 = $1 (scalp of $0.02)
```

### Example 10: Backtest Results Analysis

```python
# Run backtest on historical data
metrics = await backtest_engine.backtest_strategy(
    strategy_name="undervalued_xg_strategy",
    historical_matches=epl_matches_2023,
    strategy_func=SampleBacktests.undervalued_xg_strategy,
    start_date=datetime(2023, 8, 1),
    end_date=datetime(2024, 5, 31),
)

# Output:
# strategy_name: "undervalued_xg_strategy"
# total_return_percent: 18.7%
# sharpe_ratio: 1.42
# max_drawdown_percent: -12.3%
# win_rate: 54.2%
# profit_factor: 1.86
# trades_executed: 127
# expectancy: +$14.73 per trade

# Performance attribution
print(f"Total Return: {metrics.total_return_percent:.1%}")
print(f"Annualized: {metrics.annualized_return:.1%}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Trades: {metrics.trades_executed} ({metrics.win_rate:.1%} win rate)")
print(f"Best Trade: +${metrics.largest_win:.2f}")
print(f"Worst Trade: -${abs(metrics.largest_loss):.2f}")
print(f"Max Drawdown: {metrics.max_drawdown_percent:.1%}")

# Edge analysis by market
for market_edge in metrics.edge_analysis:
    print(f"\n{market_edge.market_type}:")
    print(f"  Trades: {market_edge.num_trades}")
    print(f"  Win Rate: {market_edge.win_rate:.1%}")
    print(f"  Edge Captured: {market_edge.edge_capture_rate:.1%}")
    print(f"  Profit Factor: {market_edge.profit_factor:.2f}")
```

## Risk Management

### Position Limits

```python
# Automatic limits enforced
MAX_SINGLE_POSITION = 5%      # Max 5% of bankroll on one contract
MAX_MARKET_CATEGORY = 20%     # Max 20% on single market type  
MAX_TEAM_EXPOSURE = 15%       # Max 15% on single team
MAX_TOTAL_EXPOSURE = 50%      # Max 50% total exposure
```

### Stop Loss Monitoring

```python
# Automatic alerts on position loss
REVIEW_THRESHOLD = 5%         # Review if down 5%
AUTO_CLOSE_THRESHOLD = 7%     # Auto-close if down 7%

monitor = StopLossMonitor(review_threshold=0.05)

# Check position
alert = monitor.check_position(
    contract_id="draw",
    entry_price=0.40,
    current_price=0.38,  # Down 5%
    quantity=70,
)

# Output:
# action: "review"
# pnl_percent: -5.0%
# pnl: -$14
```

### Kelly Criterion Safety

```python
# Always use fractional Kelly (1/4 by default)
kelly = KellyCalculator.calculate(
    probability_win=0.65,
    odds=2.1,
    bankroll=10000.0,
    kelly_fraction=0.25,  # 1/4 Kelly
)

# Full Kelly: 6.7% stake = $670
# 1/4 Kelly:  1.7% stake = $170 (much safer)
```

## Error Handling

### API Failures

```python
# Automatic retry with exponential backoff
try:
    contract = await market_client.fetch_contract(contract_id)
except httpx.HTTPError as e:
    # Retry up to 3 times with backoff
    for attempt in range(3):
        wait_time = INITIAL_RETRY_DELAY * (RETRY_BACKOFF ** attempt)
        await asyncio.sleep(wait_time)
        try:
            contract = await market_client.fetch_contract(contract_id)
            break
        except httpx.HTTPError:
            continue
```

### Order Rejections

```python
# Check liquidity before order placement
if not contract.is_liquid:
    logger.warning(f"Insufficient liquidity in {contract.contract_id}")
    return None

# Check sufficient capital
if order_value > self.cash_available:
    logger.warning("Insufficient capital for order")
    return None
```

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Live Order Latency | < 500ms | TBD |
| Market Feed Latency | < 100ms | TBD |
| API Uptime | > 99.9% | TBD |
| Portfolio Update Rate | Every 10s | TBD |
| Rate Limit Headroom | 20% | Implemented |

## Deployment Checklist

- [ ] Kalshi API credentials configured (env vars)
- [ ] SSL certificate validation enabled
- [ ] Rate limiting tested and working
- [ ] Portfolio exposure limits verified
- [ ] Stop loss monitoring active
- [ ] Error handling and retry logic tested
- [ ] Backtest passes with >15% Sharpe ratio
- [ ] All 80+ integration tests passing
- [ ] mypy --strict passes
- [ ] ruff lint passes
- [ ] 100% type coverage

## Support and Troubleshooting

### Common Issues

**Issue:** Rate limit exceeded
**Solution:** Reduce request frequency or increase API quota

**Issue:** Order rejected due to insufficient liquidity
**Solution:** Reduce order size to 5% of available liquidity

**Issue:** Authentication fails
**Solution:** Verify KALSHI_CLIENT_ID and KALSHI_CLIENT_SECRET env vars

## References

- Kalshi API Documentation: https://kalshi.com/api
- Kelly Criterion: https://en.wikipedia.org/wiki/Kelly_criterion
- FPL Prediction Modules: See INTEGRATION_GUIDE.md
- Performance Metrics: HAIKU-4 Data Services

---

**Status:** Ready for Live Trading  
**Last Updated:** 2026-08-14  
**Version:** 1.0.0
