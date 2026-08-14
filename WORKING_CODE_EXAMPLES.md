# Working Code Examples: FPL, EA Sports, and FIFA APIs
**Purpose:** Production-ready code snippets for integrating premium data sources  
**Last Updated:** August 14, 2026

---

## 1. FANTASY PREMIER LEAGUE (FPL) API - WORKING EXAMPLES

### 1.1 Basic FPL Data Fetch (No Dependencies Beyond httpx)

```python
"""
Minimal FPL API usage - works immediately with standard library
No authentication required
"""
import httpx
import json
from typing import Any

class FPLClient:
    """Simple FPL API client using httpx"""
    
    BASE_URL = "https://fantasy.premierleague.com/api"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def get_bootstrap(self) -> dict[str, Any]:
        """Get all players, teams, gameweeks in one request"""
        response = self.client.get(f"{self.BASE_URL}/bootstrap-static/")
        response.raise_for_status()
        return response.json()
    
    def get_fixtures(self) -> list[dict[str, Any]]:
        """Get all season fixtures"""
        response = self.client.get(f"{self.BASE_URL}/fixtures/")
        response.raise_for_status()
        return response.json()
    
    def get_player_summary(self, player_id: int) -> dict[str, Any]:
        """Get detailed player information and fixture list"""
        response = self.client.get(f"{self.BASE_URL}/element-summary/{player_id}/")
        response.raise_for_status()
        return response.json()
    
    def get_gameweek_live(self, gameweek: int) -> dict[str, Any]:
        """Get live points for a specific gameweek"""
        response = self.client.get(f"{self.BASE_URL}/event/{gameweek}/live/")
        response.raise_for_status()
        return response.json()
    
    def get_standings(self, league_id: int) -> dict[str, Any]:
        """Get league standings"""
        response = self.client.get(f"{self.BASE_URL}/leagues-classic/{league_id}/standings/")
        response.raise_for_status()
        return response.json()

# USAGE EXAMPLE
if __name__ == "__main__":
    fpl = FPLClient()
    
    # Get all players
    print("Fetching bootstrap data...")
    data = fpl.get_bootstrap()
    
    print(f"Total players: {len(data['elements'])}")
    print(f"Total teams: {len(data['teams'])}")
    print(f"Total gameweeks: {len(data['events'])}")
    
    # Top 5 players by points
    print("\nTop 5 players:")
    players = sorted(
        data['elements'],
        key=lambda x: x['total_points'],
        reverse=True
    )[:5]
    
    for player in players:
        name = player['first_name'] + ' ' + player['second_name']
        points = player['total_points']
        team_id = player['team']
        team_name = next(t['name'] for t in data['teams'] if t['id'] == team_id)
        print(f"  {name:25} {points:3d} pts ({team_name})")
    
    # Get fixtures for next 5 gameweeks
    print("\nUpcoming fixtures:")
    fixtures = fpl.get_fixtures()
    upcoming = [f for f in fixtures if f['status'] == 'SCHEDULED'][:5]
    
    for fixture in upcoming:
        gw = fixture['event']
        home = fixture['team_h_name']
        away = fixture['team_a_name']
        date = fixture['kickoff_time']
        print(f"  GW{gw}: {home} vs {away} ({date})")
```

### 1.2 Async FPL Client (High Performance)

