# 🔍 PLAYER VALIDATOR TOOL - MULTI-SOURCE VALIDATION

**Status:** ✅ Production Ready  
**Date:** 2026-08-18  
**Purpose:** Validate all players against multiple sources before using in simulations

---

## 📋 Overview

The **Player Validator** is a critical MCP tool that validates every player across THREE independent data sources to ensure data integrity:

1. **FPL Official API** - `fantasy.premierleague.com/api/bootstrap-static/`
2. **Wikipedia** - Player profiles and career history
3. **TransferMarkt** - Transfer market data

**RULE: A player is ONLY valid if ALL THREE sources confirm the team affiliation.**

---

## 🎯 Why This Matters

### Previous Issues
```
❌ Data contamination: Players like Luis Díaz moved clubs
❌ Outdated information: Using cached data from previous season
❌ Unverified transfers: Players with unclear status
❌ Fictional data: Hard-coded player assignments
```

### Current Solution
```
✅ Every player validated in real-time
✅ Cross-source consensus required
✅ No hardcoded data accepted
✅ Automatic detection of transferred players
```

---

## 📖 Usage Examples

### Example 1: Validate Single Player

```json
{
  "tool": "validate_player_multi_source",
  "params": {
    "player_id": 1,
    "web_name": "Erling Haaland",
    "team_name": "Man City"
  }
}
```

**Response (Valid):**
```json
{
  "player_id": 1,
  "web_name": "Erling Haaland",
  "team_name": "Man City",
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

**Response (Invalid - Player Moved):**
```json
{
  "player_id": 123,
  "web_name": "Luis Díaz",
  "team_name": "Liverpool",
  "is_valid": false,
  "status": "❌ Luis Díaz FAILED validation - sources disagree",
  "sources": {
    "fpl_api": {
      "valid": false,
      "data": "FPL shows Luis Díaz in Everton, not Liverpool"
    },
    "wikipedia": {
      "valid": false,
      "data": "Wikipedia: No confirmation of Luis Díaz in Liverpool"
    },
    "transfermarkt": {
      "valid": false,
      "data": "TransferMarkt shows different team"
    }
  },
  "validation_errors": [
    "FPL API: FPL shows Luis Díaz in Everton, not Liverpool",
    "Wikipedia: Wikipedia: No confirmation of Luis Díaz in Liverpool",
    "TransferMarkt: TransferMarkt shows different team"
  ]
}
```

---

### Example 2: Validate Entire Squad

```json
{
  "tool": "validate_squad_multi_source",
  "params": {
    "squad": [
      {"id": 1, "web_name": "Haaland", "team": "Man City"},
      {"id": 2, "web_name": "Raya", "team": "Arsenal"},
      {"id": 3, "web_name": "Saliba", "team": "Arsenal"},
      {"id": 4, "web_name": "Foden", "team": "Man City"},
      {"id": 5, "web_name": "Saka", "team": "Arsenal"}
    ]
  }
}
```

**Response:**
```json
{
  "squad_size": 5,
  "all_valid": true,
  "valid_count": 5,
  "invalid_count": 0,
  "status": "✅ SQUAD VALID - All players confirmed across all sources",
  "players": [
    {
      "player_id": 1,
      "web_name": "Haaland",
      "team_name": "Man City",
      "is_valid": true,
      "status": "✅ Haaland VALIDATED across all sources as Man City player",
      "errors": []
    },
    {
      "player_id": 2,
      "web_name": "Raya",
      "team_name": "Arsenal",
      "is_valid": true,
      "status": "✅ Raya VALIDATED across all sources as Arsenal player",
      "errors": []
    }
    // ... rest of squad
  ]
}
```

---

## 🔧 Sources of Truth

### 1. FPL API (PRIMARY)
```
Endpoint: https://fantasy.premierleague.com/api/bootstrap-static/
What it validates:
  ✅ Player exists in FPL (element ID)
  ✅ Player is in correct team
  ✅ Player status is 'available' (a)
  ✅ Player price and ep_next values
  
Failure mode: Player not found or in different team
```

### 2. Wikipedia (SECONDARY)
```
Endpoint: https://en.wikipedia.org/w/api.php
What it validates:
  ✅ Player profile exists
  ✅ Current team affiliation listed
  ✅ Career history confirms move
  
Failure mode: No Wikipedia profile or team mismatch
```

### 3. TransferMarkt (TERTIARY)
```
Endpoint: https://www.transfermarkt.com
What it validates:
  ✅ Current club assignment
  ✅ Transfer history
  ✅ Contract details
  
Failure mode: Different current team or unavailable data
```

---

## 🚨 Validation Rules

### Strict Mode (Recommended for Simulations)
```
✅ PASS: All 3 sources agree on team
❌ FAIL: Any source disagrees
❌ FAIL: Any source has error/unavailable
❌ FAIL: FPL API shows status != 'available'
```

### Lenient Mode (For Research Only)
```
✅ PASS: At least 2 of 3 sources agree
⚠️ WARNING: 1 source disagrees
```

**SIMULATIONS MUST USE STRICT MODE ONLY**

---

## 📊 Validation Workflow

### For Single Player Validation
```
INPUT: player_id, web_name, team_name
  ↓
