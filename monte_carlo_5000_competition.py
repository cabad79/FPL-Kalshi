#!/usr/bin/env python3
"""Monte Carlo Competition: 5000 teams with 70+ points filtering."""

import asyncio
import httpx
import numpy as np
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def fetch_fpl_data():
    """Fetch real data from FPL API."""
    logger.info("📥 Fetching REAL FPL data from official API...")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get('https://fantasy.premierleague.com/api/bootstrap-static/')
            if response.status_code == 200:
                logger.info("✅ Data fetched successfully")
                return response.json()
            else:
                logger.error(f"❌ FPL API returned status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error fetching FPL data: {e}")
            return None


class RealFPLPlayer:
    """Player representation using real FPL data."""

    def __init__(self, data: Dict[str, Any], team_map: Dict[int, str]):
        self.id = data.get('id')
        self.web_name = data.get('web_name', 'Unknown')
        self.element_type = data.get('element_type', 1)  # 1=GKP, 2=DEF, 3=MID, 4=FWD
        self.team_id = data.get('team', 1)
        self.team_name = team_map.get(self.team_id, 'Unknown')
        self.now_cost = data.get('now_cost', 50) / 10  # Convert to millions
        self.selected_by_percent = float(data.get('selected_by_percent', 0))
        self.form = float(data.get('form', 0))
        self.ep_next = float(data.get('ep_next', 3.5))
        self.chance_of_playing_next_round = data.get('chance_of_playing_next_round', 100)
        self.status = data.get('status', 'a')


def is_valid_squad(squad: List[RealFPLPlayer]) -> bool:
    """Validate squad against FPL rules."""
    if len(squad) != 15:
        return False

    total_cost = sum(p.now_cost for p in squad)
    if total_cost > 100.0:
        return False

    gkp = sum(1 for p in squad if p.element_type == 1)
    def_count = sum(1 for p in squad if p.element_type == 2)
    mid_count = sum(1 for p in squad if p.element_type == 3)
    fwd_count = sum(1 for p in squad if p.element_type == 4)

    if gkp != 2 or def_count != 5 or mid_count != 5 or fwd_count != 3:
        return False

    team_counts = defaultdict(int)
    for p in squad:
        team_counts[p.team_id] += 1
        if team_counts[p.team_id] > 3:
            return False

    if not all(p.status == 'a' for p in squad):
        return False

    return True


def generate_valid_squad(players: List[RealFPLPlayer], attempt: int = 0) -> List[RealFPLPlayer] | None:
    """Generate a valid squad from real FPL data."""
    if attempt > 100:
        return None

    try:
        available_players = [p for p in players if p.status == 'a']

        gkp_list = [p for p in available_players if p.element_type == 1]
        def_list = [p for p in available_players if p.element_type == 2]
        mid_list = [p for p in available_players if p.element_type == 3]
        fwd_list = [p for p in available_players if p.element_type == 4]

        if not all([gkp_list, def_list, mid_list, fwd_list]):
            return None

        squad = (
            list(np.random.choice(gkp_list, 2, replace=False)) +
            list(np.random.choice(def_list, 5, replace=False)) +
            list(np.random.choice(mid_list, 5, replace=False)) +
            list(np.random.choice(fwd_list, 3, replace=False))
        )

        if is_valid_squad(squad):
            return squad
        else:
            return generate_valid_squad(players, attempt + 1)
    except:
        return generate_valid_squad(players, attempt + 1)


def simulate_squad_mc(squad: List[RealFPLPlayer], iterations: int = 500, captain_id: int = None) -> Dict[str, float]:
    """Run Monte Carlo simulation with CAPTAIN BONUS (2x)."""
    scores = []

    if captain_id is None:
        captain_id = max(squad, key=lambda p: float(p.ep_next)).id

    for _ in range(iterations):
        score = 0
        captain_points = 0

        for p in squad:
            points = float(p.ep_next)
            form_boost = p.form * 0.1
            points += form_boost
            variance = np.random.normal(0, 0.5)
            points += variance
            chance = p.chance_of_playing_next_round or 100
            if np.random.random() > (chance / 100):
                points *= 0.3

            player_points = max(0, points)
            score += player_points

            if p.id == captain_id:
                captain_points = player_points

        # CAPTAIN BONUS: Double the captain's points (2x)
        score += captain_points

        # Bench bonus
        bench_bonus = np.random.uniform(0, 3)
        score += bench_bonus

        # Fixture variance
        fixture_var = np.random.uniform(-0.15, 0.10)
        score *= (1 + fixture_var)

        scores.append(max(0, score))

    scores = sorted(scores)
    return {
        "avg": np.mean(scores),
        "p10": scores[int(len(scores) * 0.1)],
        "p90": scores[int(len(scores) * 0.9)],
        "min": min(scores),
        "max": max(scores),
    }