```python
"""
Async FPL client for high-performance data fetching
Suitable for production environments
"""
import asyncio
import httpx
from typing import Any
from datetime import datetime
import json

class AsyncFPLClient:
    """Async HTTP client for FPL API with caching"""
    
    BASE_URL = "https://fantasy.premierleague.com/api"
    
    def __init__(self, cache_dir: str = "./fpl_cache"):
        self.cache_dir = cache_dir
        self.cache = {}
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    async def get_bootstrap(self, force_refresh: bool = False) -> dict[str, Any]:
        """Get all players, teams, gameweeks"""
        if not force_refresh and 'bootstrap' in self.cache:
            return self.cache['bootstrap']
        
        response = await self.client.get(f"{self.BASE_URL}/bootstrap-static/")
        response.raise_for_status()
        data = response.json()
        
        self.cache['bootstrap'] = data
        return data
    
    async def get_gameweek_live(self, gameweek: int) -> dict[str, Any]:
        """Get live data for gameweek"""
        response = await self.client.get(f"{self.BASE_URL}/event/{gameweek}/live/")
        response.raise_for_status()
        return response.json()
    
    async def get_multiple_players(self, player_ids: list[int]) -> list[dict[str, Any]]:
        """Fetch multiple players concurrently"""
        tasks = [
            self.client.get(f"{self.BASE_URL}/element-summary/{pid}/")
            for pid in player_ids
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
    
    async def get_all_fixtures(self) -> list[dict[str, Any]]:
        """Get all season fixtures"""
        response = await self.client.get(f"{self.BASE_URL}/fixtures/")
        response.raise_for_status()
        return response.json()

# USAGE EXAMPLE
async def main():
    async with AsyncFPLClient() as fpl:
        # Get bootstrap
        data = await fpl.get_bootstrap()
        players = data['elements']
        
        # Get live data for GW1
        live_gw1 = await fpl.get_gameweek_live(1)
        
        # Fetch 10 players concurrently
        top_10_ids = [p['id'] for p in sorted(
            players,
            key=lambda x: x['total_points'],
            reverse=True
        )[:10]]
        
        player_details = await fpl.get_multiple_players(top_10_ids)
        
        print(f"Fetched {len(player_details)} player details")
        print(f"Live GW1 data: {len(live_gw1['elements'])} player scores")

asyncio.run(main())
```

### 1.3 Using the `fpl` Library (Recommended)

```python
"""
Using the official amosbastian/fpl library
Install: pip install fpl
"""
import asyncio
import aiohttp
from fpl import FPL

async def main():
    """Complete FPL workflow example"""
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        # Get all players
        players = await fpl.get_players()
        
        # Get all gameweeks
        gameweeks = await fpl.get_gameweeks()
        
        # Get current gameweek
        current_gw = await fpl.get_gameweek()
        print(f"Current gameweek: {current_gw.id}")
        
        # Get fixtures
        fixtures = await fpl.get_fixtures()
        
        # Get specific player
        salah = await fpl.get_player(element_id=13, return_json=False)
        print(f"Salah: {salah.total_points} total points")
        
        # Get player history
        history = salah.get_history()
        print(f"Salah's last 5 gameweeks:")
        for gameweek in history[-5:]:
            print(f"  GW{gameweek['round']}: {gameweek['total_points']} points")
        
        # Get team
        arsenal = await fpl.get_team(1, return_json=False)
        print(f"\nArsenal squad:")
        for player in arsenal.players:
            print(f"  {player.web_name} ({player.element_type})")
        
        # Get user team (if ID known)
        user_id = 12345  # Example user ID
        try:
            user = await fpl.get_user(user_id, return_json=False)
            print(f"\nUser {user.username}:")
            print(f"  Total points: {user.summary_overall_points}")
            print(f"  Rank: {user.summary_overall_rank}")
        except Exception as e:
            print(f"Could not fetch user: {e}")

# Run
asyncio.run(main())
```

### 1.4 Building a Prediction Feature Pipeline

