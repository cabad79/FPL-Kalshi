# 🔍 PLAYER VALIDATOR - REAL EXAMPLES

**Status:** Ready to test  
**Date:** 2026-08-18  
**Purpose:** Demonstrate multi-source validation

---

## 📋 Test Cases

### Example 1: VALID Player - Erling Haaland at Man City

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/validate_player_multi_source \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 1,
    "web_name": "Erling Haaland",
    "team_name": "Man City"
  }'
```

**Expected Response:**
```json
{
  "is_valid": true,
  "status": "✅ Erling Haaland VALIDATED across all sources as Man City player",
  "sources": {
    "fpl_api": {
      "valid": true,
      "data": "✅ FPL API confirms: Erling Haaland (1) in Man City"
    },
    "wikipedia": {
      "valid": true,
      "data": "✅ Wikipedia confirms: Erling Haaland plays for Man City"
    },
    "transfermarkt": {
      "valid": true,
      "data": "✅ TransferMarkt data available for Erling Haaland"
    }
  },
  "validation_errors": []
}
```

**Status:** ✅ ALL SOURCES AGREE → VALID

---

### Example 2: INVALID Player - Luis Díaz at Liverpool (TRANSFERRED)

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/validate_player_multi_source \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 329,
    "web_name": "Luis Diaz",
    "team_name": "Liverpool"
  }'
```

**Expected Response:**
```json
{
  "is_valid": false,
  "status": "❌ Luis Diaz FAILED validation - sources disagree",
  "sources": {
    "fpl_api": {
      "valid": false,
      "data": "FPL API shows Luis Diaz in Everton, not Liverpool"
    },
    "wikipedia": {
      "valid": false,
      "data": "Wikipedia: No confirmation of Luis Diaz in Liverpool"
    },
    "transfermarkt": {
      "valid": false,
      "data": "TransferMarkt shows different team"
    }
  },
  "validation_errors": [
    "FPL API: FPL API shows Luis Diaz in Everton, not Liverpool",
    "Wikipedia: Wikipedia: No confirmation of Luis Diaz in Liverpool",
    "TransferMarkt: TransferMarkt shows different team"
  ]
}
```

**Status:** ❌ SOURCES DISAGREE → INVALID (Player transferred)

**Reason:** Luis Díaz moved from Liverpool to Everton. All 3 sources correctly identify him at his new club, not the old one.

---

### Example 3: VALID Squad - All Players Confirmed

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/validate_squad_multi_source \
  -H "Content-Type: application/json" \
  -d '{
    "squad": [
      {"id": 1, "web_name": "Erling Haaland", "team": "Man City"},
      {"id": 2, "web_name": "David Raya", "team": "Arsenal"},
      {"id": 3, "web_name": "William Saliba", "team": "Arsenal"},
      {"id": 4, "web_name": "Phil Foden", "team": "Man City"},
      {"id": 5, "web_name": "Bukayo Saka", "team": "Arsenal"},
      {"id": 6, "web_name": "Declan Rice", "team": "Arsenal"},
      {"id": 7, "web_name": "James Maddison", "team": "Tottenham"},
      {"id": 8, "web_name": "Moisés Caicedo", "team": "Chelsea"},
      {"id": 9, "web_name": "Bruno Fernandes", "team": "Man Utd"},
      {"id": 10, "web_name": "Son Heung-min", "team": "Tottenham"},
      {"id": 11, "web_name": "Alexander Isak", "team": "Newcastle"},
      {"id": 12, "web_name": "Dominic Solanke", "team": "Bournemouth"},
      {"id": 13, "web_name": "Ollie Watkins", "team": "Aston Villa"},
      {"id": 14, "web_name": "Jarrod Bowen", "team": "West Ham"},
      {"id": 15, "web_name": "Mohamed Salah", "team": "Liverpool"}
    ]
  }'
```

**Expected Response:**
```json
{
  "all_valid": true,
  "valid_count": 15,
  "invalid_count": 0,
  "status": "✅ SQUAD VALID - All players confirmed across all sources",
  "players": [
    {
      "player_id": 1,
      "web_name": "Erling Haaland",
      "team_name": "Man City",
      "is_valid": true,
      "status": "✅ Erling Haaland VALIDATED across all sources as Man City player",
      "errors": []
    },
    {
      "player_id": 2,
      "web_name": "David Raya",
      "team_name": "Arsenal",
      "is_valid": true,
      "status": "✅ David Raya VALIDATED across all sources as Arsenal player",
      "errors": []
    },
    ... (13 more players, all valid)
  ]
}
```

**Status:** ✅ ALL 15 PLAYERS VALID → SQUAD VALID

---

### Example 4: INVALID Squad - Mix of Valid and Invalid

**Request:**
```bash
curl -X POST http://localhost:8000/mcp/validate_squad_multi_source \
  -H "Content-Type: application/json" \
  -d '{
    "squad": [
      {"id": 1, "web_name": "Erling Haaland", "team": "Man City"},        # ✅ VALID
      {"id": 329, "web_name": "Luis Diaz", "team": "Liverpool"},         # ❌ INVALID (at Everton)
      {"id": 2, "web_name": "David Raya", "team": "Arsenal"},             # ✅ VALID
      {"id": 3, "web_name": "William Saliba", "team": "Arsenal"},         # ✅ VALID
      ... (11 more players)
    ]
  }'
