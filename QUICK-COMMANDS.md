# ⚡ FPL MCP - Quick Commands Reference

Copy & paste these commands to get running in seconds.

---

## 🚀 SETUP (Do This First)

### 1️⃣ Build Docker Image

```bash
cd fpl-mcp-v2
docker build -t fpl-mcp:latest .
```

✅ **Verify:**
```bash
docker images | grep fpl-mcp
```

---

### 2️⃣ Configure Environment

Create `.env` file:

```bash
cat > .env << 'EOF'
FPL_OIDC_CLIENT_ID=bfcbaf69-aade-4c1b-8f00-c1cb8a193030
FPL_TEAM_ID=4247143
FPL_TEAM_NAME=Your Team Name
AUTOMATION_ENABLED=true
ALERT_CHANNELS=cli
TIMEZONE=UTC
LOG_LEVEL=INFO
EOF
```

---

### 3️⃣ Start MCP Server

```bash
docker run -d \
  --name fpl-mcp-server \
  --env-file .env \
  -i -t \
  fpl-mcp:latest
```

✅ **Verify:**
```bash
docker logs fpl-mcp-server | grep "tools registered"
```

---

### 4️⃣ Start Alert System (Optional)

```bash
docker run -d \
  --name fpl-alerts-system \
  --env-file .env \
  --entrypoint python \
  fpl-mcp:latest \
  run_alert_system.py
```

✅ **Verify:**
```bash
docker logs fpl-alerts-system | grep "Alert system running"
```

---

## 🎯 COMMON COMMANDS

### Check Status

```bash
# Is MCP running?
docker ps | grep fpl-mcp-server

# Is alert system running?
docker ps | grep fpl-alerts-system

# View MCP logs
docker logs fpl-mcp-server

# View alert logs
docker logs fpl-alerts-system

# Live logs (follow mode)
docker logs -f fpl-mcp-server
```

---

### Stop/Restart

```bash
# Stop everything
docker stop fpl-mcp-server fpl-alerts-system

# Restart everything
docker restart fpl-mcp-server fpl-alerts-system

# Remove containers
docker rm fpl-mcp-server fpl-alerts-system

# Remove image
docker rmi fpl-mcp:latest
```

---

### Rebuild After Changes

```bash
# Stop old version
docker stop fpl-mcp-server

# Remove old container
docker rm fpl-mcp-server

# Rebuild image
cd fpl-mcp-v2
docker build -t fpl-mcp:latest .

# Start new version
docker run -d --name fpl-mcp-server --env-file .env -i -t fpl-mcp:latest
```

---

## 💬 USE IN CLAUDE

Once server is running, try these prompts:

### 1. Generate Squads
```
"Generate 100 contrarian squads for GW1 and show me the best one"
```

### 2. View Your Team
```
"Load my FPL team"
```

### 3. Get Transfers
```
"Suggest 2 transfers for GW2"
```

### 4. Check Alerts
```
"Show me active alerts"
```

### 5. View Schedule
```
"When is squad generation scheduled for?"
```

### 6. Analyze Fixtures
```
"What are the hardest fixtures in GW3?"
```

### 7. Find Differentials
```
"Who are the differential picks this gameweek?"
```

### 8. DGW Planning
```
"How should I approach the DGW in GW16?"
```

---

## 🔧 CONFIGURATION EXAMPLES

### Enable Email Alerts

Edit `.env`:
```bash
ALERT_CHANNELS=cli,email
SMTP_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO=your-email@gmail.com
```

Then rebuild:
```bash
docker stop fpl-mcp-server
docker rm fpl-mcp-server
docker build -t fpl-mcp:latest .
docker run -d --name fpl-mcp-server --env-file .env -i -t fpl-mcp:latest
```

---

### Enable Slack/Discord Webhooks

Edit `.env`:
```bash
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Restart:
```bash
docker restart fpl-mcp-server
```

---

## 🆘 TROUBLESHOOTING

### Server won't start

```bash
# Check logs for errors
docker logs fpl-mcp-server

# Check Docker resources
docker stats

# Try rebuilding
docker rmi fpl-mcp:latest
docker build -t fpl-mcp:latest .
```

### Authentication fails

```bash
# Reset and try again
docker logs fpl-mcp-server | grep -i auth

# If OIDC issue, try:
# 1. Check .env has correct FPL_OIDC_CLIENT_ID
# 2. Verify FPL website is accessible
curl https://fantasy.premierleague.com/
```

### Tools not showing in Claude

```bash
# Reconnect in Claude Code:
# Settings → MCP Servers → Reconnect

# Or manually restart:
docker restart fpl-mcp-server
```

### Slow squad generation

```bash
# Use fewer squads:
# "Generate 50 squads for GW1" (instead of 1000)

# Or increase CPU:
docker run -d --name fpl-mcp-server --cpus="4" \
  --env-file .env -i -t fpl-mcp:latest
```

---

## 📊 MONITORING

### Check system health

```bash
# CPU/Memory usage
docker stats fpl-mcp-server

# Last 50 log lines
docker logs --tail=50 fpl-mcp-server

# Errors only
docker logs fpl-mcp-server 2>&1 | grep -i error

# Warnings
docker logs fpl-mcp-server 2>&1 | grep -i warning
```

---

## 🔄 DAILY OPERATIONS

### Monday
```bash
# Check previous GW results
docker logs fpl-mcp-server | grep "form updated"
```

### Wednesday
```bash
# Squad generated automatically (if alert system running)
docker logs fpl-alerts-system | grep "auto_generate"
```

### Friday
```bash
# Check deadline reminder
docker logs fpl-alerts-system | grep "DEADLINE"
```

---

## 📝 USEFUL INFO

### Find FPL Team ID
```bash
# From URL: https://fantasy.premierleague.com/entry/4247143
# Team ID = 4247143

# Or programmatically:
curl -s https://fantasy.premierleague.com/api/me/ \
  | grep -o '"id":[0-9]*'
```

### Check Docker Version
```bash
docker --version
# Should be >= 20.10
```

### Free Disk Space
```bash
df -h
# Need at least 2GB free for operations
```

---

## 🎓 NEXT STEPS

1. ✅ Run the 4 setup commands above
2. 📖 Read SETUP-GUIDE.md for detailed instructions
3. 📚 Read MCP-README.md for tool documentation
4. 💬 Start using tools in Claude
5. 🤖 Enable alert system for automation

---

## 🆘 Need Help?

- **Setup issues:** See SETUP-GUIDE.md
- **Tool reference:** See MCP-README.md
- **Architecture:** See README.md
- **Logs:** `docker logs fpl-mcp-server`
- **Status:** `docker ps` / `docker stats`

---

**Ready? Start with:**
```bash
docker build -t fpl-mcp:latest . && \
docker run -d --name fpl-mcp-server --env-file .env -i -t fpl-mcp:latest
```

Then ask Claude: `"Generate 100 squads for GW1"` 🚀⚽