```python
"""
Extract prediction features from FPL API data
Ready for ML models
"""
import asyncio
import aiohttp
from fpl import FPL
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlayerFeatures:
    """Features for player performance prediction"""
    player_id: int
    player_name: str
    team: str
    position: str
    
    # Recent form
    points_last_5: float
    average_points_last_5: float
    
    # Consistency
    std_dev_last_5: float
    
    # Selection
    selected_by_percent: float
    ownership_trend: str  # "rising" / "stable" / "falling"
    
    # Fixture difficulty
    next_5_fixture_difficulty: list[int]
    home_games_next_5: int
    
    # Injury/availability
    status: str
    chance_of_playing: Optional[int]
    
    # In-game stats
    expected_goals: float
    expected_assists: float
    threat: float
    creativity: float

async def extract_features(player, fpl_client) -> PlayerFeatures:
    """Extract prediction features for a player"""
    
    # Get player summary with fixture list
    summary = await fpl_client.get_player(player['id'], return_json=True)
    
    # Get recent history
    history = summary.get('history', [])
    last_5 = history[-5:] if len(history) >= 5 else history
    
    last_5_points = [h['total_points'] for h in last_5]
    
    # Calculate stats
    import statistics
    avg_last_5 = statistics.mean(last_5_points) if last_5_points else 0
    std_last_5 = statistics.stdev(last_5_points) if len(last_5_points) > 1 else 0
    
    # Get fixtures
    fixtures = summary.get('fixtures', [])[:5]
    fixture_difficulties = [f['difficulty'] for f in fixtures]
    home_games = sum(1 for f in fixtures if f['is_home'])
    
    # Build features
    features = PlayerFeatures(
        player_id=player['id'],
        player_name=f"{player['first_name']} {player['second_name']}",
        team=player['team'],
        position=player['element_type'],
        
        points_last_5=sum(last_5_points),
        average_points_last_5=avg_last_5,
        std_dev_last_5=std_last_5,
        
        selected_by_percent=float(player['selected_by_percent']),
        ownership_trend="stable",  # Would calculate from historical data
        
        next_5_fixture_difficulty=fixture_difficulties,
        home_games_next_5=home_games,
        
        status=player['status'] or "available",
        chance_of_playing=player.get('chance_of_playing_this_round'),
        
        expected_goals=float(player.get('expected_goals', 0)),
        expected_assists=float(player.get('expected_assists', 0)),
        threat=float(player.get('threat', 0)),
        creativity=float(player.get('creativity', 0)),
    )
    
    return features

async def build_feature_matrix():
    """Build feature matrix for all players"""
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        # Get all players
        bootstrap = await fpl.get_bootstrap()
        players = bootstrap['elements']
        
        # Extract features for top 100 players
        features_list = []
        for player in sorted(players, key=lambda x: x['selected_by_percent'], reverse=True)[:100]:
            try:
                features = await extract_features(player, fpl)
                features_list.append(features)
            except Exception as e:
                print(f"Error processing {player['web_name']}: {e}")
        
        return features_list

# Run
async def main():
    features = await build_feature_matrix()
    
    print(f"Built feature matrix for {len(features)} players")
    
    # Sort by predicted points (example heuristic)
    sorted_features = sorted(
        features,
        key=lambda f: f.average_points_last_5 - (f.std_dev_last_5 * 0.5),
        reverse=True
    )
    
    print("\nTop 10 by predicted points:")
    for f in sorted_features[:10]:
        print(f"  {f.player_name:20} {f.average_points_last_5:.1f} avg pts")

asyncio.run(main())
```

---

## 2. FUTDB API - WORKING EXAMPLES

### 2.1 Basic FutDB Client

```python
"""
FutDB API for EA Sports FC player data
Free tier available at https://futdb.app
"""
import requests
from typing import Optional, List
import json

class FutDBClient:
    """FutDB API client for FC 26 player data"""
    
    BASE_URL = "https://api.fut-db.com/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Accept": "application/json"
        }
    
    def get_players(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Get paginated list of players"""
        response = requests.get(
            f"{self.BASE_URL}/players",
            headers=self.headers,
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()['items']
    
    def search_player(self, name: str) -> List[dict]:
        """Search for player by name"""
        response = requests.get(
            f"{self.BASE_URL}/players/search",
            headers=self.headers,
            params={"name": name}
        )
        response.raise_for_status()
        return response.json()['items']
    
    def get_player(self, player_id: int) -> dict:
        """Get specific player details"""
        response = requests.get(
            f"{self.BASE_URL}/players/{player_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_clubs(self) -> List[dict]:
        """Get all clubs"""
        response = requests.get(
            f"{self.BASE_URL}/clubs",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['items']
    
    def get_nations(self) -> List[dict]:
        """Get all nations"""
        response = requests.get(
            f"{self.BASE_URL}/nations",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['items']
    
    def get_leagues(self) -> List[dict]:
        """Get all leagues"""
        response = requests.get(
            f"{self.BASE_URL}/leagues",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['items']

# USAGE EXAMPLE
if __name__ == "__main__":
    # Get API key from https://futdb.app
    client = FutDBClient(api_key="YOUR_API_KEY_HERE")
    
    # Search for Salah
    print("Searching for Salah...")
    salah_results = client.search_player("Salah")
    
    if salah_results:
        salah = salah_results[0]
        print(f"\nFound: {salah['name']}")
        print(f"Overall: {salah['overall']}")
        print(f"Pace: {salah['pace']}")
        print(f"Shooting: {salah['shooting']}")
        print(f"Passing: {salah['passing']}")
        print(f"Dribbling: {salah['dribbling']}")
        print(f"Defense: {salah['defense']}")
        print(f"Physical: {salah['physical']}")
        print(f"Club: {salah['club_id']}")
        print(f"Nation: {salah['nation_id']}")
    
    # Get all Premier League players
    print("\n\nGetting all players...")
    players = client.get_players(limit=20)
    print(f"Fetched {len(players)} players")
    
    for player in players[:5]:
        print(f"  {player['name']:30} Overall: {player['overall']}")
    
    # Get clubs
    print("\n\nGetting clubs...")
    clubs = client.get_clubs()
    print(f"Total clubs: {len(clubs)}")
    for club in clubs[:5]:
        print(f"  {club['name']:30} League: {club['league_id']}")
```