```

**Expected Response:**
```json
{
  "all_valid": false,
  "valid_count": 14,
  "invalid_count": 1,
  "status": "❌ SQUAD INVALID - Contains unvalidated players",
  "players": [
    {
      "player_id": 1,
      "web_name": "Erling Haaland",
      "is_valid": true,
      "errors": []
    },
    {
      "player_id": 329,
      "web_name": "Luis Diaz",
      "is_valid": false,
      "status": "❌ Luis Diaz FAILED validation",
      "errors": [
        "FPL API: FPL shows Luis Diaz in Everton, not Liverpool",
        "Wikipedia: No confirmation of Luis Diaz in Liverpool",
        "TransferMarkt: Shows different team"
      ]
    },
    ... (13 more players)
  ]
}
```

**Status:** ❌ 1 INVALID PLAYER → SQUAD INVALID

**Action Required:** Remove or replace Luis Díaz before using squad in simulation.

---

## ⚡ Key Validation Rules

### Rule 1: ALL Sources Must Agree
```
✅ VALID:   FPL + Wikipedia + TransferMarkt = SAME TEAM
❌ INVALID: Any source = DIFFERENT TEAM
```

### Rule 2: FPL API Status Check
```
✅ VALID:   status = 'a' (available)
❌ INVALID: status = 'u' (unavailable), 'd' (doubtful), etc.
```

### Rule 3: Transferred Players Detection
```
❌ INVALID: Player moved to different club
           All sources agree on NEW club ≠ team_name input
           Example: Luis Díaz (Liverpool) → Everton
```

### Rule 4: Squad Level
```
✅ VALID SQUAD:   ALL 15 players VALID
❌ INVALID SQUAD: ANY player INVALID
```

---

## 🔧 How to Run Tests

### 1. Start MCP Server
```bash
docker-compose up -d
sleep 5
```

### 2. Test Haaland (Should Pass)
```bash
curl -X POST http://localhost:8000/mcp/validate_player_multi_source \
  -d '{"player_id": 1, "web_name": "Erling Haaland", "team_name": "Man City"}'
```

**Expected:** `"is_valid": true` ✅

### 3. Test Luis Díaz (Should Fail)
```bash
curl -X POST http://localhost:8000/mcp/validate_player_multi_source \
  -d '{"player_id": 329, "web_name": "Luis Diaz", "team_name": "Liverpool"}'
```

**Expected:** `"is_valid": false` ❌

### 4. Test Full Squad
```bash
curl -X POST http://localhost:8000/mcp/validate_squad_multi_source \
  -d '{"squad": [...]}'
```

**Expected:** `"all_valid": true/false` (depends on squad)

---

## 📊 Success Criteria

### ✅ Success Indicators
- `is_valid: true` for valid players
- `is_valid: false` for invalid/transferred players
- All 3 sources agree on team
- Squad validation works correctly
- Error messages are descriptive

### ❌ Failure Indicators
- Server returns errors
- Inconsistent validation results
- Sources disagree
- Missing validation data

---

## 🎯 Use Cases

### Use Case 1: Validate Before Squad Submission
```python
squad = [...]  # 15 players
response = validate_squad_multi_source(squad)
if response["all_valid"]:
    submit_squad(squad)  # ✅ OK
else:
    print(f"Invalid squad: {response['status']}")  # ❌ FIX FIRST
```

### Use Case 2: Detect Transferred Players
```python
# After transfer window
new_response = validate_squad_multi_source(squad)
for player in new_response["players"]:
    if not player["is_valid"]:
        print(f"Transfer detected: {player['web_name']}")
        # Update squad
```

### Use Case 3: Update Player Database
```python
# Refresh all players
for player_id in range(1, 1000):
    result = validate_player_multi_source(player_id, ...)
    if result["is_valid"]:
        update_database(player_id, result)
```

---

## 🔒 Security Verification

### What Gets Validated
- ✅ Player exists in FPL API
- ✅ Team affiliation matches across sources
- ✅ Player status is available
- ✅ No hardcoded/fictional data
- ✅ Real-time verification

### What Gets Prevented
- ❌ Using transferred players with old team
- ❌ Using unavailable/injured players
- ❌ Using hardcoded fictional data
- ❌ Using stale/outdated information
- ❌ Simulating with invalid squads

---

**READY FOR TESTING** ✅

Run the examples above to verify the Player Validator is working correctly.

