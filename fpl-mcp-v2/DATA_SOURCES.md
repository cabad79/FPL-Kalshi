# FPL MCP Data Sources & Analysis Framework

## 1. FPL Official API Endpoints

### Bootstrap Static Data (`/bootstrap-static/`)
**Primary source for:** Game settings, players, teams, gameweeks, element types
- **Players (600+):** id, name, position, price, form, expected points (ep_next), ICT Index, transfers in/out
- **Teams (20):** name, short_name, strength, fixtures
- **Gameweeks (38):** dates, deadlines, status
- **Rules:** £100m budget, 2 GKP/5 DEF/5 MID/3 FWD, max 3 per club

### Fixtures (`/fixtures/`)
**Primary source for:** Match difficulty, difficulty rating (1-5), dates
- Team fixture difficulty (1=easiest, 5=hardest)
- Used for fixture swing analysis in MC simulations
- Applied as multiplier: 1.0/0.95/0.85/0.75/0.65 based on difficulty

### Live Event (`/event/{gameweek}/live/`)
**Primary source for:** Real-time points, bonus allocation, automatic changes
- Player scores updated live during matches
- Bonus point allocation (0-3 per player)
- Used to validate/calibrate form estimates

### Entry/Team (`/entry/{team_id}/`)
**Primary source for:** Manager profile, current squad, transfers, chips
- Squad picks, captain selection, bench boost active
- Bank (available £m), transfers used/available
- Wildcard/Free Hit/Triple Captain/Bench Boost status

### Player Detailed History (`/element-summary/{player_id}/`)
**Primary source for:** Per-gameweek performance, consistency
- Point history by gameweek
- Ownership %, selected by %
- Assists, clean sheets, goals per GW

## 2. Current Implementation

### Data Validated & Working
- ✓ Player price in £m (converted from API units: /10)
- ✓ Form (string: "5.5", "0.8")
- ✓ Expected Points (ep_next: string "4.2", "0.5")
- ✓ Fixture difficulty (1-5 scale)
- ✓ Squad constraints (budget, positions, club limits)
- ✓ Team current picks & captain
- ✓ Transfer history with cost tracking

### Monte Carlo Simulation Factors
```
score_per_player = ep_next * fixture_difficulty_bonus 
                 + form_variance (gaussian 0.3 std)
                 + playing_time_risk (2% chance benched if <100%)
                 
captain_multiplier = 2x (applies only to captain)
```

## 3. Additional Data Sources Available (Not Yet Integrated)

### External Statistical Platforms

#### **Understat (xG/xA Data)**
- **URL:** https://understat.com/
- **Data:** Expected Goals (xG), Expected Assists (xA), shot data
- **FPL Application:** Identify undervalued high-xG/xA midfielders & forwards
- **Update Frequency:** Daily
- **Format:** Web scrape or API (enterprise)

#### **SofaScore (Advanced Metrics)**
- **URL:** https://www.sofascore.com/
- **Data:** Player ratings, possession, distance covered, defensive actions
- **FPL Application:** Form validation, injury risk assessment
- **Update Frequency:** Real-time
- **Format:** Public API

#### **FBref / StatsBomb (Detailed Event Data)**
- **URL:** https://fbref.com/
- **Data:** Progressive passes, tackles, pressures, shooting accuracy
- **FPL Application:** Defensive midfielder efficiency, budget defender ROI
- **Update Frequency:** Weekly
- **Format:** Web scrape (statsbomb requires API key)

#### **Reddit r/FantasyPL**
- **URL:** https://reddit.com/r/FantasyPL/
- **Data:** Community injury news, team news aggregation
- **FPL Application:** Injury alerts 24-48h before deadlines
- **Update Frequency:** Real-time
- **Format:** API (PRAW library)

#### **FPL Scout / FPL Community Consensus**
- **URL:** https://www.fplscout.com/
- **Data:** Transfer rankings, captain polls, ownership trends
- **FPL Application:** Contrarian picks, differential edge assessment
- **Update Frequency:** Weekly before deadlines
- **Format:** Web scrape

### Team News / Injury Data