async def main():
    """Run Monte Carlo competition with 5000 teams."""
    logger.info("=" * 80)
    logger.info("🏆 FPL MONTE CARLO COMPETITION - 5000 TEAMS")
    logger.info("=" * 80)
    logger.info(f"⏰ Start time: {datetime.now()}")
    logger.info(f"📊 Competition: 5,000 teams × 500 MC iterations = 2.5M simulations")
    logger.info("=" * 80)

    # Fetch real FPL data
    fpl_data = await fetch_fpl_data()

    if not fpl_data:
        logger.error("❌ Failed to fetch FPL data")
        return

    elements = fpl_data.get('elements', [])
    teams = fpl_data.get('teams', [])

    team_map = {t['id']: t['name'] for t in teams}

    logger.info(f"✅ Loaded {len(elements)} players")
    logger.info(f"✅ Loaded {len(teams)} teams")

    players = [RealFPLPlayer(p, team_map) for p in elements]
    available = [p for p in players if p.status == 'a']
    logger.info(f"✅ {len(available)} players available (status='a')")

    # Generate 5000 valid squads
    logger.info("\n🤖 Generating 5,000 squad candidates...")
    squads = []
    attempts = 0
    max_attempts = 100000

    while len(squads) < 5000 and attempts < max_attempts:
        squad = generate_valid_squad(players)
        if squad:
            squads.append(squad)
        attempts += 1

        if len(squads) % 500 == 0:
            logger.info(f"   Generated: {len(squads)}/5000...")

    logger.info(f"✅ Generated {len(squads)} valid squads\n")

    # Run Monte Carlo
    logger.info("⚙️  Running Monte Carlo simulations (500 iterations each)...")
    logger.info("   This may take 10-15 minutes...\n")

    results = []
    for idx, squad in enumerate(squads):
        if idx % 500 == 0:
            logger.info(f"   Progress: {idx}/{len(squads)}...")

        captain = max(squad, key=lambda p: float(p.ep_next))
        mc_result = simulate_squad_mc(squad, iterations=500, captain_id=captain.id)

        gkp = sum(1 for p in squad if p.element_type == 1)
        def_count = sum(1 for p in squad if p.element_type == 2)
        mid_count = sum(1 for p in squad if p.element_type == 3)
        fwd_count = sum(1 for p in squad if p.element_type == 4)
        formation = f"{def_count}-{mid_count}-{fwd_count}"

        ownership = sum(p.selected_by_percent for p in squad) / len(squad)
        cost = sum(p.now_cost for p in squad)

        results.append({
            "squad_id": idx,
            "squad": squad,
            "captain": captain,
            "formation": formation,
            "avg": mc_result["avg"],
            "p10": mc_result["p10"],
            "p90": mc_result["p90"],
            "ownership": ownership,
            "cost": cost,
        })

    logger.info(f"✅ Completed {len(results)} simulations\n")

    # Filter teams with 70+ points and sort
    teams_70plus = [r for r in results if r["avg"] >= 70]
    logger.info(f"\n🔥 Teams with 70+ points: {len(teams_70plus)}/5000")

    if not teams_70plus:
        logger.info("⚠️  No teams reached 70+ points")
        logger.info(f"\nTop teams (best available):")
        sorted_results = sorted(results, key=lambda x: x["avg"], reverse=True)[:5]
    else:
        sorted_results = sorted(teams_70plus, key=lambda x: x["avg"], reverse=True)[:5]

    logger.info("\n" + "=" * 80)
    logger.info("🏆 TOP 5 TEAMS - 70+ POINTS THRESHOLD")
    logger.info("=" * 80)

    for rank, best in enumerate(sorted_results, 1):
        logger.info(f"\n🥇 RANK {rank}: Formation {best['formation']}")
        logger.info(f"   Expected Points: {best['avg']:.2f}")
        logger.info(f"   P10 (worst 10%): {best['p10']:.2f} | P90 (best 10%): {best['p90']:.2f}")
        logger.info(f"   Ownership: {best['ownership']:.1f}% | Cost: £{best['cost']:.1f}m")
        logger.info(f"   Captain: {best['captain'].web_name} ({best['captain'].team_name}) - EP: {best['captain'].ep_next:.1f} × 2x = {best['captain'].ep_next*2:.1f}pts")

        logger.info(f"\n   SQUAD (15 players):")
        for p in sorted(best['squad'], key=lambda x: x.element_type):
            pos_map = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
            captain_flag = "⭐ " if p.id == best['captain'].id else "   "
            logger.info(f"   {captain_flag}{p.web_name:20} ({pos_map[p.element_type]}) {p.team_name:15} £{p.now_cost:.1f}m | EP: {p.ep_next:.1f}")

    logger.info("\n" + "=" * 80)
    logger.info("📈 OVERALL STATISTICS")
    logger.info("=" * 80)

    all_avg = [r["avg"] for r in results]
    logger.info(f"Average expected points (all 5000): {np.mean(all_avg):.2f}")
    logger.info(f"Best possible team: {np.max(all_avg):.2f}")
    logger.info(f"Worst team: {np.min(all_avg):.2f}")
    logger.info(f"Best teams range: {np.max(all_avg) - np.min(all_avg):.2f}pts")
    logger.info(f"Teams reaching 70+: {len(teams_70plus)} ({len(teams_70plus)/len(results)*100:.1f}%)")

    logger.info("\n" + "=" * 80)
    logger.info(f"✅ COMPETITION COMPLETE")
    logger.info(f"⏰ End time: {datetime.now()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
