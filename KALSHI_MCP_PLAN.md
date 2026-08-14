# Plan de Construcción: Kalshi MCP Server

**Fecha:** 2026-08-13  
**Estado:** Plan Estratégico - Fase de Investigación Completada  
**Versión Actual MCP:** 0.2.3

---

## 1. ANÁLISIS ACTUAL

### 1.1 Kalshi API - Capacidades Disponibles

#### Predictions API (Mercados de Eventos)
- **REST & WebSocket:** Acceso a datos de mercado en tiempo real
- **FIX Protocol:** Para traders institucionales
- **Endpoints Principales:**
  - Mercados y series (filtrado, búsqueda)
  - Order book (bid/ask levels)
  - Candlesticks (1m, 1h, 1d)
  - Trades (historial ejecutado)
  - Órdenes (crear, modificar, cancelar, batch)
  - Portfolio (balance, posiciones, fills, settlements)
  - Subaccounts (hasta 63 cuentas)
  - Block trades y RFQ (negociación OTC)

#### Perps API (Futuros/Margin)
- **REST & WebSocket:** Trading con apalancamiento
- **Órdenes marginales** con ratios de liquidación
- **Funding rates** y pagos históricos
- **Risk controls:** FCM subtraders, price banding
- **Portfolio management:** Leverage ratios, notional exposure

### 1.2 MCP Existente - Análisis Actual

**Versión:** 0.2.3  
**Stack:** Python 3.10+, mcp 1.28.1-<2, httpx, cryptography, pydantic

**Herramientas Implementadas:**
- ✅ Market Discovery: `list_markets`, `get_market`, `list_events`
- ✅ Market Research: `get_market_orderbook`, `get_market_candlesticks`, `get_market_trades`
- ✅ Rules & Documentation: `get_market_rules`, `fetch_rules_pdf`
- ✅ Portfolio: `get_balance`, `get_positions`, `get_fills`, `get_settlements`
- ✅ Trading: `create_order`, `cancel_order`, `amend_order`, `decrease_order`
- ✅ Exchange Info: `get_exchange_status`, `get_exchange_schedule`

**Características de Seguridad:**
- ✅ Sandbox por defecto (demo)
- ✅ Confirmation gates para órdenes
- ✅ Autenticación RSA-PSS con MGF1-SHA256
- ✅ Soporte para API keys opcionales

**Configuración:**
- ✅ KALSHI_ENV (demo/prod)
- ✅ KALSHI_API_KEY
- ✅ KALSHI_PRIVATE_KEY_PATH

---

## 2. GAPS Y OPORTUNIDADES

### 2.1 Funcionalidad No Cubierta

#### High Priority (Impacto Inmediato)
1. **Perps Markets** - No hay soporte actual para futuros/margin
   - `list_perps_markets`
   - `get_perps_market`
   - `create_perp_order`
   - `get_perp_positions`
   - `get_funding_rate`
   - `get_liquidation_price`

2. **Advanced Order Types** - Falta cobertura
   - Batch orders
   - Order groups (auto-cancelación por límites)
   - RFQ system (quotes, negociación)
   - Block trades (OTC)

3. **Subaccounts** - Necesario para traders multi-cuenta
   - `list_subaccounts`
   - `create_subaccount`
   - `get_subaccount_balance`
   - Routing de órdenes por subaccount

4. **Real-time Data** - WebSocket para streaming
   - Order book updates
   - Trade stream
   - Fill notifications
   - Lifecycle events
   - Candlestick updates

#### Medium Priority (Funcionalidad Robusta)
5. **Advanced Analytics**
   - `get_historical_ohlc` (mercados archivados)
   - `get_market_statistics` (volatilidad, volumen)
   - `analyze_correlation` (entre mercados)
   - `get_implied_probability` (de precios)

6. **Risk Management Tools**
   - `calculate_portfolio_exposure`
   - `estimate_liquidation_risk` (perps)
   - `get_margin_requirements`
   - `simulate_order_impact`

7. **Historical Data & Backtesting**
   - `get_historical_trades`
   - `get_historical_fills`
   - `backtest_strategy` (integración con datos)

#### Low Priority (Mejoras Futuras)
8. **Advanced Features**
   - FIX protocol support
   - Deposit/withdrawal tracking
   - Tax reporting helpers
   - Alert configuration

### 2.2 Problemas de Experiencia Actual

1. **Descubrimiento de Mercados**
   - Kalshi no tiene búsqueda por texto libre
   - Necesita mejor filtrado y categorización
   - Sugerencia: `search_markets` con múltiples criterios

