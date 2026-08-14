# Kalshi MCP - Quick Start Guide

**Fecha:** 2026-08-13  
**Propósito:** Iniciar desarrollo inmediatamente

---

## 📋 Pre-requisitos

```bash
# 1. Clone the repository
git clone https://github.com/cabad79/kalshi-dev-mcp.git
cd kalshi-dev-mcp

# 2. Install Python 3.10+
python --version  # Must be >= 3.10

# 3. Install uv (fast Python package manager)
pip install uv

# 4. Install dependencies
uv sync

# 5. Create .env file
cat > .env << EOF
KALSHI_ENV=demo
KALSHI_API_KEY=your_api_key_here
KALSHI_PRIVATE_KEY_PATH=./path/to/private/key.pem
LOG_LEVEL=DEBUG
EOF

# 6. Verify installation
python -m pytest tests/ -v
```

---

## 🚀 Fase 1: Fundamento (Semana 1-2)

### Goal
Refactorizar arquitectura base, mejorar clientes HTTP, aumentar test coverage

### Checklist

#### 1.1 Setup & Refactoring (2 days)
- [ ] Create `src/mcp_server_kalshi/clients/base_client.py`
  - [ ] Implement `BaseKalshiClient` class
  - [ ] Add retry logic with `tenacity`
  - [ ] Add error handling
  - [ ] Add logging

- [ ] Refactor existing clients
  - [ ] Extract common code to `base_client.py`
  - [ ] Update `PredictionsAPIClient` to inherit from base
  - [ ] Add type hints 100%
  - [ ] Update docstrings

#### 1.2 Utilities Layer (2 days)
- [ ] Create `src/mcp_server_kalshi/utils/market_cache.py`
  - [ ] Implement LRU cache with TTL
  - [ ] Add cache statistics
  - [ ] Add invalidation methods

- [ ] Create `src/mcp_server_kalshi/utils/validators.py`
  - [ ] Validate market IDs
  - [ ] Validate order parameters
  - [ ] Validate prices
  - [ ] Validate quantity

- [ ] Enhance `src/mcp_server_kalshi/utils/formatters.py`
  - [ ] Format prices with appropriate decimals
  - [ ] Format orders for display
  - [ ] Format dates consistently

#### 1.3 Configuration (1 day)
- [ ] Enhance `src/mcp_server_kalshi/config.py`
  - [ ] Add new settings from plan
  - [ ] Auto-determine base_url
  - [ ] Add logging configuration
  - [ ] Add rate limiting config

#### 1.4 Testing (2 days)
- [ ] Update test fixtures
  - [ ] Create market fixtures
  - [ ] Create order fixtures
  - [ ] Create response fixtures

- [ ] Add unit tests for new modules
  - [ ] `tests/unit/test_base_client.py`
  - [ ] `tests/unit/test_market_cache.py`
  - [ ] `tests/unit/test_validators.py`

- [ ] Run coverage check
  ```bash
  pytest tests/ --cov=src/mcp_server_kalshi --cov-report=html
  # Target: >80% coverage
  ```

#### 1.5 Documentation (1 day)
- [ ] Create `docs/ARCHITECTURE.md`
- [ ] Create `docs/CONTRIBUTING.md`
- [ ] Update `README.md`

### Deliverable: MCP v0.3.0
```bash
# Version update
# pyproject.toml: version = "0.3.0"

# Create git commit
git add .
git commit -m "refactor: improve base architecture and code quality for v0.3.0"
git tag v0.3.0

# Commands to run before merge:
pytest tests/ -v --cov
black src/ tests/
ruff check src/ tests/
mypy src/
```

---

## 💡 Fase 2: Predictions+ (Semana 2-3)

### Goal
Maximizar valor de Predictions API actual

### Checklist

#### 2.1 Market Discovery Enhancement (2 days)
- [ ] Enhance `src/mcp_server_kalshi/tools/market_discovery.py`
  - [ ] Create `search_markets()` tool
    - [ ] Filter by category
    - [ ] Filter by ticker
    - [ ] Filter by status
    - [ ] Filter by minimum volume
    - [ ] Sort options
  
  - [ ] Create `get_market_summary()` tool
    - [ ] Basic info (name, category)
    - [ ] Current pricing (bid/ask/last)
    - [ ] Activity level (volume trend)
    - [ ] Liquidity metrics

- [ ] Test all new tools
  ```bash
  pytest tests/unit/test_market_discovery.py -v
  ```

#### 2.2 Portfolio Analytics (2 days)
- [ ] Enhance `src/mcp_server_kalshi/tools/portfolio_management.py`
  - [ ] Create `get_portfolio_pnl()` tool
    - [ ] Calculate realized P&L
    - [ ] Calculate unrealized P&L
    - [ ] Calculate fees paid
    - [ ] Return summary

  - [ ] Create `get_portfolio_concentration()` tool
    - [ ] Concentration by market
    - [ ] Concentration by category
    - [ ] Risk metrics

  - [ ] Create `list_subaccounts()` tool
  - [ ] Create `transfer_between_subaccounts()` tool

