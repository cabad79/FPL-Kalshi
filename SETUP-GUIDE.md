# 🚀 FPL MCP - Setup & Configuration Guide

Complete step-by-step guide to configure and run the Fantasy Premier League MCP server.

---

## ⚡ Quick Start (5 minutes)

### Option 1: Docker (Recommended)

```bash
cd fpl-mcp-v2

# 1. Build image
docker build -t fpl-mcp:latest .

# 2. Verify build
docker images | grep fpl-mcp

# 3. Run MCP server
docker run -d \
  --name fpl-mcp-server \
  -e FPL_TEAM_ID=4247143 \
  -i -t \
  fpl-mcp:latest

# 4. Test connection
docker logs fpl-mcp-server
```

### Option 2: Local Python

```bash
cd fpl-mcp-v2

# 1. Create virtual environment
python -m venv .venv

# 2. Activate
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Install
pip install -e .
pip install apscheduler

# 4. Run
python -m fpl_mcp
```

---

## 📋 Detailed Setup Instructions

### Step 1: Repository Setup

```bash
# Clone/enter repository
cd fpl-mcp-v2

# Verify structure
ls -la
# Should show:
# - src/fpl_mcp/
# - pyproject.toml
# - Dockerfile
# - MCP-README.md
# - run_alert_system.py
```

---

### Step 2: Environment Configuration

Create `.env` file in `fpl-mcp-v2/` directory:

```bash
# Create file
touch .env

# Add configuration (copy below)
```

**Content of `.env`:**

```env
# ============================================================================
# FPL API Configuration
# ============================================================================
FPL_OIDC_CLIENT_ID=bfcbaf69-aade-4c1b-8f00-c1cb8a193030

# ============================================================================
# Team Configuration
# ============================================================================
FPL_TEAM_ID=4247143
FPL_TEAM_NAME=Your Team Name

# ============================================================================
# Automation Settings
# ============================================================================
AUTOMATION_ENABLED=true
ALERT_CHANNELS=cli,email,file

# ============================================================================
# Email Notifications (Optional)
# ============================================================================
SMTP_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO=your-email@gmail.com

# ============================================================================
# Webhook Integration (Slack/Discord - Optional)
# ============================================================================
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# ============================================================================
# Scheduling
# ============================================================================
TIMEZONE=UTC
GENERATION_HOUR=10
GENERATION_MINUTE=0
DEADLINE_REMINDER_MINUTES=10

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO
LOG_FILE=/app/logs/fpl_mcp.log
```

**Find your FPL Team ID:**

```bash
# Option 1: From FPL website
# Go to: https://fantasy.premierleague.com/entry/{YOUR_TEAM_ID}
# Copy the number from URL

# Option 2: Use FPL API
curl -s "https://fantasy.premierleague.com/api/me/" | grep -o '"id":[0-9]*'
```

---

### Step 3: Authentication Setup

#### Option A: Docker (Automatic)

```bash
# Docker handles authentication automatically via:
# - OS keyring for credential storage
# - OIDC token refresh every 30 minutes
# - No manual intervention needed

# Just run the container and start using
```

#### Option B: Local Python

```bash
# 1. Install keyring
pip install keyring

# 2. Store credentials
python -c "
import keyring
keyring.set_password('fpl-mcp', 'email', 'your-email@gmail.com')
keyring.set_password('fpl-mcp', 'password', 'your-password')
"

# 3. Verify
python -c "
import keyring
print('Email:', keyring.get_password('fpl-mcp', 'email'))
print('Password stored:', bool(keyring.get_password('fpl-mcp', 'password')))
"
```

**Security:** Never share credentials in chat or code. Always use OS keyring.

---

### Step 4: Installation

#### Docker Installation

```bash
# 1. Build
docker build -t fpl-mcp:latest .

# Check build size
docker images fpl-mcp
# Expected: ~500MB

# 2. Verify all dependencies
docker run --rm fpl-mcp:latest python -c "
import fpl_mcp
import apscheduler
import numpy
print('✓ All dependencies loaded')
"

# 3. Test imports
docker run --rm fpl-mcp:latest python -c "
from fpl_mcp.services.squad_generator import SquadGenerator
from fpl_mcp.services.monte_carlo_simulator import MonteCarloSimulator
from fpl_mcp.services.alert_system import SeasonAlertScheduler
print('✓ All services imported')
"
```

#### Local Python Installation

```bash
# 1. Install dependencies
pip install -e .
pip install apscheduler>=3.11.0 numpy>=1.24.0

# 2. Verify installation
python -c "
from fpl_mcp.server import FPLMCPServer
print('✓ MCP Server loaded')
"

# 3. Run tests
pytest tests/ -v
```

---

### Step 5: Run MCP Server

#### Docker