2. **Análisis Limitado**
   - Sin herramientas de análisis técnico integradas
   - Sin correlación entre mercados
   - Sin histórico de precios formateado

3. **Gestión de Portfolio**
   - Sin cálculo automático de P&L
   - Sin análisis de concentración
   - Sin recomendaciones de rebalanceo

4. **Información Contextual**
   - Rules PDF extraction actual (necesita mejoría)
   - Falta resumen ejecutivo de mercados
   - Sin notificaciones de cambios importantes

---

## 3. ARQUITECTURA PROPUESTA

### 3.1 Estructura del Proyecto Mejorada

```
kalshi-dev-mcp/
├── src/
│   └── mcp_server_kalshi/
│       ├── server.py                    # Entry point (existente)
│       ├── config.py                    # Configuration (mejorado)
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── kalshi_auth.py          # Auth handler (mejorado)
│       │   └── signing.py              # RSA signing (existente)
│       ├── clients/
│       │   ├── __init__.py
│       │   ├── base_client.py          # Base HTTP client
│       │   ├── predictions_client.py   # Predictions API
│       │   ├── perps_client.py         # Perps API (NUEVO)
│       │   └── websocket_client.py     # WebSocket support (NUEVO)
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── market_discovery.py     # Markets, events (mejorado)
│       │   ├── market_research.py      # Orderbook, trades, analytics (mejorado)
│       │   ├── portfolio_management.py # Balance, positions (mejorado)
│       │   ├── trading_operations.py   # Orders (mejorado)
│       │   ├── perps_trading.py        # Perp orders (NUEVO)
│       │   ├── risk_management.py      # Risk tools (NUEVO)
│       │   ├── advanced_analytics.py   # Analytics (NUEVO)
│       │   ├── real_time_data.py       # WebSocket tools (NUEVO)
│       │   └── utilities.py            # Helper functions (mejorado)
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── formatters.py           # Data formatting
│       │   ├── validators.py           # Input validation
│       │   ├── market_cache.py         # Caching layer (NUEVO)
│       │   └── error_handling.py       # Custom exceptions
│       └── models.py                    # Pydantic models (expandido)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
│   ├── ARCHITECTURE.md                 # Diseño del sistema
│   ├── TOOLS_REFERENCE.md              # Referencia de herramientas
│   ├── EXAMPLES.md                     # Casos de uso
│   └── API_MAPPING.md                  # Mapping Kalshi → MCP
├── examples/
│   ├── basic_market_research.py
│   ├── swing_trading_bot.py
│   ├── portfolio_analysis.py
│   └── perps_leverage_trading.py
├── Dockerfile                           # Docker support
├── pyproject.toml                       # Dependencies (expandido)
└── README.md                            # Updated documentation
```

### 3.2 Nuevos Clientes HTTP

```python
# clients/predictions_client.py - Mejorado
class PredictionsAPIClient:
    """Enhanced Kalshi Predictions API client"""
    - Market discovery with filtering
    - Advanced orderbook queries
    - Batch order operations
    - Subaccount support
    - Rate limiting awareness

# clients/perps_client.py - NUEVO
class PerpsAPIClient:
    """Kalshi Perps/Margin API client"""
    - Margin order creation/management
    - Leverage and liquidation calculations
    - Funding rate queries
    - Risk metric retrieval

# clients/websocket_client.py - NUEVO
class KalshiWebSocketClient:
    """Real-time data streaming"""
    - Order book subscriptions
    - Trade feed streaming
    - Fill notifications
    - Custom event subscriptions
```

### 3.3 Nuevas Herramientas (Tools)

#### Predictions Enhancement
```python
# market_discovery.py - Mejorado
search_markets(
    category=str,
    ticker=str,
    status=str,
    min_volume=float,
    expiration_before=date,
    sort_by=str
) → Market[]

get_market_summary(market_id: str) → {
    basic_info, pricing, liquidity, activity_level
}

# market_research.py - Mejorado
analyze_market_sentiment(market_id: str) → {
    implied_probability, volatility, volume_trend
}

get_comparable_markets(market_id: str) → Market[]

calculate_implied_statistics(market_id: str) → {
    expected_value, kelly_criterion, break_even
}

# trading_operations.py - Mejorado
batch_create_orders(orders: Order[]) → OrderResult[]

create_order_group(
    orders: Order[],
    cancel_condition: str
) → OrderGroup

# portfolio_management.py - Mejorado
get_portfolio_pnl(subaccount_id?: str) → {
    realized, unrealized, fees, total
}

get_portfolio_concentration(subaccount_id?: str) → {
    by_market, by_category, by_expiration
}

list_subaccounts() → Subaccount[]

transfer_between_subaccounts(
    from_id: str,
    to_id: str,
    amount: decimal
) → Transaction
```

