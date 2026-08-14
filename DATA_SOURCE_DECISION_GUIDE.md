# Data Source Decision Guide: Quick Reference
**For:** Prediction Market Integration with Kalshi  
**Date:** August 14, 2026

---

## QUICK ANSWER: Which Source Should You Use?

### Your Question → Recommended Answer

**"I need FREE football data for prediction markets right now"**
→ **USE: Fantasy Premier League (FPL) API**
- Cost: $0
- Setup: 5 minutes
- Quality: Excellent for predictions
- Legal: ✅ Allowed

**"I want real-time player ratings for predictions"**
→ **DO NOT USE: EA Sports Index** (doesn't exist)
→ **INSTEAD USE: FPL API + Understat/StatsBomb**
- FPL: Real player performance (what actually happens)
- Understat: xG models (predictive metrics)
- StatsBomb: Advanced analytics

**"I need video game player data for prediction markets"**
→ **USE: FutDB API**
- But: Game ratings ≠ real performance (poor prediction power)
- Better: Use game data for squad composition, not performance prediction
- Cost: Free tier available, $X/month premium

**"Which API has the official approval?"**
→ **FPL:** Undocumented but reverse-engineered, de facto standard
→ **EA Sports:** Only FUTBIN/FUT.GG/FUTWIZ approved (very limited)
→ **FIFA Data:** No commercial prediction use allowed

**"I want to integrate with Kalshi prediction markets"**
→ **Architecture:**
```
FPL API (Real performance) → Feature Engineering → Prediction Model → Kalshi API
       ↓
Optional: +Understat (xG) or SportMonks (advanced metrics)
```

---

## SOURCE COMPARISON MATRIX

```
┌─────────────────────┬──────────────┬────────────────┬─────────────────────┐
│ Criteria            │ FPL API      │ EA Sports Idx* │ FIFA Game Data      │
├─────────────────────┼──────────────┼────────────────┼─────────────────────┤
│ Cost                │ ✅ FREE      │ ❌ N/A         │ ⚠️ Free/Paid        │
│ Setup Time          │ ✅ 5 min     │ ❌ N/A         │ ⚠️ 15 min           │
│ Real Data?          │ ✅ YES       │ ❌ N/A         │ ❌ Game ratings     │
│ Data Freshness      │ ✅ 15-30min  │ ❌ N/A         │ ❌ Hours-days       │
│ Python Support      │ ✅ Excellent │ ❌ N/A         │ ⚠️ Good             │
│ Legal for Markets   │ ✅ YES       │ ❌ N/A         │ ⚠️ Restricted       │
│ Rate Limits         │ ✅ None      │ ❌ N/A         │ ⚠️ API-specific     │
│ Prediction Value    │ ✅ HIGH      │ ❌ N/A         │ ❌ LOW (0.4-0.5)    │
│ Community Support   │ ✅ Excellent │ ❌ N/A         │ ⚠️ Good             │
└─────────────────────┴──────────────┴────────────────┴─────────────────────┘
* EA Sports Index does not exist as a product
```

---

## BY YOUR SITUATION

### Starting a Prediction Market Business ($ Budget)
```
BUDGET: $0-50/month
├─ Week 1: FPL API only
├─ Week 2: Add Reddit sentiment scraping
├─ Week 3: Basic prediction model
├─ Week 4: Kalshi integration
└─ Month 2: Evaluate if revenue justifies paid APIs
```

**Actions:**
1. ✅ Set up FPL API client (code in WORKING_CODE_EXAMPLES.md)
2. ✅ Build feature extraction pipeline (form, injury, fixtures)
3. ✅ Implement simple prediction model (form-based)
4. ✅ Connect to Kalshi API
5. ⏭️ Track performance vs. actual market odds
6. ⏭️ Add paid APIs (Sportmonks, Understat) once revenue covers costs

### Serious Algorithmic Trading ($ Budget Available)
```
BUDGET: $200-2000/month
├─ FPL API ($0)
├─ Sportmonks ($32/month) - Advanced metrics
├─ Understat ($50/month) - xG models
├─ Cloud hosting ($50-200/month)
├─ Data pipeline ($0-100/month)
└─ Kalshi trading (variable)
```

**Actions:**
1. ✅ Integrate FPL + Sportmonks + Understat
2. ✅ Build ensemble prediction model
3. ✅ Backtest on historical Kalshi data
4. ✅ Implement real-time signal generation
5. ✅ Deploy to production (Docker/K8s)
6. ✅ Monitor performance and adapt

### Gaming Community / Squad Builders
```
BUDGET: $0-100/month
├─ FutDB API (Free tier or $X/month)
├─ FUTBIN scraping (Parse.bot)
└─ Hosting ($20-50/month)
```

**Note:** Gaming data ≠ Prediction market data
- Game ratings are for game balance, not predictions
- Use FPL if predicting real performance
- Use FutDB if analyzing game squads/prices

---

## API TECHNICAL QUICK REFERENCE

### FPL API
```
Base URL:    https://fantasy.premierleague.com/api/
Auth:        None required (public)
Rate Limit:  None published (safe to use)
Key Endpoint: /bootstrap-static/ (get all data in one call)
Python Lib:  pip install fpl
Test:        curl https://fantasy.premierleague.com/api/bootstrap-static/
Uptime:      >99% (very reliable)
Cost:        FREE
```

### FutDB API
```
Base URL:    https://api.fut-db.com/api/v1/
Auth:        API Key (free tier available)
Rate Limit:  API-specific (higher for paid)
Key Endpoint: /players (search/browse)
Python Lib:  pip install requests (use directly)
Test:        Requires API key from https://futdb.app
Uptime:      ~95% (game-update dependent)
Cost:        FREE tier + $X/month premium
```

### EA Sports FC Community API
```
Base URL:    OAuth 2.0 flow (no direct REST endpoint)
Auth:        OAuth with EA account
Rate Limit:  Not published
Access:      Only 3 approved sites (FUTBIN, FUT.GG, FUTWIZ)
Data Scope:  Ultimate Team squads only
Uptime:      Tied to EA Sports FC game
Cost:        FREE (if approved)
```

---

## LEGAL & COMPLIANCE CHECKLIST

### Using FPL API
- ✅ Can use data for predictions
- ✅ Can use data commercially
- ⚠️ Must respect Premier League brand
- ⚠️ Must include attribution (recommended)
- ❌ Cannot claim official PL partnership
- ❌ Cannot redistribute data as your own

**Before going live:**
- [ ] Review Premier League website ToS
- [ ] Document data sources
- [ ] Ensure Kalshi is CFTC-licensed (it is)
- [ ] Keep audit trail of prediction decisions
- [ ] Comply with financial disclosure laws (if applicable)

### Using Game Rating Data
- ⚠️ Cannot use for real prediction markets
- ❌ EA ToS likely prohibits prediction market use
- ⚠️ Poor correlation with actual performance (0.4-0.5)
- ✅ OK for gaming community tools
- ✅ OK for entertainment/analysis

### Using Paid APIs (Sportmonks, Understat, etc.)
- ✅ Check their ToS for commercial use
- ✅ Most allow prediction market use
- ⚠️ Usually require explicit agreement
- ✅ Higher cost but better legal standing

---

## IMPLEMENTATION ROADMAP

### Phase 1: Proof of Concept (Week 1)
```python
# Minimal code to validate concept
from fpl import FPL

async def poc():
    fpl = FPL()
    players = await fpl.get_players()
    # Your prediction logic here
    # Connect to Kalshi
```

**Time:** 4-6 hours  
**Cost:** $0  
**Output:** Working integration, performance metrics  

### Phase 2: MVP (Weeks 2-3)
```python
# Add proper feature engineering
# Implement caching
# Add error handling
# Deploy to cloud
```

**Time:** 20-30 hours  
**Cost:** $30-50 (hosting)  
**Output:** Production-ready system  

### Phase 3: Scale (Month 2+)
```python
# Add more data sources
# Improve models
# Optimize trading
# Monitor performance
```

**Time:** 40+ hours  
**Cost:** $100-200+ (depends on data)  
**Output:** Profitable trading system  

---

## DECISION TREE: WHICH API TO USE?

```
                          Need Football Data?
                                 |
                    ✓YES          |          NO
                     |            |            |
                     v            |      Not applicable
              Real Performance    |          (use gaming APIs)
              or Game Ratings?
                     |
        ┌────────────┴────────────┐
        |                         |
     REAL (✅)              GAME (⚠️ Not recommended)
        |                         |
        v                         v
    FPL API              FutDB + FUTBIN
        |                         |
    ✅ FREE              ⚠️ Limited value
    ✅ Official           ❌ Poor correlation
    ✅ Good quality       ⚠️ Legal restrictions
    ✅ Real predictions
        |
        v
  Ready for Kalshi
  
  Want more data?
        |
        v
  Add Sportmonks/
  Understat/API-Football
  (if budget allows)
```

---

## RED FLAGS: What NOT to Do

### ❌ "Let's use game ratings for predictions"
**Why not:**
- Correlation with real performance: ~0.4 (weak)
- Updated only weekly (not real-time)
- Game balance > real football realism
- Regulatory risk (ToS violation likely)
- Your model will underperform vs. FPL-based

**Instead:** Use FPL data (real performance) or Understat (xG models)

### ❌ "Let's scrape FUTBIN directly"
**Why not:**
- ToS violation risk
- IP bans possible
- Unstable (HTML changes often)
- Better alternatives exist (Parse.bot, FutDB)

**Instead:** Use Parse.bot ($) or FutDB (free tier)

### ❌ "EA Sports Index will have official data"
**Why not:**
- **It doesn't exist** (EA Sports is gaming division)
- Professional data from Opta/StatsBomb instead
- Or stick with free FPL API

**Instead:** Use FPL API (free) or professional APIs (paid)

### ❌ "We'll use all three sources together"
**Why not:**
- FPL ≠ Game ratings (different scales)
- Will introduce noise to models
- Creates maintenance burden
- Overkill for MVP

**Instead:** Start with FPL, add others later if needed

---

## COST-BENEFIT ANALYSIS

### FPL API Only
```
Cost:        $0/month
Setup:       5 minutes
Benefit:     Immediate MVP
Downside:    Limited to FPL players (all PL covered)
Uptime:      99%+
Ready now?   ✅ YES
```

### FPL + Sportmonks
```
Cost:        €29/month (~$32)
Setup:       30 minutes
Benefit:     2,200+ leagues, xG data, odds
Downside:    Cost, integration complexity
Uptime:      99.99%
Ready now?   ✅ YES
```

### FPL + Understat
```
Cost:        $50/month
Setup:       1 hour
Benefit:     Advanced xG/shot data
Downside:    Cost, slower data updates
Uptime:      98%+
Ready now?   ⏭️ Later (worth it for serious models)
```

### Professional (Opta/StatsBomb)
```
Cost:        $500-2000/month
Setup:       Days (integration)
Benefit:     Highest quality, enterprise support
Downside:    High cost, overkill for MVP
Uptime:      99.99%
Ready now?   ❌ Only after revenue growth
```

---

## MY RECOMMENDATION FOR YOUR PROJECT

**Situation:** FPL-Kalshi integration for prediction markets

**Phase 1 (This Week):**
1. ✅ Use FPL API (already integrated in project)
2. ✅ Build feature engineering (form, injury, fixtures)
3. ✅ Implement prediction model (xG-based)
4. ✅ Connect to Kalshi API
5. ✅ Deploy and monitor

**Cost:** $0 data + $20-50 hosting = $20-50/month

**Phase 2 (Month 2+):**
- If profitable: Add Sportmonks ($32/month)
- If highly profitable: Add Understat ($50/month)
- If enterprise: Switch to Opta/StatsBomb

**NOT RECOMMENDED:**
- ❌ EA Sports Index (doesn't exist)
- ❌ Game rating data for real predictions
- ❌ Direct Futbin scraping

---

## NEXT STEPS

1. **Read:** PREMIUM_DATA_SOURCES_RESEARCH.md (comprehensive details)
2. **Code:** WORKING_CODE_EXAMPLES.md (copy-paste ready examples)
3. **Decide:** Use this guide to pick which sources
4. **Build:** Implement chosen APIs
5. **Deploy:** Connect to Kalshi
6. **Monitor:** Track performance vs. market

---

## CONTACT & SUPPORT

**FPL API Issues:**
- GitHub: https://github.com/amosbastian/fpl
- Docs: https://fpl.readthedocs.io/
- Reddit: r/FantasyPL

**Kalshi Integration:**
- Docs: https://docs.kalshi.com/welcome
- Support: support@kalshi.com

**Data Quality Questions:**
- FPL: Official site /r/FantasyPL
- Sportmonks: https://www.sportmonks.com/football-api/
- Understat: https://understat.com/

---

**End of Decision Guide**  
*Use this as your decision framework*  
*See other docs for detailed technical info*