```bash
# 1. Start MCP server
docker run -d \
  --name fpl-mcp-server \
  --env-file .env \
  -i -t \
  fpl-mcp:latest

# 2. Verify running
docker ps | grep fpl-mcp-server

# 3. Check logs
docker logs fpl-mcp-server

# Expected output:
# INFO:fpl_mcp.server:🚀 FPL MCP Server starting...
# INFO:fpl_mcp.server:✓ Authentication successful
# INFO:fpl_mcp.server:✓ Loaded 600+ players
# INFO:fpl_mcp.server:✓ 36 tools registered
```

#### Local Python

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# 2. Run server
python -m fpl_mcp

# Expected output:
# 🚀 FPL MCP Server starting...
# ✓ Authentication successful
# ✓ Loaded 600+ players
# ✓ 36 tools registered
```

---

### Step 6: Run Alert System (Optional but Recommended)

```bash
# Docker
docker run -d \
  --name fpl-alerts-system \
  --env-file .env \
  --entrypoint python \
  fpl-mcp:latest \
  run_alert_system.py

# Verify
docker logs fpl-alerts-system

# Expected output:
# 🚀 FPL Alert System Starting...
# 📅 Pre-season tasks scheduled: 7
# ✅ Alert system running
```

---

### Step 7: Connect to Claude

#### In Claude Code

Add to `.claude/launch.json`:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "FPL MCP Server",
      "runtimeExecutable": "docker",
      "runtimeArgs": ["run", "--rm", "-i", "fpl-mcp:latest"],
      "port": null
    }
  ]
}
```

#### In Claude.ai (via MCP Server Config)

Add to Claude settings:

```json
{
  "mcpServers": {
    "fpl-mcp": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "fpl-mcp:latest"]
    }
  }
}
```

---

## 🔧 Configuration Options

### Basic Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `FPL_TEAM_ID` | 4247143 | Your FPL team ID |
| `TIMEZONE` | UTC | Event scheduling timezone |
| `LOG_LEVEL` | INFO | Logging verbosity |

### Advanced Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `AUTOMATION_ENABLED` | true | Enable weekly squad generation |
| `ALERT_CHANNELS` | cli,email | Where to send alerts |
| `SMTP_ENABLED` | true | Enable email notifications |
| `WEBHOOK_ENABLED` | true | Enable Slack/Discord webhooks |

### Alert Channels

**CLI (Default)**
```bash
# Alerts printed to terminal
# Useful for: Local testing, monitoring
```

**Email**
```bash
# Requires Gmail app password
SMTP_ENABLED=true
SMTP_FROM=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # 16-char app password
```

**Webhook (Slack/Discord)**
```bash
# Get webhook from Slack/Discord
# Settings → Apps & integrations → Incoming Webhooks
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

---

## ✅ Verification Checklist

```bash
# After setup, verify each step

□ Docker image built
  docker images | grep fpl-mcp

□ MCP server running
  docker ps | grep fpl-mcp-server

□ MCP server logs clean
  docker logs fpl-mcp-server | grep -i error

□ Authentication successful
  docker logs fpl-mcp-server | grep "✓ Authentication"

□ Players loaded
  docker logs fpl-mcp-server | grep "600+ players"

□ Tools registered
  docker logs fpl-mcp-server | grep "36 tools"

□ Alert system running (if enabled)
  docker logs fpl-alerts-system | grep "Alert system running"

□ Can connect to Claude
  Ask Claude: "List available FPL tools"
```

---

## 🚀 First Commands

Once setup complete, try these in Claude:

### 1. Generate Initial Squad
```
"Generate 100 contrarian squads for GW1 and show me the best one"
```

### 2. View Current Team
```
"Load my current FPL team"
```

### 3. Get Transfer Suggestions
```
"Suggest 2 transfers for GW2"
```

### 4. Check Alert Status
```
"Are there any active alerts?"
```

### 5. View Schedule
```
"What's the squad generation schedule for the season?"
```

---

## 🔍 Troubleshooting

### Issue: Docker build fails

```bash
# Solution 1: Check Docker version
docker --version
# Should be >=20.10

# Solution 2: Clean rebuild
docker system prune -a
docker build -t fpl-mcp:latest . --no-cache

# Solution 3: Check available disk space
df -h
# Need at least 2GB free
```

### Issue: Authentication fails

```bash
# Solution 1: Verify credentials
docker run --rm fpl-mcp:latest python -c "
import keyring
print(keyring.get_password('fpl-mcp', 'email'))
"

# Solution 2: Reset credentials
python -c "
import keyring
keyring.delete_password('fpl-mcp', 'email')
keyring.delete_password('fpl-mcp', 'password')
"
# Then re-run setup step 3

# Solution 3: Use alternative auth
# Contact FPL support if OIDC not working
```

### Issue: MCP tools not available in Claude

```bash
# Solution 1: Verify server is running
docker ps | grep fpl-mcp-server