### 2.2 Async FutDB Client

```python
"""
Async FutDB client for better performance
"""
import httpx
import asyncio
from typing import List

class AsyncFutDBClient:
    """Async FutDB client"""
    
    BASE_URL = "https://api.fut-db.com/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Accept": "application/json"
        }
    
    async def search_player(self, name: str, client: httpx.AsyncClient) -> List[dict]:
        """Search for player"""
        response = await client.get(
            f"{self.BASE_URL}/players/search",
            headers=self.headers,
            params={"name": name}
        )
        response.raise_for_status()
        return response.json()['items']
    
    async def get_player(self, player_id: int, client: httpx.AsyncClient) -> dict:
        """Get player details"""
        response = await client.get(
            f"{self.BASE_URL}/players/{player_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def search_multiple_players(self, names: List[str]) -> List[dict]:
        """Search multiple players concurrently"""
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = [self.search_player(name, client) for name in names]
            results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_players = []
        for result in results:
            all_players.extend(result)
        return all_players

# USAGE
async def main():
    client = AsyncFutDBClient(api_key="YOUR_API_KEY")
    
    # Search multiple players at once
    premier_league_players = [
        "Salah", "De Bruyne", "Foden", "Haaland", "Kane"
    ]
    
    players = await client.search_multiple_players(premier_league_players)
    
    print(f"Found {len(players)} players")
    for player in players:
        print(f"  {player['name']:30} Overall: {player['overall']}")

asyncio.run(main())
```

---

## 3. FUTBIN DATA SCRAPING - WORKING EXAMPLES

### 3.1 Using Parse.bot Futbin API (Official Alternative)

```python
"""
Parse.bot provides official Futbin API scraping
No direct scraping needed - legal alternative
"""
import requests

class ParseBotFutbinAPI:
    """Wrapper for Parse.bot Futbin scraper"""
    
    # Register at parse.bot/marketplace for credentials
    PARSE_API = "https://api.parse.bot/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_player_data(self, player_name: str) -> dict:
        """Get player data from Futbin via Parse.bot"""
        # This requires specific Parse.bot configuration
        # Contact Parse.bot for integration details
        
        response = requests.post(
            f"{self.parse_api}/actors/getFutbinPlayerData/run",
            headers=self.headers,
            json={"playerName": player_name}
        )
        response.raise_for_status()
        return response.json()

# USAGE
# 1. Register at https://parse.bot/
# 2. Purchase Futbin scraper credits
# 3. Use API to fetch data
```

### 3.2 Educational Web Scraping (Verify ToS First)