#### Perps Trading - NUEVO
```python
# perps_trading.py - NUEVO
list_perps_markets() → PerpMarket[]

get_perp_market(market_id: str) → PerpMarket

create_perp_order(
    market_id: str,
    side: "long" | "short",
    size: float,
    limit_price: decimal,
    leverage: float  # 1x-10x típicamente
) → OrderResult

amend_perp_order(order_id: str, updates: dict) → OrderResult

cancel_perp_order(order_id: str) → bool

get_perp_positions(subaccount_id?: str) → PerpPosition[]

get_liquidation_price(
    market_id: str,
    position_size: float,
    leverage: float
) → decimal

get_funding_rate(market_id: str) → {
    current_rate, annual_rate, next_payment_time
}

get_margin_requirements(subaccount_id?: str) → {
    initial_margin, maintenance_margin, available_margin
}
```

#### Risk Management - NUEVO
```python
# risk_management.py - NUEVO
calculate_portfolio_vat(subaccount_id?: str) → {
    total_exposure, by_market, by_category
}

simulate_liquidation_cascade(
    market_id: str,
    price_move_percent: float
) → {
    liquidation_price, forced_close_details
}

get_margin_usage(subaccount_id?: str) → {
    used_margin, available_margin, utilization_pct
}

calculate_breakeven_analysis(
    market_id: str,
    position: str,
    entry_price: decimal
) → {
    breakeven_price, fee_impact, probability
}

get_concentration_risk(subaccount_id?: str) → {
    top_positions, correlation_matrix, diversification_score
}
```

#### Advanced Analytics - NUEVO
```python
# advanced_analytics.py - NUEVO
get_market_snapshot(market_id: str) → {
    price, spread, volume, volatility, momentum
}

detect_arbitrage_opportunities(
    max_spread: float = 0.02
) → ArbitrageOpportunity[]

correlate_markets(
    market_ids: str[],
    days: int = 30
) → CorrelationMatrix

forecast_market_resolution(
    market_id: str,
    method: "bayesian" | "trend" | "ensemble"
) → Forecast

analyze_order_book_imbalance(market_id: str) → {
    buy_pressure, sell_pressure, imbalance_ratio
}

calculate_historical_statistics(
    market_id: str,
    days: int = 90
) → {
    avg_daily_volume, volatility, max_spread, win_rate
}
```

#### Real-time Data - NUEVO
```python
# real_time_data.py - NUEVO
subscribe_order_book(
    market_id: str,
    callback: Callable
) → Subscription

subscribe_trades(
    market_id: str,
    callback: Callable
) → Subscription

subscribe_fills(
    user_callback: Callable
) → Subscription

subscribe_market_events(
    event_type: str,
    callback: Callable
) → Subscription

unsubscribe(subscription_id: str) → bool
```

---

## 4. FASES DE IMPLEMENTACIÓN

### Fase 1: Fundamento (Semana 1-2)
**Objetivo:** Refactorización y arquitectura robusta

- [ ] Refactorizar clients/ con base_client.py
- [ ] Implementar mejor caching y rate limiting
- [ ] Mejorar error handling y logging
- [ ] Expandir test coverage (>80%)
- [ ] Documentar arquitectura interna
- [ ] Crear fixtures de test completas

**Deliverable:** MCP v0.3.0 con arquitectura mejorada

### Fase 2: Predictions Enhancement (Semana 2-3)
**Objetivo:** Maximizar valor de Predictions API actual

- [ ] Mejorar `search_markets` con filtrado avanzado
- [ ] Agregar `get_market_summary` y análisis sentiment
- [ ] Implementar batch orders
- [ ] Agregar `get_portfolio_pnl` y análisis de concentración
- [ ] Subaccount support completo
- [ ] Block trades y RFQ básico

**Deliverable:** MCP v0.4.0 con Predictions mejorado

### Fase 3: Perps Implementation (Semana 3-4)
**Objetivo:** Soporte completo para Perps/Margin

- [ ] Implementar `perps_client.py`
- [ ] Todas las herramientas de `perps_trading.py`
- [ ] Risk management para margin
- [ ] Liquidation price calculations
- [ ] Funding rate tracking

**Deliverable:** MCP v0.5.0 con Perps support

