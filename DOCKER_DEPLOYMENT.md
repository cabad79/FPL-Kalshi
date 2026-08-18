# Kalshi Football Markets MCP v0.4.0 - Docker Deployment Guide

## Quick Start (Local Laptop)

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2.0+
- At least 2GB RAM available for container

### 1. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
# or
code .env  # VS Code
```

**Required Variables:**
```
KALSHI_API_KEY=your_api_key
KALSHI_SECRET_KEY=your_secret_key
FOOTBALL_DATA_API_KEY=your_football_data_key (optional)
```

### 2. Build and Start Container

```bash
# Build Docker image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f kalshi-mcp
```

### 3. Verify Deployment

```bash
# Check container is running
docker-compose ps

# Health check
curl http://localhost:8000/health

# View logs
docker-compose logs kalshi-mcp

# Run tests inside container
docker-compose exec kalshi-mcp pytest tests/ -v
```

---

## Full Container Operations

### Starting the Service
```bash
# Start in background
docker-compose up -d

# Start in foreground (view logs)
docker-compose up

# Start with build
docker-compose up -d --build
```

### Stopping the Service
```bash
# Stop running containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers and volumes (full cleanup)
docker-compose down -v
```

### Viewing Logs
```bash
# View real-time logs
docker-compose logs -f kalshi-mcp

# View last 100 lines
docker-compose logs --tail=100 kalshi-mcp

# View logs from specific time
docker-compose logs --since 2h kalshi-mcp
```

### Executing Commands Inside Container
```bash
# Run bash shell
docker-compose exec kalshi-mcp bash

# Run Python command
docker-compose exec kalshi-mcp python -c "import fpl_mcp; print(fpl_mcp.__version__)"

# Run tests
docker-compose exec kalshi-mcp pytest tests/ -v

# Run specific test file
docker-compose exec kalshi-mcp pytest tests/integration/test_kalshi_integration.py -v

# Check type safety
docker-compose exec kalshi-mcp mypy --strict src/ --ignore-missing-imports

# Run linter
docker-compose exec kalshi-mcp ruff check src/
```

---

## Development Workflow

### 1. Code Changes (Hot Reload)
Since `src/` and `tests/` are mounted as volumes, changes are immediately reflected:

```bash
# Edit code locally
nano fpl-mcp-v2/src/fpl_mcp/kalshi_client.py

# Changes are reflected in container immediately
# Run tests to verify
docker-compose exec kalshi-mcp pytest tests/ -v
```

### 2. Install New Dependencies
```bash
# Edit pyproject.toml locally
nano fpl-mcp-v2/pyproject.toml

# Rebuild container to install new dependencies
docker-compose up -d --build
```

### 3. Debug Inside Container
```bash
# Start Python REPL
docker-compose exec kalshi-mcp python

# Test a module
>>> from fpl_mcp.kalshi_client import KalshiAuthClient
>>> print("Module loaded successfully")
```

---

## Environment Configuration

### Cache Configuration
```env
CACHE_MAX_SIZE=10000         # Max items in cache (default: 10000)
CACHE_TTL_SECONDS=3600       # Cache time-to-live in seconds (default: 1 hour)
```

### Trading Configuration
```env
KELLY_FRACTION=0.25          # Fractional Kelly (1/4 = 25% safety, default: 0.25)
MIN_CONFIDENCE=0.65          # Minimum prediction confidence (default: 65%)
MAX_POSITION_PERCENT=0.05    # Max position per market (default: 5% of bankroll)
```

### Logging Configuration
```env
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## Port Mapping

| Service | Container Port | Local Port | Purpose |
|---------|---|---|---|
| MCP Server | 8000 | 8000 | API endpoints and health checks |
| Redis (optional, v0.5+) | 6379 | 6379 | Distributed caching |

### Change Port Mapping
Edit `docker-compose.yml`:
```yaml
ports:
  - "9000:8000"  # Access at http://localhost:9000
```

---

## Resource Limits

Current Docker resource configuration:
```yaml
cpus: '2'      # Max 2 CPU cores
memory: 2G     # Max 2GB RAM
```

Adjust in `docker-compose.yml` if needed:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs kalshi-mcp

# Common issues:
# 1. Port 8000 already in use
#    Solution: Change port in docker-compose.yml
# 2. Missing environment variables
#    Solution: Ensure .env file exists and is configured
# 3. Insufficient resources
#    Solution: Check Docker Desktop resource allocation
```

### Health Check Failing
```bash
# Test connectivity
docker-compose exec kalshi-mcp curl -f http://localhost:8000/health

# Check service logs
docker-compose logs kalshi-mcp | grep -i error
```

### Tests Failing in Container
```bash
# Run tests with verbose output
docker-compose exec kalshi-mcp pytest tests/ -vv --tb=short

# Run specific test
docker-compose exec kalshi-mcp pytest tests/integration/test_kalshi_integration.py::TestKalshiMarketClient::test_init -vv
```

### Permission Issues
```bash
# Container runs as non-root user (kalshi:1000)
# If you see permission errors, rebuild:
docker-compose down -v
docker-compose up -d --build
```

---

## Monitoring

### Check Container Status
```bash
# Detailed container info
docker-compose ps -a

# Resource usage
docker stats kalshi-mcp

# Inspect container
docker inspect kalshi-mcp-server
```

### View Application Metrics
```bash
# Inside container
docker-compose exec kalshi-mcp python -c "
from fpl_mcp import get_metrics
metrics = get_metrics()
print(f'Predictions/sec: {metrics[\"throughput\"]}')
print(f'Cache hit rate: {metrics[\"cache_hit_rate\"]:.1%}')
"
```

---

## Production Deployment (Future)

For production environments:

1. Use Docker Swarm or Kubernetes
2. Set `LOG_LEVEL=ERROR` in production
3. Use external Redis for caching
4. Configure secrets management (not .env file)
5. Set up monitoring and alerting
6. Use persistent volumes for logs and data

### Example Production Setup (Kubernetes, v0.5+)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kalshi-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kalshi-mcp
  template:
    metadata:
      labels:
        app: kalshi-mcp
    spec:
      containers:
      - name: kalshi-mcp
        image: kalshi-mcp:v0.4.0
        ports:
        - containerPort: 8000
        env:
        - name: KALSHI_API_KEY
          valueFrom:
            secretKeyRef:
              name: kalshi-secrets
              key: api-key
```

---

## Support & Documentation

- **Project Docs**: `./fpl-mcp-v2/INTEGRATION_GUIDE.md`
- **Kalshi Integration**: `./fpl-mcp-v2/KALSHI_INTEGRATION_GUIDE.md`
- **API Reference**: `./fpl-mcp-v2/QA_FINAL_SIGN_OFF_REPORT.md`

---

## Quick Reference

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Stop
docker-compose stop

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Execute
docker-compose exec kalshi-mcp pytest tests/

# Cleanup
docker-compose down -v

# Status
docker-compose ps
```

---

**v0.4.0 MVP - Ready for production deployment** 🚀