#### 2.3 Advanced Orders (1 day)
- [ ] Enhance `src/mcp_server_kalshi/tools/trading_operations.py`
  - [ ] Create `batch_create_orders()` tool
  - [ ] Create `create_order_group()` tool
  - [ ] Add preview functionality

#### 2.4 Market Research Enhancement (1 day)
- [ ] Enhance `src/mcp_server_kalshi/tools/market_research.py`
  - [ ] Create `analyze_market_sentiment()` tool
  - [ ] Create `get_comparable_markets()` tool

#### 2.5 Testing (1 day)
- [ ] Add integration tests
  ```bash
  pytest tests/integration/test_predictions_end_to_end.py -v
  ```

### Deliverable: MCP v0.4.0
```bash
# pyproject.toml: version = "0.4.0"
git add .
git commit -m "feat: enhance predictions API tools and portfolio analytics for v0.4.0"
git tag v0.4.0
```

---

## 🎯 Fase 3: Perps Trading (Semana 3-4)

### Goal
Soporte completo para Futuros/Margin

### Checklist

#### 3.1 Perps Client (2 days)
- [ ] Create `src/mcp_server_kalshi/clients/perps_client.py`
  - [ ] `list_perps_markets()`
  - [ ] `get_perps_market()`
  - [ ] `create_perp_order()`
  - [ ] `get_perp_positions()`
  - [ ] `get_funding_rate()`
  - [ ] `get_liquidation_price()`
  - [ ] `get_margin_requirements()`

- [ ] Add comprehensive error handling

#### 3.2 Perps Tools (2 days)
- [ ] Create `src/mcp_server_kalshi/tools/perps_trading.py`
  - [ ] All tools from implementation examples
  - [ ] Preview functionality
  - [ ] Confirmation gates

- [ ] Enhance `src/mcp_server_kalshi/tools/risk_management.py`
  - [ ] `calculate_portfolio_exposure()`
  - [ ] `simulate_liquidation_cascade()`
  - [ ] `get_concentration_risk()`

#### 3.3 Models (1 day)
- [ ] Update `src/mcp_server_kalshi/models.py`
  - [ ] Add `PerpMarket` model
  - [ ] Add `PerpPosition` model
  - [ ] Add `PerpOrder` model
  - [ ] Add risk models

#### 3.4 Testing (1 day)
- [ ] Add perps tests
  - [ ] `tests/unit/test_perps_client.py`
  - [ ] `tests/unit/test_perps_trading.py`
  - [ ] `tests/integration/test_perps_end_to_end.py`

### Deliverable: MCP v0.5.0
```bash
# pyproject.toml: version = "0.5.0"
git add .
git commit -m "feat: add complete perps/margin trading support for v0.5.0"
git tag v0.5.0
```

---

## 🔥 Fase 4: Advanced Features (Semana 4-5)

### Goal
Capabilities premium y análisis avanzado

### Checklist

#### 4.1 Advanced Analytics (2 days)
- [ ] Create `src/mcp_server_kalshi/tools/advanced_analytics.py`
  - [ ] `detect_arbitrage_opportunities()`
  - [ ] `correlate_markets()`
  - [ ] `forecast_market_resolution()`
  - [ ] `analyze_order_book_imbalance()`
  - [ ] `calculate_historical_statistics()`

#### 4.2 WebSocket Client (2 days)
- [ ] Create `src/mcp_server_kalshi/clients/websocket_client.py`
  - [ ] Order book streaming
  - [ ] Trade streaming
  - [ ] Fill notifications
  - [ ] Event subscriptions

- [ ] Create `src/mcp_server_kalshi/tools/real_time_data.py`
  - [ ] `subscribe_order_book()`
  - [ ] `subscribe_trades()`
  - [ ] `subscribe_fills()`

#### 4.3 Performance (1 day)
- [ ] Benchmark API calls
- [ ] Optimize caching
- [ ] Profile code
  ```bash
  python -m cProfile -s cumtime main.py
  ```

### Deliverable: MCP v0.6.0
```bash
# pyproject.toml: version = "0.6.0"
git add .
git commit -m "feat: add advanced analytics and real-time streaming for v0.6.0"
git tag v0.6.0
```

---

## ✨ Fase 5: Production Ready (Semana 5-6)

### Goal
Polish, documentación, audit de seguridad

### Checklist

#### 5.1 Documentation (2 days)
- [ ] Create `docs/TOOLS_REFERENCE.md`
- [ ] Create `docs/EXAMPLES.md`
  - [ ] Basic market research example
  - [ ] Swing trading bot example
  - [ ] Portfolio analysis example
  - [ ] Perps leverage trading example

- [ ] Create `docs/API_MAPPING.md`
  - [ ] Kalshi API → MCP tools mapping
  - [ ] Completitud de cobertura (should be 100%)

- [ ] Update `README.md` with new features

#### 5.2 Testing & Quality (2 days)
- [ ] Integration testing completo
  ```bash
  pytest tests/integration/ -v
  ```