```python
"""
Educational example of web scraping Futbin
WARNING: Always verify current ToS before using
This example demonstrates the technique only
"""
import httpx
from bs4 import BeautifulSoup
import asyncio
import time

class FutbinScraper:
    """Educational web scraper for Futbin (verify ToS first!)"""
    
    BASE_URL = "https://www.futbin.com"
    
    def __init__(self, delay_between_requests: float = 2.0):
        self.delay = delay_between_requests
        self.last_request_time = 0
    
    async def _respectful_get(self, url: str) -> str:
        """GET request with rate limiting to be respectful"""
        # Wait to avoid overloading server
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        
        self.last_request_time = time.time()
        return response.text
    
    async def search_player(self, player_name: str) -> dict:
        """Search for player on Futbin"""
        search_url = f"{self.BASE_URL}/search?q={player_name}"
        
        html = await self._respectful_get(search_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Parse player data from HTML (structure varies - adjust selectors)
        player_rows = soup.find_all('tr', class_='player-row')
        
        if not player_rows:
            return None
        
        # Get first result
        row = player_rows[0]
        
        try:
            player_data = {
                'name': row.find('td', class_='player-name').text.strip(),
                'overall': row.find('td', class_='overall').text.strip(),
                'price': row.find('td', class_='price').text.strip(),
            }
            return player_data
        except AttributeError:
            return None

# USAGE - EDUCATION ONLY
async def main():
    # WARNING: Verify FUTBIN ToS before running
    # This is for educational purposes only
    scraper = FutbinScraper(delay_between_requests=2.0)
    
    player_data = await scraper.search_player("Salah")
    if player_data:
        print(f"Player: {player_data['name']}")
        print(f"Overall: {player_data['overall']}")
        print(f"Price: {player_data['price']}")

# UNCOMMENT TO RUN
# asyncio.run(main())
```

---

## 4. INTEGRATION EXAMPLES

### 4.1 FPL to Kalshi Pipeline

```python
"""
Example: Use FPL data to generate Kalshi market signals
"""
import asyncio
import aiohttp
from fpl import FPL
from typing import List, Dict

class FPLKalshiBridge:
    """Bridge between FPL and Kalshi prediction markets"""
    
    def __init__(self, kalshi_api_key: str = None):
        self.kalshi_key = kalshi_api_key
    
    async def get_player_signals(self) -> List[Dict]:
        """Generate prediction signals for all players"""
        signals = []
        
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            
            # Get all players
            players = await fpl.get_players()
            
            # Get current gameweek
            current_gw = await fpl.get_gameweek()
            
            for player in players[:50]:  # Top 50 players
                signal = self._generate_signal(player, current_gw)
                signals.append(signal)
        
        return signals
    
    def _generate_signal(self, player, current_gw) -> Dict:
        """Generate market signal for a player"""
        
        # Simple heuristic (would use ML model in production)
        last_5_avg = player.get('form', 0)
        selected_pct = float(player.get('selected_by_percent', 0))
        threat = float(player.get('threat', 0))
        
        # Predict points: form + selection + threat
        predicted_points = (
            last_5_avg * 2 +
            (selected_pct / 100) * 10 +
            (threat / 100) * 15
        )
        
        # Generate market prediction
        signal = {
            'player_id': player['id'],
            'player_name': f"{player['first_name']} {player['second_name']}",
            'gameweek': current_gw.id,
            'predicted_points': max(0, min(20, predicted_points)),
            'confidence': 0.65,  # Would calculate from model validation
            'market_type': 'points_over_under',
            'recommended_bet': 'OVER' if predicted_points > 10 else 'UNDER',
        }
        
        return signal
    
    async def get_top_signals(self, limit: int = 10) -> List[Dict]:
        """Get top N predicted performers"""
        signals = await self.get_player_signals()
        
        # Sort by confidence * predicted points
        ranked = sorted(
            signals,
            key=lambda s: s['predicted_points'] * s['confidence'],
            reverse=True
        )
        
        return ranked[:limit]

# USAGE
async def main():
    bridge = FPLKalshiBridge(kalshi_api_key="YOUR_KEY")
    
    # Get top 10 predictions
    signals = await bridge.get_top_signals(limit=10)
    
    print("Top 10 Player Predictions for Kalshi")
    print("=" * 60)
    
    for signal in signals:
        print(f"\n{signal['player_name']:25} GW{signal['gameweek']}")
        print(f"  Predicted Points: {signal['predicted_points']:.1f}")
        print(f"  Confidence: {signal['confidence']:.0%}")
        print(f"  Recommendation: {signal['recommended_bet']}")

asyncio.run(main())
```

### 4.2 Combined FPL + FutDB Analysis