### Fase 4: Advanced Features (Semana 4-5)
**Objetivo:** Capabilities avanzadas y análisis

- [ ] Analytics avanzados (correlación, arbitrage detection)
- [ ] WebSocket client y real-time streaming
- [ ] Advanced risk management tools
- [ ] Historical data y backtesting
- [ ] Performance optimizations

**Deliverable:** MCP v0.6.0 con Advanced Features

### Fase 5: Polish & Documentation (Semana 5-6)
**Objetivo:** Producción-ready

- [ ] Comprehensive documentation
- [ ] Example scripts y use cases
- [ ] Integration testing completo
- [ ] Docker optimizations
- [ ] Performance benchmarking
- [ ] Security audit

**Deliverable:** MCP v1.0.0 - Production Ready

---

## 5. DETALLES TÉCNICOS

### 5.1 Mejoras de Configuración

```python
# config.py - Expandido
from pydantic_settings import BaseSettings

class KalshiSettings(BaseSettings):
    # Environment
    kalshi_env: str = "demo"  # demo | prod
    
    # Authentication
    kalshi_api_key: str = None
    kalshi_private_key_path: str = None
    
    # Client Configuration
    base_url: str = None  # Auto-determined from env
    timeout: int = 30
    max_retries: int = 3
    
    # Rate Limiting
    rate_limit_per_second: int = 50
    rate_limit_per_hour: int = 10000
    
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
    order_preview_only: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### 5.2 Modelos Pydantic Expandidos

```python
# models.py - Adicionales necesarios

# Market Data
class PerpMarket(BaseModel):
    market_id: str
    ticker: str
    description: str
    underlying_asset: str
    funding_rate: float
    open_interest: float
    max_leverage: float
    price: Decimal
    impact_bid_price: Decimal
    impact_ask_price: Decimal

class PerpPosition(BaseModel):
    market_id: str
    side: Literal["long", "short"]
    size: float
    entry_price: Decimal
    current_price: Decimal
    leverage: float
    maintenance_margin: Decimal
    liquidation_price: Decimal
    unrealized_pnl: Decimal

# Orders
class PerpOrder(BaseModel):
    order_id: str
    market_id: str
    side: Literal["long", "short"]
    size: float
    limit_price: Decimal
    leverage: float
    status: str
    created_at: datetime
    filled_size: float

# Analytics
class MarketSnapshot(BaseModel):
    market_id: str
    price: Decimal
    bid_ask_spread: float
    volume_24h: float
    volatility: float
    momentum: float
    implied_probability: float

class CorrelationMatrix(BaseModel):
    markets: str[]
    correlations: Dict[str, Dict[str, float]]
    period_days: int
    calculated_at: datetime
```

### 5.3 Mejoras de Seguridad

```python
# auth/kalshi_auth.py - Mejorado

class KalshiAuthHandler:
    """Enhanced authentication with better error handling"""
    
    def validate_credentials(self) -> bool:
        """Validate API key and private key setup"""
        
    def sign_request(self, method: str, path: str, body: str) -> str:
        """RSA-PSS signature con MGF1-SHA256"""
        
    def refresh_if_expired(self) -> bool:
        """Detect and refresh expired credentials"""
        
    def get_auth_headers(self) -> Dict[str, str]:
        """Build auth headers with timestamp and nonce"""

class RateLimiter:
    """Token bucket rate limiter"""
    - Per-second limits
    - Per-hour limits
    - Burst capacity
    - Backoff strategy

class RequestValidator:
    """Input validation for all requests"""
    - Market ID format
    - Order parameters
    - Price ranges
    - Quantity limits
```

### 5.4 Caching Layer

```python
# utils/market_cache.py - NUEVO

class MarketCache:
    """LRU cache con TTL para market data"""
    
    def get_market(self, market_id: str) -> Market:
        """Get from cache or API"""
        
    def get_order_book(self, market_id: str) -> OrderBook:
        """Cache order book con TTL corto (1-5s)"""
        
    def invalidate(self, market_id: str) -> None:
        """Manual invalidation"""
        
    def get_stats(self) -> CacheStats:
        """Cache hit/miss metrics"""

class PerformanceTracker:
    """Track API call performance"""
    - Response times
    - Error rates
    - Cache hit rates
```

---

## 6. TESTING STRATEGY

### 6.1 Unit Tests
```
tests/unit/
├── test_auth.py
├── test_predictions_client.py
├── test_perps_client.py
├── test_market_discovery.py
├── test_trading_operations.py
├── test_portfolio_management.py
├── test_utils.py
└── test_validators.py

