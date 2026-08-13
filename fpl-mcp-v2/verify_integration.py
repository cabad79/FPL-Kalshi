#!/usr/bin/env python3
"""Integration verification script for FPL MCP v2."""

import sys
sys.path.insert(0, "src")

errors = []

# Test 1: Domain models
print("[1/6] Testing domain models...")
try:
    from fpl_mcp.domain import Player, Team, Fixture, Gameweek, BootstrapStatic
    p = Player(id=1, first_name="Test", second_name="Player", web_name="Test",
               team_id=1, element_type=3, now_cost=100, total_points=50,
               points_per_game=5.0, minutes=900, goals_scored=5, assists=3,
               clean_sheets=2, goals_conceded=10, own_goals=0, penalties_saved=0,
               penalties_missed=0, yellow_cards=1, red_cards=0, saves=0, bonus=5,
               bps=100, influence=200.0, creativity=150.0, threat=180.0,
               ict_index=53.0, form="5.0", value_form="0.5", value_season="5.0",
               cost_change_start=0, cost_change_event=0, selected_by_percent="10.0",
               transfers_in=1000, transfers_out=500, transfers_in_event=100,
               transfers_out_event=50, event_points=5, status="a")
    assert p.full_name == "Test Player"
    assert p.price_millions == 10.0
    print("  ✓ Domain models OK")
except Exception as e:
    errors.append(f"Domain: {e}")
    print(f"  ✗ Domain models FAILED: {e}")

# Test 2: Config
print("[2/6] Testing config...")
try:
    from fpl_mcp.config import FPLConfig
    import os
    os.environ["FPL_OIDC_CLIENT_ID"] = "test-client-id"
    cfg = FPLConfig()
    assert cfg.api_base_url == "https://fantasy.premierleague.com/api"
    assert cfg.resolved_token_url == "https://account.premierleague.com/as/token"
    print("  ✓ Config OK")
except Exception as e:
    errors.append(f"Config: {e}")
    print(f"  ✗ Config FAILED: {e}")

# Test 3: Utilities
print("[3/6] Testing utilities...")
try:
    from fpl_mcp.utils.difficulty import fixture_score, assess_fixtures
    from fpl_mcp.utils.position_utils import normalize_position
    from fpl_mcp.utils.params import unwrap
    from fpl_mcp.utils.nicknames import NICKNAMES
    
    assert fixture_score([{"difficulty": 3}, {"difficulty": 3}]) == 6.0
    assert assess_fixtures(8.5) == "Excellent fixtures"
    assert normalize_position("goalkeeper") == "GKP"
    assert normalize_position("mid") == "MID"
    assert unwrap("value", "key") == "value"
    assert unwrap({"key": "value"}, "key") == "value"
    print("  ✓ Utilities OK")
except Exception as e:
    errors.append(f"Utilities: {e}")
    print(f"  ✗ Utilities FAILED: {e}")

# Test 4: Infrastructure
print("[4/6] Testing infrastructure...")
try:
    from fpl_mcp.infrastructure.rate_limiter import RateLimiter
    from fpl_mcp.infrastructure.cache import TieredCache, CacheTier
    from fpl_mcp.infrastructure.credentials import SecureCredentialManager
    
    rl = RateLimiter(max_requests=10, per_seconds=60)
    assert rl.stats["max_requests"] == 10
    cache = TieredCache()
    print("  ✓ Infrastructure OK")
except Exception as e:
    errors.append(f"Infrastructure: {e}")
    print(f"  ✗ Infrastructure FAILED: {e}")

# Test 5: Repositories
print("[5/6] Testing repositories...")
try:
    from fpl_mcp.repositories import BootstrapRepository, PlayerRepository, FixtureRepository
    print("  ✓ Repositories import OK")
except Exception as e:
    errors.append(f"Repositories: {e}")
    print(f"  ✗ Repositories FAILED: {e}")

# Test 6: Services
print("[6/6] Testing services...")
try:
    from fpl_mcp.services import PlayerService, FixtureService, CaptainService, LeagueService
    print("  ✓ Services import OK")
except Exception as e:
    errors.append(f"Services: {e}")
    print(f"  ✗ Services FAILED: {e}")

# Test 7: MCP layer (may fail if mcp version is incompatible)
print("[7/7] Testing MCP layer...")
try:
    from fpl_mcp.presentation.resources import register_resources
    from fpl_mcp.presentation.tools import register_tools
    from fpl_mcp.presentation.prompts import register_prompts
    from fpl_mcp.server import FPLMCPServer, ServiceContainer
    print("  ✓ MCP layer OK")
except Exception as e:
    errors.append(f"MCP layer: {e}")
    print(f"  ✗ MCP layer FAILED: {e}")

# Summary
print("\n" + "=" * 50)
if errors:
    print(f"INTEGRATION CHECK: {len(errors)} error(s)")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("INTEGRATION CHECK PASSED: All layers importable")
    sys.exit(0)