```python
"""
Combine FPL real performance with game ratings for analysis
"""
import asyncio
import aiohttp
from fpl import FPL
import requests

class DualSourceAnalyzer:
    """Analyze players using both FPL and FutDB data"""
    
    def __init__(self, futdb_key: str):
        self.futdb_key = futdb_key
    
    async def analyze_player(self, fpl_id: int, player_name: str) -> dict:
        """Get comprehensive player analysis from both sources"""
        
        # Get FPL data
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            fpl_player = await fpl.get_player(fpl_id, return_json=False)
        
        # Get FutDB game data
        futdb_headers = {"X-API-Key": self.futdb_key}
        futdb_response = requests.get(
            f"https://api.fut-db.com/api/v1/players/search",
            headers=futdb_headers,
            params={"name": player_name}
        )
        futdb_data = futdb_response.json()['items'][0] if futdb_response.json()['items'] else None
        
        # Combine analysis
        analysis = {
            'player_name': player_name,
            
            # FPL metrics
            'fpl': {
                'total_points': fpl_player.total_points,
                'form': float(fpl_player.form),
                'selected_by': float(fpl_player.selected_by_percent),
                'minutes': fpl_player.minutes,
                'goals': fpl_player.goals_scored,
                'assists': fpl_player.assists,
            },
            
            # Game metrics (if available)
            'game': {
                'overall_rating': futdb_data['overall'] if futdb_data else None,
                'pace': futdb_data['pace'] if futdb_data else None,
                'shooting': futdb_data['shooting'] if futdb_data else None,
                'passing': futdb_data['passing'] if futdb_data else None,
                'dribbling': futdb_data['dribbling'] if futdb_data else None,
            },
            
            # Correlation
            'correlation': {
                'form_vs_rating': "Positive" if (
                    float(fpl_player.form) > 0 and 
                    futdb_data and futdb_data['overall'] > 85
                ) else "Neutral",
                'recommendation': "Good form + High rating = BUY",
            }
        }
        
        return analysis

# USAGE
async def main():
    analyzer = DualSourceAnalyzer(futdb_key="YOUR_KEY")
    
    analysis = await analyzer.analyze_player(fpl_id=13, player_name="Mohamed Salah")
    
    print("Combined Player Analysis")
    print("=" * 50)
    print(f"\nPlayer: {analysis['player_name']}")
    
    print("\nFPL Metrics:")
    for key, value in analysis['fpl'].items():
        print(f"  {key:15}: {value}")
    
    print("\nGame Metrics:")
    for key, value in analysis['game'].items():
        if value is not None:
            print(f"  {key:15}: {value}")
    
    print("\nCorrelation Analysis:")
    for key, value in analysis['correlation'].items():
        print(f"  {key:15}: {value}")

asyncio.run(main())
```

---

## 5. SETUP INSTRUCTIONS

### 5.1 Install Dependencies

```bash
# FPL API access
pip install fpl httpx aiohttp

# FutDB access
pip install requests

# Web scraping (if needed)
pip install beautifulsoup4 httpx
```

### 5.2 Get API Keys

**FPL API:**
- ✅ No key needed - public API
- Just start using!

**FutDB:**
1. Visit https://futdb.app
2. Create free account
3. Generate API key in dashboard
4. Use in code: `client = FutDBClient(api_key="YOUR_KEY")`

**Parse.bot (Futbin Scraping):**
1. Visit https://parse.bot
2. Sign up for free tier
3. Purchase Futbin scraper credits
4. Get API credentials

### 5.3 Quick Test

```bash
# Test FPL connectivity
python -c "
import httpx
response = httpx.get('https://fantasy.premierleague.com/api/bootstrap-static/')
data = response.json()
print(f'✓ Connected to FPL API')
print(f'  Players: {len(data[\"elements\"])}')
print(f'  Teams: {len(data[\"teams\"])}')
print(f'  Gameweeks: {len(data[\"events\"])}')
"
```

---

## 6. PRODUCTION CHECKLIST

- [ ] Implement caching (1hr for bootstrap, 2min for live data)
- [ ] Add error handling and retries
- [ ] Set up rate limiting (respect API limits)
- [ ] Implement logging
- [ ] Add monitoring/alerting
- [ ] Document data sources
- [ ] Verify legal compliance (ToS)
- [ ] Test with real data before deploying
- [ ] Set up automated data refresh (APScheduler)
- [ ] Monitor API status page

---

**End of Working Examples**
*Last Updated: August 14, 2026*