- [ ] Type checking
  ```bash
  mypy src/ --strict
  ```

- [ ] Code quality
  ```bash
  black src/ tests/ --check
  ruff check src/ tests/ --select=E,W,F,I
  ```

- [ ] Security audit
  - [ ] Check for hardcoded secrets
  - [ ] Review auth handling
  - [ ] Check input validation

#### 5.3 Docker & Deployment (1 day)
- [ ] Update `Dockerfile`
- [ ] Test Docker build
  ```bash
  docker build -t mcp-server-kalshi:1.0.0 .
  docker run -it mcp-server-kalshi:1.0.0
  ```

#### 5.4 Final Release (1 day)
- [ ] Update version in all places
- [ ] Create CHANGELOG.md
- [ ] Create release notes

### Deliverable: MCP v1.0.0
```bash
# Final version update
# pyproject.toml: version = "1.0.0"

git add .
git commit -m "release: v1.0.0 - production-ready Kalshi MCP with comprehensive API coverage"
git tag v1.0.0

# Push to GitHub
git push origin main
git push origin --tags

# Create GitHub Release with notes
gh release create v1.0.0 \
  --title "Kalshi MCP v1.0.0 - Production Ready" \
  --notes-file RELEASE_NOTES.md
```

---

## 🏃 Running Each Phase

### Phase 1 - Create branch and start
```bash
git checkout -b feature/phase-1-architecture
# Complete checklist items
# Run tests, commits as you go
git push origin feature/phase-1-architecture
# Create PR, review, merge
```

### Phase 2 - Continue
```bash
git checkout -b feature/phase-2-predictions
# Complete checklist items
git push origin feature/phase-2-predictions
# PR → merge
```

And so on for phases 3, 4, 5...

---

## 📊 Success Metrics per Phase

### Phase 1 (v0.3.0)
- [ ] Test coverage ≥ 80%
- [ ] Type hints 100%
- [ ] All existing tools working
- [ ] 0 critical issues

### Phase 2 (v0.4.0)
- [ ] 10+ new tools
- [ ] Portfolio analytics working
- [ ] Test coverage ≥ 82%

### Phase 3 (v0.5.0)
- [ ] 12+ perps tools
- [ ] Liquidation calculations accurate
- [ ] Margin simulation working
- [ ] Test coverage ≥ 85%

### Phase 4 (v0.6.0)
- [ ] 45+ total tools
- [ ] WebSocket streaming working
- [ ] Analytics algorithms verified
- [ ] Performance <200ms p90

### Phase 5 (v1.0.0)
- [ ] 50+ tools
- [ ] 100% API coverage
- [ ] Test coverage >85%
- [ ] Complete documentation
- [ ] 5+ working examples

---

## 🔍 Daily Workflow

```bash
# Start day
git pull origin main
git checkout feature/phase-X-name

# Development loop
# 1. Make changes
code src/mcp_server_kalshi/...

# 2. Test immediately
pytest tests/unit/test_specific.py -v

# 3. Check quality
black src/
ruff check src/
mypy src/

# 4. Small commits
git add src/mcp_server_kalshi/module.py
git commit -m "feat: add specific functionality"

# End of day
# 5. Push to branch
git push origin feature/phase-X-name

# 6. Check PR status in GitHub
# 7. Review any feedback
```

---

## 🐛 Debugging Tips

```python
# Enable debug logging
export LOG_LEVEL=DEBUG

# Test specific tool
pytest tests/unit/test_module.py::test_specific -v -s

# Profile performance
python -m cProfile -s cumtime src/mcp_server_kalshi/server.py | head -20

# Check type errors
mypy src/ --show-error-context --show-error-codes

# Dry-run formatting
black --check src/

# Find potential bugs
ruff check src/ --select=E,W,F,I,C90,B
```

---

## 📞 Key Resources

**Documentation Files:**
- `KALSHI_MCP_PLAN.md` - Complete detailed plan
- `KALSHI_MCP_EXECUTIVE_SUMMARY.md` - High-level overview
- `ARCHITECTURE_DIAGRAM.md` - Visual architecture
- `IMPLEMENTATION_EXAMPLES.md` - Code examples
- `QUICK_START_GUIDE.md` - This file

**External:**
- Kalshi API Docs: https://docs.kalshi.com
- MCP Protocol: https://modelcontextprotocol.io
- GitHub Repo: https://github.com/cabad79/kalshi-dev-mcp

---

## ✅ Ready to Start?

1. ✅ Read `KALSHI_MCP_EXECUTIVE_SUMMARY.md` (5 min)
2. ✅ Review `ARCHITECTURE_DIAGRAM.md` (10 min)
3. ✅ Clone repository and run tests (5 min)
4. ✅ Create feature/phase-1-architecture branch
5. ✅ Start with checklist items for Phase 1

**Total prep time: ~20 minutes → Ready to code!**

---

**Guide Created:** 2026-08-13  
**Time to v1.0:** ~6 weeks (part-time) or ~4 weeks (full-time)
