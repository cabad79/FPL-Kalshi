# Diagrama de Arquitectura - Kalshi MCP

## 1. Arquitectura General del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Claude / Agents                              │
│                    (MCP Protocol Clients)                            │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                    MCP Interface
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│                    Kalshi MCP Server (Python)                        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Tool Handlers                              │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐ │ │
│  │  │ Market   │ Market   │ Trading  │Portfolio │ Real-time   │ │ │
│  │  │Discovery │Research  │Operations│Management│ Data        │ │ │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────────┘ │ │
│  │  ┌──────────┬──────────┬──────────┬──────────────────────────┐ │ │
│  │  │  Perps  │   Risk   │ Advanced │ Utilities & Validation    │ │ │
│  │  │ Trading │Management│Analytics │                          │ │ │
│  │  └──────────┴──────────┴──────────┴──────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                           │                                        │
│  ┌────────────────────────▼──────────────────────────────────────┐ │
│  │                     API Clients Layer                          │ │
│  │  ┌─────────────────┬─────────────────┬─────────────────────┐ │ │
│  │  │  Base Client    │ Predictions     │     Perps Client    │ │ │
│  │  │  (Shared)       │ Client          │     (NUEVO)         │ │ │
│  │  └─────────────────┴─────────────────┴─────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  WebSocket Client (NUEVO) - Real-time Streaming        │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────┬────────────────────────────────────┘ │
│                          │                                       │
│  ┌──────────────────────▼──────────────────────────────────────┐ │
│  │                  Utilities Layer                            │ │
│  │  ┌──────────────┬──────────────┬──────────────────────────┐ │ │
│  │  │ Market Cache │ Rate Limiter │ Validators & Formatters  │ │ │
│  │  │ (NUEVO)      │              │                          │ │ │
│  │  └──────────────┴──────────────┴──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│  ┌──────────────────────▼──────────────────────────────────────┐ │
│  │              Configuration & Auth                            │ │
│  │  ┌────────────────┬────────────────┬────────────────────┐   │ │
│  │  │ Env Config     │ Auth Handler   │ RSA Signing        │   │ │
│  │  │ (Improved)     │ (Improved)     │ (Signing.py)       │   │ │
│  │  └────────────────┴────────────────┴────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐        ┌──────────┐
   │  REST   │         │WebSocket│        │   FIX    │
   │Protocol │         │Streaming│        │Protocol  │
   └────┬────┘         └────┬────┘        └────┬─────┘
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────▼───────────────────┐
        │                                       │
        │      Kalshi API Infrastructure        │
        │   (https://api.kalshi.com)            │
        │                                       │
        │  ┌─────────────────────────────────┐ │
        │  │ Predictions API                 │ │
        │  │ - Markets, Events               │ │
        │  │ - Orders, Portfolio             │ │
        │  │ - Orderbook, Trades             │ │
        │  └─────────────────────────────────┘ │
        │  ┌─────────────────────────────────┐ │
        │  │ Perps API                       │ │
        │  │ - Margin Orders                 │ │
        │  │ - Leverage Trading              │ │
        │  │ - Funding Rates                 │ │
        │  └─────────────────────────────────┘ │
        │                                       │
        └───────────────────────────────────────┘
```

---

## 2. Flujo de Datos para una Orden de Trading

```
Claude Request
    │
    ▼
┌─────────────────────────────────────┐
│  Tool Handler (trading_operations)  │
│  - Validate parameters              │
│  - Check confirmation flag          │
│  - Build order object               │
└─────────────┬───────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Return Preview Only?│
    │ (confirm=false)     │
    └──────┬──────────────┘
           │ No / Yes
           │
   ┌───────┴──────────┐
   │                  │
   ▼ Yes              ▼ No
[Return]    ┌───────────────────────────────┐
Preview     │ Auth Handler                  │
            │ - Sign request with RSA       │
            │ - Add timestamp & nonce       │
            └──────────┬────────────────────┘
                       │
                       ▼
            ┌───────────────────────────────┐
            │ Rate Limiter                  │
            │ - Check quota                 │
            │ - Update bucket               │
            └──────────┬────────────────────┘
                       │
                       ▼
            ┌───────────────────────────────┐
            │ HTTP Client (Predictions)     │
            │ - POST /orders/create         │
            │ - Timeout: 30s                │
            │ - Retries: 3x with backoff    │
            └──────────┬────────────────────┘
                       │
                       ▼
            ┌───────────────────────────────┐
            │ Kalshi API Server             │
            │ - Validate order              │
            │ - Match orderbook             │
            │ - Return OrderResult          │
            └──────────┬────────────────────┘
                       │
                       ▼
            ┌───────────────────────────────┐
            │ Response Handler              │
            │ - Parse JSON                  │
            │ - Create Order model          │
            │ - Update cache                │
            └──────────┬────────────────────┘
                       │
                       ▼
                   Return to Claude
```

---

## 3. Arquitectura de Caching y Rate Limiting

```
┌────────────────────────────────────────────────────┐
│         Request Handling Pipeline                  │
└────────────┬──────────────────────────────────────┘
             │
    ┌────────▼─────────┐
    │ Check Cache?     │
    │ (TTL based)      │
    └────┬────────┬────┘
         │        │
      Yes│        │No
         │        │
         ▼        ▼
    [Return]   ┌──────────────────┐
             │ Rate Limiter       │
             │                    │
             │ Tokens/Second: 50  │
             │ Tokens/Hour: 10k   │
             │ Burst: +10%        │
             └────┬───────────────┘
                  │
          ┌───────┴──────────┐
          │                  │
       OK │                  │ Rate Limited
         │                   │
         ▼                   ▼
    [Make Request]    [Queue & Retry]
         │                   │
         └───────────────────┘
                 │
         ┌───────▼────────┐
         │ Update Cache   │
         │ (TTL:300s)     │
         └────────────────┘
```

---

## 4. Roadmap de Implementación

```
Semana   Fase         Versión  Herramientas       Status
────────────────────────────────────────────────────────
1-2      Fundamento   v0.3     ─────────────      ▓ 15 (refactored)
         Arquitectura base, caching, testing

2-3      Predictions  v0.4     ▓▓▓▓─────────      ▓ 25 (+10)
         Enhanced discovery, batch orders, analytics

3-4      Perps        v0.5     ▓▓▓▓▓▓▓──────      ▓ 37 (+12)
         Margin trading, leverage, liquidation

4-5      Advanced     v0.6     ▓▓▓▓▓▓▓▓▓───       ▓ 45 (+8)
         Analytics, WebSocket, backtesting

5-6      Production   v1.0     ▓▓▓▓▓▓▓▓▓▓▓       ✓ 50+ (final)
         Polish, documentation, security audit

Legend: ▓ = Implemented | ─ = Planned | ✓ = Complete
```

---

## 5. Componentes de Alto Nivel

### Tools Layer (MCP Interface)
```
┌─────────────────────────────────────────────┐
│            MCP Tools (50+)                  │
├─────────────────────────────────────────────┤
│ Market Discovery (5)                        │
│  - list_markets(filters)                    │
│  - get_market(id)                           │
│  - search_markets(category, ticker, etc)    │
│  - get_market_summary(id)                   │
│  - list_events()                            │
├─────────────────────────────────────────────┤
│ Market Research (8)                         │
│  - get_market_orderbook(id)                 │
│  - get_market_candlesticks(id, interval)    │
│  - get_market_trades(id, limit)             │
│  - analyze_market_sentiment(id)             │
│  - detect_arbitrage_opportunities()         │
│  - correlate_markets(ids, days)             │
│  - ... and 2 more                           │
├─────────────────────────────────────────────┤
│ Trading Operations (6)                      │
│  - create_order(market_id, side, limit)     │
│  - batch_create_orders(orders)              │
│  - amend_order(order_id, updates)           │
│  - cancel_order(order_id)                   │
│  - decrease_order(order_id, size)           │
│  - create_order_group(orders, condition)    │
├─────────────────────────────────────────────┤
│ Perps Trading (12) - NUEVO                  │
│  - create_perp_order(market, side, leverage)│
│  - get_perp_positions(subaccount)           │
│  - get_liquidation_price(market, size)      │
│  - get_funding_rate(market)                 │
│  - ... and 8 more                           │
├─────────────────────────────────────────────┤
│ Portfolio Management (7)                    │
│  - get_balance(subaccount)                  │
│  - get_positions(subaccount)                │
│  - get_fills(market, limit)                 │
│  - get_settlements(market, limit)           │
│  - get_portfolio_pnl(subaccount)            │
│  - list_subaccounts()                       │
│  - transfer_between_subaccounts()           │
├─────────────────────────────────────────────┤
│ Risk Management (8) - NUEVO                 │
│  - calculate_portfolio_exposure()           │
│  - simulate_liquidation_cascade()           │
│  - get_concentration_risk()                 │
│  - calculate_breakeven_analysis()           │
│  - ... and 4 more                           │
├─────────────────────────────────────────────┤
│ Advanced Analytics (8) - NUEVO              │
│  - get_market_snapshot()                    │
│  - forecast_market_resolution()             │
│  - analyze_order_book_imbalance()           │
│  - calculate_historical_statistics()        │
│  - ... and 4 more                           │
├─────────────────────────────────────────────┤
│ Real-time Data (6) - NUEVO                  │
│  - subscribe_order_book(callback)           │
│  - subscribe_trades(callback)               │
│  - subscribe_fills(callback)                │
│  - subscribe_market_events(callback)        │
│  - ... and 2 more                           │
├─────────────────────────────────────────────┤
│ Exchange Info (2)                           │
│  - get_exchange_status()                    │
│  - get_exchange_schedule()                  │
└─────────────────────────────────────────────┘
                    ▲
            (All tools through MCP protocol)
```

### Clients Layer
```
┌──────────────────────────────────┐
│      Base Client (Shared)         │ ← Error handling, retries, logging
├──────────────────────────────────┤
│                                  │
│  ┌──────────────────────────┐    │
│  │ Predictions API Client   │    │ ← Markets, orders, portfolio
│  └──────────────────────────┘    │
│  ┌──────────────────────────┐    │
│  │ Perps API Client (NUEVO) │    │ ← Margin orders, liquidation
│  └──────────────────────────┘    │
│  ┌──────────────────────────┐    │
│  │ WebSocket Client (NUEVO) │    │ ← Real-time streaming
│  └──────────────────────────┘    │
└──────────────────────────────────┘
```

### Utilities Layer
```
┌──────────────────────────────────┐
│      Market Cache (NUEVO)         │ ← LRU + TTL
│  - get_market()                   │
│  - invalidate()                   │
│  - cache_stats()                  │
├──────────────────────────────────┤
│      Rate Limiter (NUEVO)         │ ← Token bucket
│  - check_quota()                  │
│  - update()                       │
├──────────────────────────────────┤
│      Validators (NUEVO)           │ ← Input validation
│  - validate_market_id()           │
│  - validate_order_params()        │
├──────────────────────────────────┤
│      Formatters (Improved)        │ ← Output formatting
│  - format_price()                 │
│  - format_order()                 │
└──────────────────────────────────┘
```

---

## 6. Seguridad - Request Signing Flow

```
User Request
    │
    ▼
┌────────────────────────────────────┐
│ Auth Handler                        │
│ - Load API Key                      │
│ - Load Private Key (RSA)            │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│ Build Canonical Request             │
│ - Method (GET, POST, etc)           │
│ - Path (/orders/create)             │
│ - Body (JSON)                       │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│ Generate Signature                  │
│ - RSA-PSS + MGF1-SHA256             │
│ - Add timestamp (milliseconds)      │
│ - Add nonce (random)                │
│ - Sign: [key + timestamp + nonce]   │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│ Build HTTP Headers                  │
│ Authorization: Bearer {signature}   │
│ X-Kalshi-Timestamp: {timestamp}     │
│ X-Kalshi-Nonce: {nonce}             │
│ X-Kalshi-Key: {api_key}             │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│ Send Signed Request                 │
│ - HTTPS to api.kalshi.com           │
│ - Headers + Body                    │
│ - Kalshi validates signature        │
└────────────────────────────────────┘
```

---

## 7. Estado Actual vs. Plan

```
Current (v0.2.3)        Plan (v1.0)
───────────────        ─────────────
Tools:         15      Tools:         50+
Endpoints:     18       Endpoints:     45+
Test Coverage: 60%      Test Coverage: 85%+
Type Hints:    70%      Type Hints:    100%

Predictions:   80%      Predictions:   100%
Perps:         0%       Perps:         100%
Real-time:     0%       Real-time:     100%

Clients:       2        Clients:       3
APIs:          1        APIs:          3 (REST, WS, FIX-ready)
```

---

## 8. Ejemplos de Tools Nuevas

### Antes (v0.2.3)
```
create_order(market_id, side, limit)
- Básico: solo orden simple
- Sin confirmación
- Sin vista previa
```

### Después (v1.0)
```
create_order(market_id, side, limit, confirm=false)
- Vista previa detallada si confirm=false
- Ejecución si confirm=true
- P&L impact analysis
- Fee calculation

batch_create_orders(orders: Order[])
- Múltiples órdenes en 1 llamada
- Confirmación grupal
- Atomic execution

create_order_group(orders: Order[], cancel_condition)
- Auto-cancel si se cumple condición
- Ej: "cancel all if first fails"
```

### Perps (NUEVO)
```
create_perp_order(
    market_id,
    side: "long" | "short",
    size: float,
    limit_price: decimal,
    leverage: float  # 1x to 10x
)
- Margin order con apalancamiento
- Liquidation price automático
- Funding rate estimation

get_liquidation_price(market_id, position_size, leverage)
- Calcula precio de liquidación
- Incluye margin maintenance
- Con margen de seguridad

get_funding_rate(market_id)
- Tasa de financiamiento actual
- Historial de pagos
- Próximo pago estimado
```

---

**Diagrama Creado:** 2026-08-13  
**Arquitectura Final:** MCP v1.0 Production-Ready