# Solution 2: Check logs
docker logs fpl-mcp-server | tail -20

# Solution 3: Restart server
docker restart fpl-mcp-server

# Solution 4: Reconnect Claude
# In Claude Code: /config → Reconnect MCP Server
```

### Issue: Squad generation is slow

```bash
# Solution 1: Reduce squad count
# In Claude: "Generate 50 squads for GW1"
# (instead of 1000)

# Solution 2: Increase Docker CPU
docker run -d \
  --cpus="4" \
  --name fpl-mcp-server \
  fpl-mcp:latest

# Solution 3: Reduce Monte Carlo iterations
# Expected times:
# - 100 squads, 100 iterations: 30s
# - 500 squads, 100 iterations: 150s
# - 1000 squads, 100 iterations: 300s
```

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2GB | 4GB |
| Disk | 2GB | 5GB |
| Docker | 20.10+ | Latest |
| Python | 3.11+ | 3.12+ |

---

## 🔐 Security Best Practices

1. **Never share credentials**
   ```
   ✗ Don't: paste passwords in chat
   ✓ Do: use OS keyring or .env with .gitignore
   ```

2. **Secure .env file**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo ".env.local" >> .gitignore
   
   # Restrict permissions
   chmod 600 .env
   ```

3. **Rotate tokens**
   ```bash
   # MCP automatically rotates OIDC tokens every 30 minutes
   # No manual action needed
   ```

4. **Secure Docker images**
   ```bash
   # Use non-root user (built-in)
   # No hardcoded secrets
   # Minimal base image (python:3.11-slim)
   ```

---

## 📖 Next Steps

1. ✅ **Complete this setup guide**

2. 📚 **Read MCP-README.md**
   ```bash
   cat MCP-README.md
   ```

3. 🎯 **Start with examples**
   - Generate GW1 squad
   - View current team
   - Get transfer suggestions

4. 🤖 **Enable automation**
   - Run alert system
   - Set up email/webhook alerts
   - Weekly squad generation runs automatically

5. 📊 **Monitor performance**
   ```bash
   # View logs
   docker logs -f fpl-mcp-server
   docker logs -f fpl-alerts-system
   ```

---

## 💡 Useful Commands

### Docker Management

```bash
# View all containers
docker ps -a

# View images
docker images

# View logs (live)
docker logs -f fpl-mcp-server

# Stop server
docker stop fpl-mcp-server

# Restart server
docker restart fpl-mcp-server

# Remove container
docker rm fpl-mcp-server

# Remove image
docker rmi fpl-mcp:latest
```

### Testing

```bash
# Test squad generation
docker run --rm fpl-mcp:latest python -c "
from fpl_mcp.services.squad_generator import SquadGenerator
print('✓ SquadGenerator works')
"

# Test Monte Carlo
docker run --rm fpl-mcp:latest python -c "
from fpl_mcp.services.monte_carlo_simulator import MonteCarloSimulator
print('✓ MonteCarloSimulator works')
"

# Test API connection
docker run --rm fpl-mcp:latest python -c "
import httpx
resp = httpx.get('https://fantasy.premierleague.com/api/bootstrap-static/')
print(f'✓ API response: {resp.status_code}')
"
```

---

## 🎓 Learning Path

1. **Basics** (15 min)
   - Follow "Quick Start" section
   - Run MCP server
   - Generate one squad

2. **Intermediate** (1 hour)
   - Read MCP-README.md
   - Try 5 different tools
   - Configure alerts

3. **Advanced** (2 hours)
   - Understand Monte Carlo simulation
   - Configure email/webhook alerts
   - Set up weekly automation

4. **Expert** (ongoing)
   - Optimize performance
   - Customize squad strategies
   - Integrate with external systems

---

## 📞 Support

### Documentation
- **MCP-README.md** - Complete tool reference
- **README.md** - Architecture overview
- **SETUP-GUIDE.md** - This file

### Debugging
```bash
# Collect debug info
docker logs fpl-mcp-server > debug.log
docker inspect fpl-mcp-server >> debug.log
docker stats --no-stream >> debug.log

# Check environment
docker exec fpl-mcp-server env | grep FPL_
```

### Common Issues
- Authentication failed → Step 3
- Tools not available → Step 7
- Slow performance → Troubleshooting section
- Configuration → Step 2

---

## ✨ Success Indicators

After completing this setup, you should see:

✅ Docker image built successfully
✅ MCP server running with 36 tools
✅ Authentication to FPL working
✅ Can generate squads in Claude
✅ Alert system monitoring (if enabled)

**Once complete, you're ready to start optimizing your FPL squad!** 🚀⚽

---

**Next: Read MCP-README.md for complete tool documentation**