#### **Official Club Sources**
- Team news from club websites & Twitter
- Expected return dates
- Rotation risk (e.g., cup fixtures)

#### **Aggregators**
- **Transfermarkt:** Injury reports, player valuation
- **Sky Sports:** Live team sheets 1h before match
- **ESPN:** Confirmed lineups

## 4. Current Analysis Pipeline

```
┌─────────────────────────────────────────┐
│  FPL Official API                       │
│  - Players (price, form, ep_next)       │
│  - Fixtures (difficulty by GW)          │
│  - Live scores (actual points)          │
│  - Team/Entry (current picks, bank)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Squad Generator (Constraint Satisfaction)
│  - 3 strategies: premium/balanced/budget │
│  - Position limits, club limits          │
│  - Budget constraint (£100m)             │
│  - Generate 1000 valid squads            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Monte Carlo Simulator (100-1000 iter)  │
│  - Per-player score = ep_next            │
│  - Fixture difficulty multiplier         │
│  - Form variance (gaussian)              │
│  - Playing time risk (2% bench chance)   │
│  - Captain 2x multiplier                 │
│  - Returns: avg, p10, p90 points         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Squad Ranking & Selection               │
│  - Top 3 squads by expected GW points    │
│  - Captain recommendation                │
│  - Transfer analysis vs current team     │
│  - Wildcard decision logic               │
└─────────────────────────────────────────┘
```

## 5. Proposed Enhancements

### Phase 1: xG/xA Integration
```python
# Use Understat xG to refine shot-heavy players
player_score = (ep_next * 0.6) + (form * 0.3) + (xg_metric * 0.1)
```

### Phase 2: Injury Risk Model
```python
# Aggregate official news + community consensus
injury_probability = (official_status * 0.7) + (reddit_alerts * 0.3)
playing_time_risk *= (1 - injury_probability)
```

### Phase 3: Ownership Contrarian Adjustment
```python
# Fade high-ownership picks in differentials
captain_score *= (1 - ownership_pct/100)  # If contrarian mode enabled
```

### Phase 4: Advanced Fixture Weighting
```python
# Consider double gameweeks (DGW) and blank gameweeks (BGW)
fixture_bonus = 1.0  # Normal
fixture_bonus = 1.5  # Double gameweek
fixture_bonus = 0.0  # Blank gameweek (player unavailable)
```

## 6. Data Validation & Quality

### Real-time Checks
- Player status "a" (available) before squad inclusion
- Chance of playing ≥50% for XI inclusion
- Budget constraint validated pre-submission
- Club limit (max 3) enforced

### Form Confidence
- Form score based on last 5 gameweeks
- ep_next validated against historical performance
- Outliers flagged (e.g., player with 0.1 ep_next despite 7 form)

## 7. Next Steps for Full Integration

1. **Add Understat scraper** → xG/xA by player, per gameweek
2. **Reddit PRAW integration** → r/FantasyPL injury threads 48h before deadline
3. **Advanced fixture weighting** → DGW/BGW detection from FPL API
4. **Ownership adjustment** → API integration with fplscout.com
5. **Real-time alerts** → CLI flag for critical injury news + stat anomalies

## 8. MCP Tools Available

**Implemented:**
- `get_player` - Search players, historical stats
- `validate_squad` - Check 15-player squad vs FPL rules
- `generate_optimal_squads` - Create 100-1000 diverse squads
- `simulate_squad_performance` - Run MC simulation (100-1000 iterations)
- `rank_squads_by_simulation` - Compare and rank multiple squads
- `suggest_captain` - Recommend captain by form/fixtures/ep_next
- `get_fixture_detail` - Match difficulty, kickoff time
- `get_gameweek_live_status` - Real-time points & bonus

**Coming:**
- `get_current_team` - Load active squad & transfer history
- `suggest_transfers` - Optimal changes within 1-3 transfers
- `suggest_wildcard_squad` - Complete rebuild recommendation
- `get_available_chips` - Wildcard/Free Hit/3xC/Bench Boost status
- `transfer_impact_analysis` - Cost & point projection for proposed changes
