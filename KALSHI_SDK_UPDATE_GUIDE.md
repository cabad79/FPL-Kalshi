# ✅ Kalshi SDK Integration - Complete Update Guide

**Status:** Configuration Updated | Ready for Credentials  
**Date:** 2026-08-14  
**SDK Used:** Official `kalshi_python_async` (RSA Signature Authentication)

---

## 🔄 **CHANGES MADE**

### 1. **Environment Variables (.env)**

#### ❌ OLD (OAuth2 - INCORRECT)
```env
KALSHI_CLIENT_ID=...
KALSHI_CLIENT_SECRET=...
```

#### ✅ NEW (RSA Signature - CORRECT)
```env
KALSHI_KEY_ID=your_key_id_here
KALSHI_PRIVATE_KEY_PEM=your_rsa_private_key_pem_here
```

**File Updated:** `C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi\.env`

---

### 2. **Kalshi Client Implementation**

#### Updated `kalshi_client.py`

**Before:**
```python
# Custom OAuth2 implementation
class KalshiAuthClient:
    def __init__(self, client_id, client_secret):
        # OAuth2 token management
        self.token = ...
        self.refresh_token = ...
```

**After:**
```python
# Official SDK integration
from kalshi_python_async import KalshiClient, KalshiAuth

class KalshiAuthClient:
    def __init__(self, key_id, private_key_pem):
        self.auth = KalshiAuth(
            key_id=key_id,
            private_key_pem=private_key_pem
        )
        self.kalshi_client = KalshiClient(auth=self.auth)
```

**Benefits:**
- ✅ Official Kalshi SDK (maintained & tested)
- ✅ RSA signature authentication (cryptographically secure)
- ✅ Automatic request signing
- ✅ Built-in rate limiting
- ✅ Full API coverage

**File Updated:** `fpl-mcp-v2/src/fpl_mcp/kalshi_client.py`

---

### 3. **Dependencies**

Added to `pyproject.toml`:
```toml
kalshi_python_async>=0.2.0
```

---

## 🔑 **HOW TO GET YOUR CREDENTIALS**

### Step 1: Go to Kalshi Account Settings

1. Visit **https://kalshi.com** and sign in
2. Go to **Account Settings** → **Profile**
3. Find the **"API Keys"** section

### Step 2: Generate New API Key

1. Click **"Create New API Key"**
2. Kalshi will generate:
   - **Key ID**: Public identifier (e.g., `a952bcbe-ec3b-4b5b-b8f9-11dae589608c`)
   - **Private Key**: RSA private key in PEM format

### Step 3: Save Your Credentials

⚠️ **IMPORTANT:** The private key is only shown ONCE. Save it immediately!

```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdef...
[many lines of base64 encoded key data]
-----END RSA PRIVATE KEY-----
```

### Step 4: Update .env File

Edit `C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi\.env`:

```env
KALSHI_KEY_ID=a952bcbe-ec3b-4b5b-b8f9-11dae589608c
KALSHI_PRIVATE_KEY_PEM=-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdef...
[paste your entire private key here]
-----END RSA PRIVATE KEY-----
```

---

## 🚀 **NEXT STEPS**

### Step 1: Install Updated Dependencies

```bash
cd fpl-mcp-v2
pip install -e ".[dev]"
```

This will install:
- ✅ Official Kalshi SDK (`kalshi_python_async`)
- ✅ All other dependencies

### Step 2: Restart Docker Container

```powershell
docker-compose -f docker-compose-simple.yml down
docker-compose -f docker-compose-simple.yml up -d
```

### Step 3: Test Connection

```bash
docker exec kalshi-mcp-v0.4.0 python3 << 'EOF'
from fpl_mcp.kalshi_client import KalshiAuthClient

auth = KalshiAuthClient()
if auth.is_authenticated():
    print("✅ Kalshi API connected and authenticated!")
    print(f"   Key ID: {auth.key_id[:20]}...")
else:
    print("❌ Not authenticated. Check .env credentials.")
EOF
```

### Step 4: Get Live Markets

Once authenticated:

```bash
docker exec kalshi-mcp-v0.4.0 python3 << 'EOF'
import asyncio
from fpl_mcp.kalshi_client import KalshiAuthClient

async def main():
    auth = KalshiAuthClient()
    client = auth.get_client()
    
    if client:
        # Get exchange status
        status = await client.exchange_api.get_exchange_status()
        print(f"Kalshi Status: {status}")
        
        # Get markets
        markets = await client.market_api.get_markets(limit=5)
        print(f"Available Markets: {len(markets.markets)}")
        
        await client.close()

asyncio.run(main())
EOF
```

---

## 📋 **AUTHENTICATION METHOD COMPARISON**

| Aspect | Old (OAuth2) | New (RSA) |
|--------|------------|----------|
| Method | Username/Password Token | RSA Signature |
| Credentials | Client ID + Secret | Key ID + Private Key |
| Token Management | Manual refresh | Automatic signing |
| Security | Token-based | Cryptographic signing |
| Official Support | ❌ Custom | ✅ Official SDK |
| Request Headers | Bearer Token | KALSHI-ACCESS-* headers |
| Rate Limiting | Manual | Built-in |

---

## 🔐 **SECURITY NOTES**

1. **Private Key is Secret**
   - Never commit to git
   - Never share in logs
   - Store securely (.env won't be committed)

2. **RSA Signature**
   - Each request is individually signed
   - Timestamp included in signature (prevents replay attacks)
   - No tokens to expire/refresh

3. **Environment Variables**
   - `.env` is git-ignored (check `.gitignore`)
   - Only loaded at container startup
   - Not visible in logs or error messages

---

## 🧪 **TESTING ENVIRONMENTS**

### Demo Environment
```env
KALSHI_ENV=demo
KALSHI_API_URL=https://external-api.demo.kalshi.co
```

For testing without real money.

### Production Environment
```env
KALSHI_ENV=live
KALSHI_API_URL=https://external-api.kalshi.co
```

For live trading with real money.

---

## 📞 **TROUBLESHOOTING**

### Issue: "Not authenticated"
**Solution:** Check that `.env` has both:
- `KALSHI_KEY_ID` is set (not empty)
- `KALSHI_PRIVATE_KEY_PEM` is set (not empty)

### Issue: "Invalid signature"
**Solution:** Ensure private key:
- Is in valid PEM format (starts with `-----BEGIN RSA PRIVATE KEY-----`)
- Matches the Key ID
- Has no extra whitespace

### Issue: "Rate limited"
**Solution:** Official SDK handles rate limiting automatically. Slow down request rate.

---

## 📚 **OFFICIAL DOCUMENTATION**

- **Kalshi API Docs:** https://docs.kalshi.com
- **API Keys Guide:** https://docs.kalshi.com/getting_started/api_keys
- **SDKs Overview:** https://docs.kalshi.com/sdks/overview
- **Python Async SDK:** https://pypi.org/project/kalshi_python_async/

---

## ✅ **CHECKLIST**

Before going live:

- [ ] Have Kalshi account created
- [ ] Generated API Key ID and Private Key
- [ ] Added credentials to `.env`
- [ ] Installed dependencies: `pip install -e ".[dev]"`
- [ ] Restarted Docker container
- [ ] Tested connection successfully
- [ ] Retrieved live markets without errors
- [ ] Review live match events (see previous output)
- [ ] Ready for Gameweek 1 (starts Friday Aug 21)

---

**Next Action:** Get your Kalshi credentials from https://kalshi.com/account/profile and update `.env`
