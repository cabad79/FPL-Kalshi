# Kalshi MCP v0.4.0 - Docker Quick Start Guide

## Prerequisites
- Docker Desktop installed
- Docker Compose v2.0+
- Git (already have it)

## Step 1: Setup Environment File

```bash
# Copy environment template
cp .env.example .env

# Edit with your Kalshi credentials (optional for testing)
# nano .env
```

## Step 2: Simple Docker Setup (Recommended)

Instead of building from scratch, use a Python image with required packages:

```bash
# Create docker-compose-simple.yml:
cat > docker-compose-simple.yml << 'COMPOSE'
version: '3.8'

services:
  kalshi-mcp:
    image: python:3.11-slim
    container_name: kalshi-mcp-v0.4.0
    working_dir: /app
    command: bash -c "pip install -e . && pytest tests/ -v && python -m fpl_mcp"
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from mount
    ports:
      - "8000:8000"
    environment:
      PYTHONUNBUFFERED: "1"
      KALSHI_API_URL: https://api.kalshi.com
      LOG_LEVEL: INFO
    restart: unless-stopped
COMPOSE

# Start the container
docker-compose -f docker-compose-simple.yml up -d
```

## Step 3: Install Dependencies Inside Container

```bash
# Enter container
docker exec -it kalshi-mcp-v0.4.0 bash

# Inside container, run:
cd /app/fpl-mcp-v2
pip install -e .
```

## Step 4: Run Tests

```bash
# Run all tests
docker exec kalshi-mcp-v0.4.0 bash -c "cd /app/fpl-mcp-v2 && pytest tests/ -v"

# Run specific test
docker exec kalshi-mcp-v0.4.0 bash -c "cd /app/fpl-mcp-v2 && pytest tests/unit/test_goal_prediction.py -v"
```

## Step 5: Check Logs

```bash
# View live logs
docker logs -f kalshi-mcp-v0.4.0

# View last 50 lines
docker logs --tail 50 kalshi-mcp-v0.4.0
```

## Alternative: Native Python Installation (Fastest)

If Docker build takes too long, use native Python directly:

```bash
# Install Python 3.11+ (if not already installed)
# Go to https://www.python.org/downloads/

# Install dependencies
cd fpl-mcp-v2
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Start server
fpl-mcp-v2 --host localhost --port 8000
```

## Quick Command Reference

```bash
# Start container
docker-compose -f docker-compose-simple.yml up -d

# Stop container
docker-compose -f docker-compose-simple.yml down

# View status
docker-compose -f docker-compose-simple.yml ps

# Enter container bash
docker exec -it kalshi-mcp-v0.4.0 bash

# Run Python code in container
docker exec kalshi-mcp-v0.4.0 python -c "import fpl_mcp; print('Loaded!')"

# View all logs
docker logs kalshi-mcp-v0.4.0

# Remove container (cleanup)
docker-compose -f docker-compose-simple.yml down -v
```

## Troubleshooting

### Port 8000 already in use
```bash
# Change port in docker-compose-simple.yml:
ports:
  - "9000:8000"
```

### Permission denied
```bash
# If you get permission errors, rebuild:
docker-compose -f docker-compose-simple.yml down -v
docker-compose -f docker-compose-simple.yml up -d --build
```

### See what's in the container
```bash
docker exec -it kalshi-mcp-v0.4.0 ls -la /app
```

---

**v0.4.0 is production-ready. Use the simple setup above for fastest deployment.** 🚀