CHECK FPL API
  ↓ Player found & correct team & status='a'
  ↓
CHECK WIKIPEDIA
  ↓ Profile found & team mentioned
  ↓
CHECK TRANSFERMARKT
  ↓ Current club matches
  ↓
ALL 3 PASS? → VALID ✅
ANY FAIL? → INVALID ❌
```

### For Squad Validation
```
INPUT: squad list (15 players)
  ↓
VALIDATE EACH PLAYER (parallel)
  ↓
ALL PLAYERS VALID? → SQUAD VALID ✅
ANY PLAYER INVALID? → SQUAD INVALID ❌
  ↓
OUTPUT: List of valid/invalid players
```

---

## ⚠️ Critical Rules

### BEFORE USING IN SIMULATIONS:
1. **Always validate squad first**
   ```json
   {
     "tool": "validate_squad_multi_source",
     "params": {"squad": [...]}
   }
   ```

2. **Check response.all_valid == true**
   ```
   if response["all_valid"] == false:
     STOP - Do not proceed with simulations
   ```

3. **Review validation_errors for each invalid player**
   ```
   for player in response["players"]:
     if not player["is_valid"]:
       Log player["errors"] for analysis
   ```

4. **Only use valid players in simulations**
   ```
   valid_players = [p for p in squad if p["is_valid"]]
   simulation(valid_players)  // NOT full squad
   ```

---

## 🔄 Update Frequency

Player validation should be run:
- ✅ **Before each gameweek** - Catch any transfers
- ✅ **Before squad submission** - Final verification
- ✅ **After transfer windows** - Re-validate all players
- ✅ **On demand** - If player status changes

---

## 📈 Expected Behavior

### Successful Validation
```
Player: Erling Haaland
Team: Man City
Result: ✅ VALID

All sources confirm:
  FPL:         ✅ Player 1 in Man City, status='a'
  Wikipedia:   ✅ Current club: Manchester City
  TransferMarkt: ✅ Current club: Manchester City
```

### Failed Validation (Transferred Player)
```
Player: Luis Díaz
Team: Liverpool
Result: ❌ INVALID

Sources disagree:
  FPL:         ❌ Player 123 in Everton, not Liverpool
  Wikipedia:   ❌ No recent mention of Liverpool
  TransferMarkt: ❌ Current club: Everton
```

### Failed Validation (Incorrect Team Input)
```
Player: David Raya
Team: Chelsea (WRONG)
Result: ❌ INVALID

Sources agree on actual team:
  FPL:         ❌ Player 2 in Arsenal, not Chelsea
  Wikipedia:   ❌ Current club: Arsenal
  TransferMarkt: ❌ Current club: Arsenal
```

---

## 🛡️ Error Handling

### API Unavailable
```json
{
  "is_valid": false,
  "validation_errors": [
    "FPL API unreachable - network error"
  ]
}
```

### Player Not Found
```json
{
  "is_valid": false,
  "validation_errors": [
    "FPL API: Player ID 999999 not found in FPL API"
  ]
}
```

### Partial Source Failure
```json
{
  "is_valid": false,
  "validation_errors": [
    "Wikipedia error: timeout",
    "FPL API: OK",
    "TransferMarkt: OK"
  ]
}
```

---

## 💡 Best Practices

### ✅ DO:
1. Validate before EVERY simulation
2. Check all sources agree
3. Log validation errors
4. Re-validate after transfers
5. Use strict mode only

### ❌ DON'T:
1. Hardcode player teams
2. Use data from previous season
3. Trust single source
4. Skip validation for "known" players
5. Cache validation results > 24 hours

---

## 🔗 Integration Points

### MCP Tools:
1. `validate_player_multi_source` - Single player
2. `validate_squad_multi_source` - Full squad

### Services:
- `PlayerValidator` class in `player_validator.py`
- Supports async/await pattern
- Proper error handling and logging

### Before Simulations:
- ❌ DO NOT use `monte_carlo_*` functions directly
- ✅ Always validate squad first
- ✅ Check response before proceeding

---

## 📝 Example Integration

```python
# 1. Validate squad
validation_response = validate_squad_multi_source(
    squad=[
        {"id": 1, "web_name": "Haaland", "team": "Man City"},
        # ... 14 more players
    ]
)

# 2. Check result
if not validation_response["all_valid"]:
    print(f"Invalid squad: {validation_response['status']}")
    for player in validation_response["players"]:
        if not player["is_valid"]:
            print(f"  - {player['web_name']}: {player['errors']}")
    return None  # Don't proceed

# 3. Proceed only if all valid
print("✅ Squad validated across all sources")
# Continue with simulations...
```

---

## ✅ Status

- ✅ FPL API validation implemented
- ✅ Wikipedia validation implemented
- ✅ TransferMarkt validation implemented
- ✅ Multi-source consensus logic
- ✅ Squad-level validation
- ✅ Error handling and logging
- ✅ MCP tools registered

**Ready for production use** ⚽✅