Objetivo: >85% coverage
```

### 6.2 Integration Tests
```
tests/integration/
├── test_predictions_end_to_end.py
├── test_perps_end_to_end.py
├── test_order_lifecycle.py
├── test_concurrent_operations.py
└── test_error_scenarios.py

Requisito: Fixtures con Kalshi demo environment
```

### 6.3 Fixtures
```
tests/fixtures/
├── market_fixtures.py     # Sample markets
├── order_fixtures.py      # Sample orders
├── response_fixtures.py   # Mock API responses
└── auth_fixtures.py       # Auth test data
```

---

## 7. DOCUMENTACIÓN

### Archivos a Crear

1. **ARCHITECTURE.md**
   - Diagrama de componentes
   - Flujos de datos
   - Decisiones de diseño

2. **TOOLS_REFERENCE.md**
   - Cada tool con parámetros y ejemplos
   - Formatos de respuesta
   - Casos de error

3. **EXAMPLES.md**
   - Swing trading bot
   - Portfolio analysis
   - Perps leverage trading
   - Arbitrage detection

4. **API_MAPPING.md**
   - Kalshi API → MCP tools mapping
   - Completitud de cobertura

5. **CONTRIBUTING.md**
   - Setup local development
   - Testing requirements
   - Code style guide

---

## 8. DEPENDENCIES UPDATE

### pyproject.toml - Actualizaciones
```toml
[project]
name = "mcp-server-kalshi"
version = "1.0.0"
description = "Production-ready MCP server for Kalshi prediction markets"

dependencies = [
    "mcp >= 1.28.1, < 2",
    "httpx >= 0.24.0",
    "cryptography >= 49.0.0",
    "pypdf >= 4.0.0",
    "pydantic == 2.12.0",
    "pydantic-settings == 2.11.0",
    "python-dotenv >= 1.0.0",
    "tenacity >= 8.2.0",  # Retry logic
    "python-dateutil >= 2.8.0",
]

[project.optional-dependencies]
websocket = ["websockets >= 11.0", "aiohttp >= 3.8.0"]
dev = [
    "black >= 23.0",
    "ruff >= 0.1.0",
    "mypy >= 1.0",
    "pytest >= 7.0",
    "pytest-asyncio >= 0.21.0",
    "pytest-cov >= 4.0",
    "pytest-mock >= 3.10",
    "pre-commit >= 3.0",
]
```

---

## 9. SUCCESS METRICS

### Cobertura de Funcionalidad
- [ ] 100% de endpoints Predictions API cubiertos
- [ ] 100% de endpoints Perps API cubiertos
- [ ] WebSocket support para real-time data
- [ ] 50+ herramientas disponibles

### Calidad de Código
- [ ] Test coverage > 85%
- [ ] Type hints 100%
- [ ] Zero security vulnerabilities
- [ ] Performance: <200ms para 90th percentile

### Documentación
- [ ] README actualizado
- [ ] 5+ ejemplos working
- [ ] API reference completo
- [ ] Architecture documentation

### Usabilidad
- [ ] Installation < 5 minutes
- [ ] First working trade < 15 minutes
- [ ] Claude desktop integration tested
- [ ] Docker deployment tested

---

## 10. PRÓXIMOS PASOS

### Acción Inmediata
1. ✅ **Investigación completada** - Arquitectura API mapeada
2. **Planificación confirmada** - Plan de 6 semanas definido
3. **Fase 1 kickoff** - Iniciar refactorización base

### Para Iniciar Desarrollo
```bash
# Clone repository
git clone https://github.com/cabad79/kalshi-dev-mcp.git
cd kalshi-dev-mcp

# Install dependencies
uv sync

# Start Phase 1
# - Refactor clients/ architecture
# - Implement base_client.py
# - Improve error handling
```

### Decisiones a Tomar
1. ¿Prioridad: Breadth (más endpoints) o Depth (mejor análisis)?
   - **Recomendación:** Breadth primero → v1.0 con cobertura completa
2. ¿WebSocket como MVP o post-v1.0?
   - **Recomendación:** Post-v1.0 (nice-to-have pero no crítico)
3. ¿Docker support en v1.0?
   - **Recomendación:** Sí, crítico para deployment

---

**Plan Creado:** 2026-08-13  
**Timeline Total Estimado:** 6 semanas para v1.0 production-ready  
**Líneas de Código Esperadas:** ~8,000-10,000 loc  
**Test Cases Target:** 150+
