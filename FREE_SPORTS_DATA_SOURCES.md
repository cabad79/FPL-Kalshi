# FREE SPORTS DATA SOURCES: Complete Toolkit for Football Prediction Markets

**Last Updated:** August 2026  
**Project:** FPL-Kalshi Sports MCP Bootstrap  
**Goal:** $0 initial investment, real-time data for English football prediction markets

---

## EXECUTIVE SUMMARY: THE BOOTSTRAP PATH

### Cost to Launch: **$0**
- **Phase 1 (Days 1-7):** Free APIs + basic data aggregation
- **Phase 2 (Days 8-14):** Web scraping + Reddit sentiment
- **Phase 3 (Days 15-21):** Advanced models + odds integration
- **Phase 4 (Month 2+):** Revenue growth → selective paid upgrades

### Coverage Achievable with FREE sources:
- ✅ All Premier League fixtures, results, lineups
- ✅ Real-time odds from multiple bookmakers
- ✅ Player performance metrics (goals, assists, xG)
- ✅ Injury news and team updates
- ✅ Community sentiment (Reddit/Twitter)
- ✅ Historical data (5+ years)
- ✅ Weather forecasts for match prediction
- ✅ Basic statistical models (xG, Poisson)

### Revenue Generation Path:
1. **Immediate (Week 1):** Sell fixture analysis + lineup predictions
2. **Week 2:** Add sentiment-based market signals
3. **Week 3:** Deploy automated betting recommendations
4. **Month 2+:** Once revenue covers costs, add premium APIs strategically

---

## 1. FREE PUBLIC APIs (No Authentication Required)

### 1.1 Football-Data.org - HIGHLY RECOMMENDED
**Status:** Actively maintained, proven reliable  
**Free Tier:** Yes (requires registration, no credit card)

```
Base URL: https://www.football-data.org/api/v4/
Rate Limit: 10 requests/min (generous)
Authorization: API Key in header (free tier)
Data Freshness: Updated every 5-15 minutes
Reliability: 9/10
```

**Available Endpoints:**
```
GET /competitions/PL/matches          # All PL matches (current + historical)
GET /matches/{id}                      # Match details, lineups, statistics
GET /competitions/PL/standings         # League table
GET /teams/{id}                        # Team info, squad, latest results
GET /teams/{id}/matches                # Team's match history
GET /competitions/PL/scorers           # Top scorers, assists leaders
```

**What You Get:**
- Fixtures (date, time, opponent, venue)
- Match results and scores
- Team lineups (when available)
- Head-to-head records
- League standings
- Goals, assists, yellow/red cards
- Odds from multiple bookmakers (varies by match)

**Implementation Example (Python):**
```python
import requests

API_KEY = "YOUR_FREE_KEY_FROM_FOOTBALL_DATA_ORG"
BASE_URL = "https://www.football-data.org/api/v4"
headers = {"X-Auth-Token": API_KEY}

# Get all PL matches for a gameweek
response = requests.get(
    f"{BASE_URL}/competitions/PL/matches",
    headers=headers,
    params={"status": "FINISHED"}  # or SCHEDULED, LIVE
)
matches = response.json()["matches"]

for match in matches:
    print(f"{match['homeTeam']['name']} vs {match['awayTeam']['name']}")
    print(f"Score: {match['score']['fullTime']['home']}-{match['score']['fullTime']['away']}")
```

**Cost:** FREE (forever, registration required)  
**ToS:** Commercial use allowed with proper attribution  
**Fallback:** API is very stable, but keep 2-3 backup sources

---

### 1.2 API-Football (RapidAPI) - Free Tier Available
**Status:** Widely used, good coverage  
**Free Tier:** 100 requests/day (limited but usable)

```
Base URL: https://api-football-v3.p.rapidapi.com/
Rate Limit: 100 requests/day (free tier)
Authorization: RapidAPI Key (free subscription)
Data Freshness: Real-time
Reliability: 8/10 (rate limits can be restrictive)
```

**Available Endpoints:**
```
GET /fixtures                     # Matches
GET /fixtures/{id}                # Match details
GET /standings                    # League positions
GET /players                      # Player data
GET /players/{id}/statistics      # Player performance stats
GET /teams                        # Team information
GET /odds                         # Historical odds
GET /predictions                  # ML-based predictions (premium only)
```

**Cost:** FREE (100 req/day limit)  
**Implementation:**
```python
import requests

headers = {
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "api-football-v3.p.rapidapi.com"
}

# Get PL fixtures for a date range
response = requests.get(
    "https://api-football-v3.p.rapidapi.com/fixtures",
    headers=headers,
    params={
        "league": 39,  # Premier League
        "season": 2026,
        "status": "FT"  # Finished
    }
)
```

**Warning:** 100 req/day is tight. Good for once-daily cron jobs, not real-time.

---

### 1.3 Open-Meteo Weather API - Completely Free
**Status:** Gold standard for free weather data  
**Free Tier:** Unlimited requests (no API key required)

```
Base URL: https://api.open-meteo.com/v1/
Rate Limit: Unlimited (free, no auth required)
Data Freshness: Real-time + 15 days forecast
Reliability: 10/10
```

**Available Endpoints:**
```
GET /forecast              # Weather forecasts by coordinates
GET /archive               # Historical weather data
GET /marine               # Weather for coastal areas
```

**Match Data Available:**
- Stadium coordinates (hardcoded per Premier League ground)
- Wind speed (impacts corners, throw-ins)
- Precipitation (affects ball movement, passing accuracy)
- Temperature (player fatigue factor)
- Cloud cover (visibility, pitch conditions)

**Implementation Example:**
```python
import requests

# Stamford Bridge coordinates
STADIUMS = {
    "Chelsea": (51.4816, -0.1910),
    "Arsenal": (51.5549, -0.1084),
    "Man City": (53.4811, -2.2001),
    "Liverpool": (53.4309, -2.9609),
    # ... add all 20 PL teams
}

def get_match_weather(team_home, team_away, match_date):
    lat, lon = STADIUMS[team_home]
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": match_date,
            "end_date": match_date,
            "hourly": "wind_speed_10m,precipitation,temperature_2m",
            "timezone": "Europe/London"
        }
    )
    return response.json()
```

**Cost:** FREE (forever, no limits)  
**Value:** Essential for weather-dependent markets (corners, goals)

---

### 1.4 RapidAPI - Multiple Football Endpoints (Free Tier)
**Options Available:**
- **Football Live Scores** - 100 req/day
- **Sports Live Data** - Basic free tier
- **Soccer API** - Limited free tier

**Cost:** FREE (various rate limits)  
**Quality:** Varies, use as backup

---

### 1.5 Sportify API - Free Tier
**Status:** Basic coverage, limited endpoints  
**Free Tier:** 50 req/day

```
Coverage: Limited to major leagues
Rate Limit: 50 requests/day
Reliability: 6/10
```

**Cost:** FREE (registration required)

---

## 2. FREE TIER SERVICES (Registration, No Credit Card)

### 2.1 Odds Portal - Historical Odds Scraping
**URL:** https://www.oddsportal.com/  
**What:** Free odds comparison, no registration needed

**Available Data:**
- Live odds from 100+ bookmakers
- Historical odds for past matches
- Closing odds (most predictive)
- Implied probabilities

**How to Extract:**
```python
import requests
from bs4 import BeautifulSoup

# Odds Portal is HTML-scrapeable (check ToS)
url = "https://www.oddsportal.com/soccer/england/premier-league/"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Extract odds from match rows
matches = soup.find_all("tr", class_="tr-normal")
for match in matches:
    teams = match.find_all("td")[1].text
    odds_1x2 = match.find_all("td")[2:5]
    print(f"{teams}: {[o.text for o in odds_1x2]}")
```

**Reliability:** 8/10  
**Legal:** Public data, scraping allowed (check current ToS)  
**Cost:** FREE

---

### 2.2 Flashscore - Live Scores & Odds
**URL:** https://www.flashscore.com/  
**Public Data:** Yes, no login required

**Available:**
- Live scores (updated in real-time)
- Match lineups
- Player statistics
- Historical results
- Odds from bookmakers
- Form data (last 5 matches)

**Scraping Approach:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://www.flashscore.com/soccer/england/premier-league/")

# Wait for content to load
matches = driver.find_elements(By.CLASS_NAME, "event")
for match in matches:
    teams = match.find_element(By.CLASS_NAME, "event__match").text
    score = match.find_element(By.CLASS_NAME, "event__score").text
    print(f"{teams}: {score}")

driver.quit()
```

**Cost:** FREE  
**Reliability:** 9/10  
**Legal:** Public data

---

### 2.3 ESPN - Free Public Pages
**URL:** https://www.espn.com/soccer/  
**Access:** No login required for public data

**Available Endpoints (Web Scraping):**
- Match schedules and results
- Team standings
- Player statistics
- Injury reports
- Head-to-head records
- Expert predictions

**Example:**
```python
from espn_api.soccer import *

# Note: ESPN has limited public API for soccer
# Primary access is via web scraping

import requests
from bs4 import BeautifulSoup

url = "https://www.espn.com/soccer/standings/_/league/eng.1"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Extract standings table
standings_rows = soup.find_all("tr", class_="Table__TR")
for row in standings_rows:
    cells = row.find_all("td")
    if len(cells) > 2:
        team = cells[1].text
        points = cells[-1].text
        print(f"{team}: {points} points")
```

**Cost:** FREE  
**Reliability:** 8/10  
**Legal:** Public data, scraping allowed per ToS

---

### 2.4 Transfermarkt - Free Public Data
**URL:** https://www.transfermarkt.com/  
**Access:** No login required

**World's Best Source For:**
- Player market values
- Transfer history and rumors
- Squad lists (all players per team)
- Injury status (updated daily)
- Player statistics (detailed breakdowns)
- Contract information
- Age, height, preferred foot

**Implementation:**
```python
import requests
from bs4 import BeautifulSoup

# Transfermarkt allows scraping with proper user-agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_team_squad(team_id):
    url = f"https://www.transfermarkt.com/arsenal/kader/verein/{team_id}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    players = []
    for row in soup.find_all("tr", class_="odd") + soup.find_all("tr", class_="even"):
        cells = row.find_all("td")
        if len(cells) > 3:
            name = cells[1].text.strip()
            position = cells[2].text.strip()
            age = cells[3].text.strip()
            market_value = cells[6].text.strip()
            players.append({
                "name": name,
                "position": position,
                "age": age,
                "market_value": market_value
            })
    
    return players

# Example: Get Arsenal squad
arsenal = get_team_squad(11)
for player in arsenal:
    print(f"{player['name']} ({player['position']}) - Value: {player['market_value']}")
```

**Key Pages:**
- `/arsenal/kader/verein/1` - Squad list
- `/arsenal/verletzungen/verein/1` - Injury list
- `/arsenal/news/verein/1` - Transfer news

**Cost:** FREE  
**Reliability:** 9/10  
**Legal:** Public data, scraping allowed (be respectful with rate limits)

---

### 2.5 BBC Sport - Free Public Data
**URL:** https://www.bbc.com/sport/football/  
**Access:** Public data, no login

**Available:**
- Live scores
- Fixtures and results
- Team news
- Player form
- Statistics
- Injury reports

**Cost:** FREE  
**Reliability:** 9/10

---

### 2.6 Sky Sports - Limited Free Data
**URL:** https://www.skysports.com/football  
**Access:** Mostly free (some premium content behind paywall)

**Available:**
- Live scores
- Fixtures
- Results
- News
- Team stats

**Cost:** FREE (mostly)  
**Reliability:** 8/10

---

## 3. WEB SCRAPING TARGETS (Legal, Public Data)

### 3.1 Premier League Official Website
**URL:** https://www.premierleague.com/  
**ToS:** Check, but generally allows scraping of public data

**Data Available:**
- Official fixtures and results
- Team standings
- Player statistics
- Official team lineups
- Match statistics (possession, shots, passes)

**Scraping Strategy:**
```python
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class PremierLeagueScraper:
    def __init__(self):
        self.base_url = "https://www.premierleague.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def get_fixtures_gameweek(self, gameweek):
        """Scrape fixtures for specific gameweek"""
        url = f"{self.base_url}/fixtures"
        # PL uses JavaScript rendering, so use Selenium
        driver = webdriver.Chrome()
        driver.get(url)
        
        # Wait for matches to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "matchBlock"))
        )
        
        fixtures = []
        match_blocks = driver.find_elements(By.CLASS_NAME, "matchBlock")
        for block in match_blocks:
            try:
                home = block.find_element(By.CLASS_NAME, "team-home").text
                away = block.find_element(By.CLASS_NAME, "team-away").text
                date = block.find_element(By.CLASS_NAME, "matchDate").text
                fixtures.append({"home": home, "away": away, "date": date})
            except:
                pass
        
        driver.quit()
        return fixtures
    
    def get_team_fixtures(self, team_name):
        """Get fixtures for specific team"""
        url = f"{self.base_url}/clubs/{team_name.lower().replace(' ', '-')}/fixture"
        response = requests.get(url, headers=self.headers)
        # Parse response...
```

**Frequency:** Update once daily (after matches)  
**Reliability:** 9/10  
**Legal:** Public data, commercial use allowed

---

### 3.2 Team Official Websites
**Targets:**
- Manchester City: https://www.mancity.com/
- Liverpool: https://www.liverpoolfc.com/
- Arsenal: https://www.arsenal.com/
- Chelsea: https://www.chelseafc.com/
- Tottenham: https://www.tottenhamhotspur.com/
- Manchester United: https://www.manutd.com/
- Brighton: https://www.brightonandhovealbion.com/
- Aston Villa: https://www.avfc.co.uk/
- And 12 other Premier League teams...

**Data Available:**
- Official team news
- Injury announcements
- Lineups (official confirmation)
- Match reports
- Statistics
- Travel/venue information

**Key Strategy:**
```python
def scrape_injury_news(team_url):
    """Monitor official team site for injury announcements"""
    response = requests.get(team_url + "/news")
    soup = BeautifulSoup(response.content, "html.parser")
    
    injury_keywords = ["injury", "injured", "out", "unavailable", "doubt", "strain", "surgery"]
    
    news_items = soup.find_all("article")
    injuries = []
    
    for article in news_items:
        text = article.text.lower()
        if any(keyword in text for keyword in injury_keywords):
            injuries.append({
                "title": article.find("h3").text if article.find("h3") else "N/A",
                "date": article.find("time")["datetime"] if article.find("time") else "N/A",
                "text": article.text[:200]
            })
    
    return injuries
```

**Frequency:** Check 2-3x daily (before and after matches)  
**Reliability:** 9/10  
**Legal:** Public team announcements, absolutely allowed

---

### 3.3 Reddit - Community Intelligence
**Subreddits:**
- r/FantasyPL (180k members) - GOLD for FPL insights
- r/football (1.3M members) - General football discussion
- r/PremierLeague (500k members) - PL-specific
- r/soccer (3.2M members) - General soccer news

**What You Find:**
- Injury confirmations BEFORE official announcements
- Lineup predictions and analysis
- Expert opinion from data scientists
- Sentiment shifts
- Reddit awards indicate consensus
- Comment threads = crowdsourced validation

**Scraping Implementation:**
```python
import praw
import pandas as pd
from datetime import datetime, timedelta

# Free API access (requires Reddit account)
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="MyFantasyFootballBot/1.0"
)

def extract_injury_signals():
    """Monitor r/FantasyPL for injury discussions"""
    subreddit = reddit.subreddit("FantasyPL")
    
    injury_keywords = ["injury", "injured", "doubt", "out", "fit", "return", "news"]
    injury_posts = []
    
    # Get hot posts from last 24 hours
    for submission in subreddit.hot(limit=50):
        created_time = datetime.fromtimestamp(submission.created_utc)
        if datetime.now() - created_time < timedelta(hours=24):
            if any(keyword in submission.title.lower() for keyword in injury_keywords):
                injury_posts.append({
                    "title": submission.title,
                    "author": submission.author,
                    "upvotes": submission.ups,
                    "comments": submission.num_comments,
                    "created": created_time,
                    "url": submission.url,
                    "sentiment": "bullish" if submission.ups > 500 else "neutral"
                })
    
    # Sort by engagement
    return sorted(injury_posts, key=lambda x: x["upvotes"], reverse=True)

def extract_lineups_predictions():
    """Extract predicted lineups from Reddit discussion"""
    subreddit = reddit.subreddit("FantasyPL")
    
    predictions = {}
    
    # Find "Lineups" or "Predicted XI" threads
    for submission in subreddit.hot(limit=30):
        if "lineups" in submission.title.lower() or "xi" in submission.title.lower():
            # Get top comments (assumed to be predictions)
            submission.comments.replace_more(limit=0)
            for comment in submission.comments[:20]:
                if comment.score > 50:  # Only high-upvote predictions
                    predictions[submission.title] = {
                        "comment": comment.body,
                        "confidence": comment.score
                    }
    
    return predictions
```

**Reddit API Registration:**
1. Go to https://www.reddit.com/prefs/apps
2. Create app (Free, no cost)
3. Get client ID and secret
4. Install praw: `pip install praw`

**Cost:** FREE  
**Reliability:** 8/10 (depends on community activity)  
**Legal:** Public data, praw follows Reddit ToS

---

## 4. SOCIAL MEDIA & NEWS INTEGRATION

### 4.1 Twitter/X - Real-Time Signals
**Best For:**
- Breaking injury announcements
- Transfer news
- Expert predictions
- Sentiment shifts

**Follow These Accounts:**
- @premierleague - Official
- @SkySportsPL - Breaking news
- Individual club accounts (@Arsenal, @ManCity, etc.)
- Tier 1 journalists (@FabrizioRomano, @AjaxShowtime, etc.)
- Fantasy experts (@FPLWisdom, @Lateriser12, etc.)

**Free Extraction:**
```python
# Using Twitter API v2 FREE tier (450k tweets/month)
import requests

TWITTER_API_KEY = "YOUR_FREE_TWITTER_API_KEY"
headers = {
    "Authorization": f"Bearer {TWITTER_API_KEY}"
}

def get_injury_tweets():
    """Extract injury-related tweets from Premier League"""
    query = "Premier League injury -is:retweet"
    url = "https://api.twitter.com/2/tweets/search/recent"
    
    params = {
        "query": query,
        "max_results": 100,
        "tweet.fields": "created_at,public_metrics",
        "expansions": "author_id"
    }
    
    response = requests.get(url, headers=headers, params=params)
    tweets = response.json()["data"]
    
    return [
        {
            "text": tweet["text"],
            "created_at": tweet["created_at"],
            "retweets": tweet["public_metrics"]["retweet_count"],
            "likes": tweet["public_metrics"]["like_count"]
        }
        for tweet in tweets
    ]
```

**Twitter Free API Setup:**
- Apply at: https://developer.twitter.com/
- Free tier: 450k tweets/month
- Approved for academic/hobbyist use
- Get keys instantly

**Cost:** FREE (with basic limitations)  
**Reliability:** 9/10

---

### 4.2 RSS Feeds - News Aggregation
**Free Sources:**
- BBC Sport: https://feeds.bbc.co.uk/sport/0/rss.xml
- ESPN: https://www.espn.com/espnfeeds/
- Sky Sports: https://www.skysports.com/feeds/
- The Guardian: https://www.theguardian.com/football/rss
- Goal.com: https://www.goal.com/feeds
- CNET Sports: https://www.cnet.com/news/sports/rss

**Implementation:**
```python
import feedparser
import pandas as pd
from datetime import datetime

def aggregate_sports_news():
    """Pull latest news from multiple RSS feeds"""
    feeds = [
        "https://feeds.bbc.co.uk/sport/0/rss.xml",
        "https://www.theguardian.com/football/rss",
        "https://www.goal.com/feeds"
    ]
    
    all_items = []
    
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:  # Last 20 items
            all_items.append({
                "title": entry.title,
                "source": feed.feed.title,
                "published": entry.published_parsed,
                "summary": entry.summary[:200] if "summary" in entry else "",
                "link": entry.link
            })
    
    df = pd.DataFrame(all_items)
    # Filter for injury/news keywords
    keywords = ["injury", "injured", "out", "return", "transfer", "announce"]
    df_filtered = df[df["title"].str.lower().str.contains("|".join(keywords))]
    
    return df_filtered.sort_values("published", ascending=False)

# Run every 30 minutes
news = aggregate_sports_news()
print(news)
```

**Cost:** FREE  
**Reliability:** 9/10  
**Freshness:** 15-60 minutes behind breaking news

---

## 5. BETTING ODDS AGGREGATORS (Free)

### 5.1 Betfair Historical Odds (JSON Download)
**URL:** https://historicaldata.betfair.com/  
**What:** Historical odds from Betfair exchange (betting exchange, not bookmaker)

**How to Access:**
```python
# Betfair allows bulk download of historical odds
# Download via web interface or API (Betfair API requires account)

import requests
import json

def download_historical_odds(date_from, date_to):
    """
    Manual download process:
    1. Go to https://historicaldata.betfair.com/
    2. Select sport (Football)
    3. Select league (Premier League)
    4. Download CSV
    5. Parse locally
    """
    
    # After downloading CSV:
    import pandas as pd
    
    odds_df = pd.read_csv("betfair_historical_odds.csv")
    
    # Columns: Match ID, Home Team, Away Team, Back Odds, Lay Odds, Volume, Timestamp
    # Back odds = betting "for" (moneyline)
    # Lay odds = betting "against" (implies probability)
    
    return odds_df

# Data quality: 9/10 (Betfair is betting exchange, very liquid)
# Freshness: Historical only (can be 6-12 months old)
```

**Cost:** FREE (download CSV)  
**Reliability:** 9/10  
**Legal:** Public historical data

---

### 5.2 OddsPortal API & Scraping
**URL:** https://www.oddsportal.com/  
**Status:** Scrapeable (check current ToS)

**Scraping Approach:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import pandas as pd

def scrape_oddsportal_match(team_home, team_away, date):
    """Scrape live odds for a specific match"""
    
    driver = webdriver.Chrome()
    url = f"https://www.oddsportal.com/soccer/england/premier-league/{date}-{team_home}-{team_away}/"
    
    try:
        driver.get(url)
        
        # Wait for odds table to load
        import time
        time.sleep(3)
        
        # Extract odds rows
        bookies = []
        odds_rows = driver.find_elements(By.CLASS_NAME, "tr-altColor")
        
        for row in odds_rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                bookmaker = cells[0].text
                odds_1 = cells[1].text  # Home win
                odds_x = cells[2].text  # Draw
                odds_2 = cells[3].text  # Away win
                
                bookies.append({
                    "bookmaker": bookmaker,
                    "odds_home": float(odds_1),
                    "odds_draw": float(odds_x),
                    "odds_away": float(odds_2)
                })
            except:
                pass
        
        driver.quit()
        return pd.DataFrame(bookies)
    
    except Exception as e:
        driver.quit()
        print(f"Error scraping: {e}")
        return None

# Get odds comparison
odds = scrape_oddsportal_match("Arsenal", "Chelsea", "2026-08-21")
best_odds = odds.groupby(["odds_home", "odds_draw", "odds_away"]).size().reset_index()
print(f"Best home odds: {odds['odds_home'].max()}")
print(f"Best draw odds: {odds['odds_draw'].max()}")
print(f"Best away odds: {odds['odds_away'].max()}")
```

**Cost:** FREE  
**Reliability:** 8/10  
**Legal:** Check current ToS (public data but site-dependent)

---

### 5.3 SportRadar Free Trial Data
**Status:** Commercial API, but offers 14-day free trial

```
Endpoints: Similar to API-Football
Trial Duration: 14 days
Rate Limit: 1000 requests/day (trial)
Data Quality: Enterprise-grade (10/10)
```

**Strategy:** Get free trial → extract historical data → use for 2 weeks while building on free sources

---

## 6. STATISTICAL MODELS & LIBRARIES (Free, Open Source)

### 6.1 Expected Goals (xG) - Open Source Implementation
**GitHub:** https://github.com/statsbomb/StatsBomb-Event-Data  
**Library:** understat-py (Python wrapper for xG data)

```python
# Option 1: Use existing xG models (Understat-inspired)
import numpy as np
import pandas as pd

class BasicXGModel:
    """Simplified xG model based on shot data"""
    
    def __init__(self):
        # Pre-trained weights (based on historical data)
        self.weights = {
            "distance": 0.15,      # Distance from goal
            "angle": 0.10,         # Angle to goal
            "defender_dist": 0.05, # Closest defender distance
            "assist_type": 0.20,   # How the ball was received
            "shot_type": 0.25,     # Header, foot, etc.
            "previous_events": 0.15 # Build-up play
        }
    
    def calculate_xg(self, shot_data):
        """
        shot_data: {
            "distance": float (yards from goal line),
            "angle": float (degrees),
            "defender_distance": float (yards),
            "assist_type": str ("pass", "head", "rebound"),
            "shot_type": str ("foot", "header"),
            "pressure": bool (defender closing down)
        }
        """
        
        # Normalize inputs
        distance_norm = min(shot_data["distance"] / 40, 1.0)  # Cap at 40 yards
        angle_norm = shot_data["angle"] / 90  # Cap at 90 degrees
        
        # Calculate base xG (simplified logistic model)
        xg_base = 1 / (1 + np.exp(distance_norm * 3 + angle_norm * 2 - 3))
        
        # Adjust for shot type
        if shot_data["shot_type"] == "foot":
            xg_base *= 1.0
        elif shot_data["shot_type"] == "header":
            xg_base *= 0.5
        
        # Adjust for pressure
        if shot_data["pressure"]:
            xg_base *= 0.8
        
        return min(xg_base, 0.95)  # Cap at 0.95

# Usage:
model = BasicXGModel()
shot = {
    "distance": 12,
    "angle": 15,
    "defender_distance": 2,
    "assist_type": "pass",
    "shot_type": "foot",
    "pressure": False
}
xg = model.calculate_xg(shot)
print(f"Expected Goals: {xg:.3f}")
```

**Better Option: Use Statsbomb Open Data**
```python
# Statsbomb provides FREE event data for select matches
# GitHub: https://github.com/statsbomb/statsbomb-python

from statsbomb.sb import StatsBomb

sb = StatsBomb()

# Get event data for Premier League matches
matches = sb.matches(competition_id=2, season_id=1)
print(f"Found {len(matches)} Premier League matches")

# Analyze events for xG
events = sb.events(match_id=matches[0]["match_id"])
shots = events[events["type"] == "Shot"]

for idx, shot in shots.iterrows():
    print(f"{shot['player']} - xG: {shot['shot']['statsbomb_xg']}")
```

**Cost:** FREE  
**Reliability:** 8/10 (limited matches but very accurate)  
**Data Source:** Statsbomb provides free data for ~200 matches/year

---

### 6.2 Poisson Distribution for Goal Prediction
**Theory:** Football goals follow Poisson distribution approximately

```python
import numpy as np
from scipy.stats import poisson
from scipy.special import comb

class PoissonGoalModel:
    """Predict match outcomes using Poisson distribution"""
    
    def __init__(self, team_stats):
        """
        team_stats: {
            "home_team": {"goals_for": X, "goals_against": Y},
            "away_team": {"goals_for": X, "goals_against": Y}
        }
        """
        self.team_stats = team_stats
    
    def calculate_team_strength(self, team_key, stat_type):
        """Calculate goals per match for team"""
        team_data = self.team_stats[team_key]
        return team_data[stat_type] / 19  # 38 PL matches per season
    
    def predict_goals(self, home_team, away_team, home_advantage=0.3):
        """Predict goal distribution for both teams"""
        
        # Attack strength (goal scoring ability)
        home_attack = self.calculate_team_strength(home_team, "goals_for")
        away_attack = self.calculate_team_strength(away_team, "goals_for")
        
        # Defense strength (goals conceded)
        home_defense = self.calculate_team_strength(home_team, "goals_against")
        away_defense = self.calculate_team_strength(away_team, "goals_against")
        
        # Expected goals (with home advantage)
        lambda_home = (home_attack * away_defense) + home_advantage
        lambda_away = (away_attack * home_defense)
        
        return lambda_home, lambda_away
    
    def predict_outcome_probabilities(self, home_team, away_team):
        """Calculate P(Home Win), P(Draw), P(Away Win)"""
        
        lambda_home, lambda_away = self.predict_goals(home_team, away_team)
        
        # Calculate probabilities for goals 0-10
        home_probs = [poisson.pmf(g, lambda_home) for g in range(11)]
        away_probs = [poisson.pmf(g, lambda_away) for g in range(11)]
        
        p_home = 0
        p_draw = 0
        p_away = 0
        
        for h_goals in range(11):
            for a_goals in range(11):
                prob = home_probs[h_goals] * away_probs[a_goals]
                
                if h_goals > a_goals:
                    p_home += prob
                elif h_goals == a_goals:
                    p_draw += prob
                else:
                    p_away += prob
        
        return {
            "home_win": p_home,
            "draw": p_draw,
            "away_win": p_away,
            "expected_home_goals": lambda_home,
            "expected_away_goals": lambda_away
        }

# Usage:
stats = {
    "Arsenal": {
        "goals_for": 88,
        "goals_against": 55
    },
    "Chelsea": {
        "goals_for": 82,
        "goals_against": 52
    }
}

model = PoissonGoalModel(stats)
probs = model.predict_outcome_probabilities("Arsenal", "Chelsea")

print(f"Arsenal win: {probs['home_win']:.1%}")
print(f"Draw: {probs['draw']:.1%}")
print(f"Chelsea win: {probs['away_win']:.1%}")
print(f"Over 2.5: {1 - (poisson.pmf(0, probs['expected_home_goals'] + probs['expected_away_goals']) + poisson.pmf(1, probs['expected_home_goals'] + probs['expected_away_goals']) + poisson.pmf(2, probs['expected_home_goals'] + probs['expected_away_goals'])):.1%}")
```

**Cost:** FREE (scipy is open source)  
**Reliability:** 7/10 (simplistic but fast)  
**Advantage:** Can be deployed in real-time with minimal computation

---

### 6.3 Python Libraries for Football Analytics
**Install:** `pip install <package>`

```
Library                  | Purpose                          | Cost  | Quality
-------------------------|-------------------------------------|-------|----------
understat-python         | xG, shot maps, advanced stats    | FREE  | 9/10
worldfootballR           | Data scraping (R/Python)         | FREE  | 8/10
socceraction             | Action sequences, VAEP           | FREE  | 8/10
matplotsoccer            | Visualization (pitch plots)      | FREE  | 8/10
football_api             | Various football APIs wrapper    | FREE  | 7/10
mplsoccer                | Advanced pitch visualizations    | FREE  | 9/10
```

**Installation:**
```bash
pip install understat-python worldfootballR socceraction matplotsoccer mplsoccer
```

**Usage:**
```python
import understat
import pandas as pd

async def get_understat_data():
    """Fetch xG and advanced stats from Understat (limited free data)"""
    
    understat_client = understat.Understat(login="your_email", password="your_password")
    
    # Understat free tier: limited data
    # But public pages can be scraped
    
    # Alternative: Use worldfootballR
    from worldfootballR import scraper
    
    # Get FBRef (Sports Reference) data
    matches = scraper.fb.FBref_Scraper().get_season_matches(season=2025, league="ENG-Premier League")
    
    return matches
```

---

## 7. HISTORICAL DATA ARCHIVES (Free, Public)

### 7.1 Kaggle Datasets
**URL:** https://www.kaggle.com/  
**What:** Community-contributed datasets (free to download)

**Top Football Datasets:**
1. **Premier League Historical Data**
   - 30 years of EPL results
   - Team stats, season summaries
   - URL: https://www.kaggle.com/datasets/maurycy/english-premier-league-seasons-7920

2. **European Soccer Database**
   - 25 years of European football
   - Players, teams, matches, goals
   - URL: https://www.kaggle.com/datasets/hugomathien/soccer

3. **Football Transfer History**
   - Transfers 2000-2020
   - Player values over time
   - URL: https://www.kaggle.com/datasets/davidcariboo/player-transfers

**Usage:**
```python
import pandas as pd
import numpy as np

# After downloading from Kaggle
matches = pd.read_csv("EPL_historical_matches.csv")

# Example: Analyze team home/away performance
home_perf = matches.groupby("HomeTeam").agg({
    "HomeGoals": "mean",
    "AwayGoals": ["mean", "count"]
}).rename(columns={"count": "matches"})

print(home_perf.sort_values("HomeGoals", ascending=False))

# Example: Calculate team statistics for Poisson model
team_stats = {}
for team in matches["HomeTeam"].unique():
    home_matches = matches[matches["HomeTeam"] == team]
    away_matches = matches[matches["AwayTeam"] == team]
    
    team_stats[team] = {
        "goals_for": home_matches["HomeGoals"].sum() + away_matches["AwayGoals"].sum(),
        "goals_against": home_matches["AwayGoals"].sum() + away_matches["HomeGoals"].sum()
    }
```

**Cost:** FREE  
**Reliability:** 8/10 (depends on dataset quality)  
**Freshness:** Updated by community, typically 1-2 seasons behind

---

### 7.2 GitHub Repositories
**Search:** `site:github.com football data`

**Top Repositories:**
1. **footballdata** (GitHub: tarasosmiyan/footballdata)
   - Clean datasets, multiple leagues
   - 20 years historical data
   - API endpoints to raw data

2. **football-stats** (GitHub: understat-projects)
   - Event data, xG models
   - Code examples

3. **soccer-analytics** (Multiple authors)
   - Analysis code, statistics
   - Machine learning models

**Clone & Use:**
```bash
git clone https://github.com/tarasosmiyan/footballdata.git
cd footballdata
# Data is in CSV format, load with pandas
```

**Cost:** FREE  
**Reliability:** 7/10 (varies by repo)

---

### 7.3 Sports Reference / StatsBomb Open Data
**URLs:**
- Football Reference: https://fbref.com/en/
- Statsbomb: https://github.com/statsbomb/StatsBomb-Event-Data

**Football Reference (FBref):**
- Team and player statistics
- Season comparisons
- Advanced metrics (xG, defensive actions, etc.)
- Completely free, public web pages

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_fbref_team_stats(team_name, season=2025):
    """Scrape FBref for team statistics"""
    
    # FBref URLs: https://fbref.com/en/squads/{team-id}/{season}/
    url = f"https://fbref.com/en/squads/{team_name.lower()}/{season}/"
    
    response = requests.get(url)
    tables = pd.read_html(response.text)
    
    # Table index varies, look for main stats table
    stats_table = tables[0]  # Usually first table
    
    return stats_table
```

**Cost:** FREE  
**Reliability:** 9/10  
**Legal:** Public data

---

## 8. MACHINE-GENERATED DATA (Free Tools)

### 8.1 Sentiment Analysis with Claude API (Limited Free)
**Option 1: Using Free Claude API Credits**
```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_FREE_TIER_KEY")

def analyze_injury_sentiment(text):
    """Use Claude to analyze injury news sentiment"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this injury news and rate sentiment:
                
Text: {text}

Respond with: POSITIVE (likely to return soon) / NEUTRAL (uncertain) / NEGATIVE (long-term concern)
Confidence: 0-100"""
            }
        ]
    )
    
    return message.content[0].text

# Example:
injury_news = "Bukayo Saka suffered ankle strain, expected to be back in 2 weeks"
sentiment = analyze_injury_sentiment(injury_news)
print(sentiment)
```

**Cost:** Limited free credits (research projects)  
**Quality:** 9/10 (Claude is excellent at language understanding)

---

### 8.2 Free Sentiment Analysis with HuggingFace
```python
from transformers import pipeline

# Download once, use offline
sentiment_pipeline = pipeline("sentiment-analysis", 
                             model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_reddit_sentiment(comments):
    """Batch analyze Reddit comments for injury consensus"""
    
    results = {}
    for comment in comments:
        result = sentiment_pipeline(comment[:512])  # Truncate to 512 tokens
        sentiment = result[0]["label"]
        confidence = result[0]["score"]
        
        if "injury" in comment.lower() or "out" in comment.lower():
            results[comment[:50]] = {
                "sentiment": sentiment,
                "confidence": confidence
            }
    
    return results

# Usage:
comments = [
    "Saliba is back in full training, looks sharp",
    "Still concerned about his ankle, doubtful for weekend",
    "Confirmed to miss next 2-3 weeks with hamstring"
]

sentiments = analyze_reddit_sentiment(comments)
for comment, data in sentiments.items():
    print(f"{comment}... -> {data['sentiment']} ({data['confidence']:.2f})")
```

**Cost:** FREE  
**Quality:** 8/10 (distilBERT is accurate enough for signal detection)

---

### 8.3 Image Recognition for Lineup Confirmation
```python
from PIL import Image
import pytesseract  # Optical Character Recognition

def extract_text_from_lineup_image(image_path):
    """Extract lineup names from official team announcements"""
    
    image = Image.open(image_path)
    
    # Extract text using Tesseract (free, open-source)
    text = pytesseract.image_to_string(image)
    
    # Parse lineup names
    lines = text.split("\n")
    lineup = [line.strip() for line in lines if line.strip() and len(line.split()) <= 3]
    
    return lineup

# Install: pip install pytesseract pillow
# Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

# Usage:
lineup = extract_text_from_lineup_image("arsenal_lineup.jpg")
print(f"Arsenal XI: {', '.join(lineup[:11])}")
```

**Cost:** FREE (Tesseract is open source)  
**Quality:** 7/10 (works well for clean images)

---

## 9. BOOTSTRAP STRATEGY: Phase-by-Phase Implementation

### Phase 1: Days 1-7 (Week 1) - Foundation APIs
**Goal:** Get real-time match data flowing

**Tasks:**
1. Register for free APIs:
   - Football-Data.org (5 min)
   - Open-Meteo (instant, no registration)
   - Get Twitter/X API keys (10 min)
   - Get Kaggle account (5 min)

2. Build data pipeline:
   ```python
   # collect_football_data.py
   
   import requests
   import schedule
   import time
   from datetime import datetime
   
   class FootballDataCollector:
       def __init__(self):
           self.fd_api_key = "YOUR_FOOTBALL_DATA_KEY"
           self.base_url = "https://www.football-data.org/api/v4"
       
       def collect_daily(self):
           """Run once daily"""
           fixtures = self.get_fixtures()
           results = self.get_results()
           standings = self.get_standings()
           
           # Save to database
           self.save_to_db({
               "fixtures": fixtures,
               "results": results,
               "standings": standings,
               "timestamp": datetime.now()
           })
       
       def get_fixtures(self):
           headers = {"X-Auth-Token": self.fd_api_key}
           response = requests.get(
               f"{self.base_url}/competitions/PL/matches",
               headers=headers,
               params={"status": "SCHEDULED"}
           )
           return response.json()
       
       def get_results(self):
           headers = {"X-Auth-Token": self.fd_api_key}
           response = requests.get(
               f"{self.base_url}/competitions/PL/matches",
               headers=headers,
               params={"status": "FINISHED"}
           )
           return response.json()
       
       def get_standings(self):
           headers = {"X-Auth-Token": self.fd_api_key}
           response = requests.get(
               f"{self.base_url}/competitions/PL/standings",
               headers=headers
           )
           return response.json()
       
       def save_to_db(self, data):
           # Save to JSON or database
           import json
           with open(f"football_data_{datetime.now().date()}.json", "w") as f:
               json.dump(data, f, indent=2, default=str)
   
   # Run daily
   if __name__ == "__main__":
       collector = FootballDataCollector()
       schedule.every().day.at("12:00").do(collector.collect_daily)
       
       while True:
           schedule.run_pending()
           time.sleep(60)
   ```

3. First deliverable: "Fixture Analyzer" - simple CLI showing:
   - Upcoming fixtures (next 7 days)
   - Team form (last 5 results)
   - Head-to-head records

**Revenue:** Sell fixture analysis + predictions (even simple ones)

**Time:** 2-3 hours to build

---

### Phase 2: Days 8-14 (Week 2) - Web Scraping + Community Data
**Goal:** Add depth with injury news and sentiment

**Tasks:**
1. Set up Reddit scraping:
   ```python
   import praw
   import sqlite3
   
   reddit = praw.Reddit(client_id="...", client_secret="...", user_agent="...")
   
   def monitor_injuries():
       subreddit = reddit.subreddit("FantasyPL")
       
       for submission in subreddit.hot(limit=30):
           if "injury" in submission.title.lower():
               # Extract player names
               extract_player_mentions(submission.title)
               # Save to DB
               save_to_db(submission.title)
   ```

2. Scrape Transfermarkt injuries:
   ```python
   # See Section 3.4 above - monitor injury lists daily
   ```

3. Add weather data to fixtures:
   ```python
   # For each match, fetch weather forecast
   # Store wind_speed, precipitation, temperature
   ```

**Revenue:** "Injury Alert System" - notify users of player status changes

**Time:** 4-6 hours

---

### Phase 3: Days 15-21 (Week 3) - ML Models & Predictions
**Goal:** Generate betting recommendations

**Tasks:**
1. Build Poisson model with collected data:
   ```python
   # See Section 6.2 above
   ```

2. Train xG model from historical data:
   ```python
   # Use Kaggle datasets to train basic model
   ```

3. Generate match predictions:
   ```python
   def generate_predictions():
       model = PoissonGoalModel(team_stats)
       
       for fixture in upcoming_fixtures:
           probs = model.predict_outcome_probabilities(
               fixture["home_team"],
               fixture["away_team"]
           )
           
           # Compare to market odds
           market_odds = get_current_odds(fixture)
           
           # Find value bets (where model > market)
           if probs["home_win"] > 1 / market_odds["home"]:
               print(f"VALUE: {fixture['home_team']} at {market_odds['home']}")
   ```

**Revenue:** "Prediction API" - sell match outcomes + expected goals

**Time:** 8-10 hours

---

### Phase 4: Month 2+ (Scaling)
**As revenue grows, strategically add paid sources:**

**Low Cost, High Value:**
- (**$49/month**) API-Football Premium: 100k requests/day
- (**$29/month**) Odds API: Better odds data
- (**$99/month**) Understat premium: Detailed xG + tactical heat maps

**Decision Rule:**
- If revenue > $500/month → Add API-Football Premium
- If revenue > $1000/month → Add Understat Premium
- If betting volume > $10k/day → Add Betfair API

---

## 10. PRIORITY MATRIX: Value vs. Effort

```
HIGH VALUE + FREE:
├─ Football-Data.org API             [Critical]
├─ Open-Meteo weather                [Critical]
├─ Transfermarkt injury lists        [Critical]
├─ Premier League official site      [Critical]
└─ FBref statistics                  [Important]

HIGH VALUE + MODERATE EFFORT:
├─ Reddit sentiment (r/FantasyPL)    [Important]
├─ Poisson model implementation      [Important]
├─ Odds Portal scraping              [Important]
├─ Injury news aggregation           [Important]
└─ Twitter/X sentiment               [Important]

NICE TO HAVE + LOW EFFORT:
├─ Kaggle datasets (historical)      [Nice]
├─ RSS feed aggregation              [Nice]
├─ Sky Sports/BBC scraping           [Nice]
└─ Team official websites            [Nice]

IGNORE (Low Value, High Effort):
├─ Facebook scraping (limited data)
├─ Instagram comment sentiment
├─ YouTube thumbnail analysis
└─ Advanced computer vision
```

---

## 11. IMPLEMENTATION EXAMPLES: Putting It Together

### 11.1 Complete Data Pipeline (Orchestration)
```python
# orchestrator.py - Central nervous system

import schedule
import logging
from datetime import datetime
import sqlite3
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataOrchestrator:
    def __init__(self):
        self.db = self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect("football_data.db")
        c = conn.cursor()
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS fixtures (
            id INTEGER PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            date TEXT,
            status TEXT,
            home_goals INTEGER,
            away_goals INTEGER
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS injuries (
            id INTEGER PRIMARY KEY,
            player TEXT,
            team TEXT,
            status TEXT,
            expected_return DATE,
            source TEXT,
            timestamp DATETIME
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            p_home REAL,
            p_draw REAL,
            p_away REAL,
            expected_goals REAL,
            model TEXT,
            timestamp DATETIME
        )
        """)
        
        conn.commit()
        return conn
    
    def run_daily_tasks(self):
        """Master schedule for all data collection"""
        
        logger.info("Starting daily data collection...")
        
        # 6 AM: Collect fixtures and standings
        self.collect_fixtures_and_standings()
        
        # 8 AM: Check injuries
        self.monitor_injuries()
        
        # 10 AM: Scrape team news
        self.scrape_team_news()
        
        # 2 PM: Get updated odds
        self.collect_odds()
        
        # 4 PM: Generate predictions
        self.generate_match_predictions()
        
        # 6 PM: Monitor Reddit sentiment
        self.monitor_reddit_sentiment()
        
        logger.info("Daily collection complete")
    
    def collect_fixtures_and_standings(self):
        from collectors import FootballDataCollector
        
        collector = FootballDataCollector()
        fixtures = collector.get_fixtures()
        standings = collector.get_standings()
        
        logger.info(f"Collected {len(fixtures['matches'])} fixtures")
        self.save_fixtures(fixtures)
        self.save_standings(standings)
    
    def monitor_injuries(self):
        from collectors import TransfermarktScraper, RedditScraper
        
        # Transfermarkt
        scraper = TransfermarktScraper()
        injuries = scraper.get_all_team_injuries()
        
        # Reddit confirmation
        reddit_scraper = RedditScraper()
        reddit_signals = reddit_scraper.extract_injury_signals()
        
        self.save_injuries(injuries, source="transfermarkt")
        self.save_injuries(reddit_signals, source="reddit")
        
        logger.info(f"Monitored injury status for {len(injuries)} players")
    
    def scrape_team_news(self):
        from collectors import TeamNewsScraper
        
        scraper = TeamNewsScraper()
        for team_id, team_name in enumerate(self.get_pl_teams()):
            news = scraper.get_team_news(team_id)
            self.save_news(team_name, news)
    
    def collect_odds(self):
        from collectors import OddsCollector
        
        collector = OddsCollector()
        odds = collector.get_current_odds()
        
        logger.info(f"Collected odds for {len(odds)} bookmakers")
        self.save_odds(odds)
    
    def generate_match_predictions(self):
        from models import PoissonModel
        
        model = PoissonModel(team_stats=self.get_team_stats())
        fixtures = self.get_upcoming_fixtures()
        
        for fixture in fixtures:
            if fixture["date"] <= 3:  # Only next 3 days
                probs = model.predict(fixture["home"], fixture["away"])
                self.save_prediction(fixture, probs)
        
        logger.info(f"Generated predictions for {len(fixtures)} matches")
    
    def monitor_reddit_sentiment(self):
        from collectors import RedditScraper
        
        scraper = RedditScraper()
        sentiments = scraper.get_sentiment_summary()
        
        self.save_sentiment(sentiments)
    
    # Helper methods
    def save_fixtures(self, fixtures):
        for match in fixtures["matches"]:
            self.db.execute("""
            INSERT OR REPLACE INTO fixtures
            (home_team, away_team, date, status)
            VALUES (?, ?, ?, ?)
            """, (
                match["homeTeam"]["name"],
                match["awayTeam"]["name"],
                match["utcDate"],
                match["status"]
            ))
        self.db.commit()
    
    def get_pl_teams(self):
        """Return list of Premier League teams"""
        return [
            "Arsenal", "Aston Villa", "Bournemouth", "Brighton", "Chelsea",
            "Crystal Palace", "Everton", "Fulham", "Ipswich", "Leicester City",
            "Liverpool", "Manchester City", "Manchester United", "Newcastle United",
            "Nottingham Forest", "Southampton", "Tottenham", "West Ham", "Wolverhampton",
            "Brentford"
        ]
    
    def get_team_stats(self):
        """Load team statistics from database"""
        # Return pre-loaded stats for Poisson model
        return {}
    
    def get_upcoming_fixtures(self):
        cursor = self.db.execute("""
        SELECT * FROM fixtures
        WHERE status = 'SCHEDULED'
        ORDER BY date ASC
        LIMIT 20
        """)
        return cursor.fetchall()
    
    def save_prediction(self, fixture, probs):
        self.db.execute("""
        INSERT INTO predictions
        (home_team, away_team, p_home, p_draw, p_away, expected_goals, model, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fixture["home"], fixture["away"],
            probs["home_win"], probs["draw"], probs["away_win"],
            probs["expected_goals"], "poisson", datetime.now()
        ))
        self.db.commit()

# Main execution
if __name__ == "__main__":
    orchestrator = DataOrchestrator()
    
    # Schedule daily tasks
    schedule.every().day.at("06:00").do(orchestrator.run_daily_tasks)
    
    # Also run immediately on startup
    orchestrator.run_daily_tasks()
    
    # Keep scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)
```

---

### 11.2 Prediction API Endpoint
```python
# api.py - Serve predictions to betting system

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route("/api/predictions/<date>", methods=["GET"])
def get_predictions(date):
    """Get match predictions for a specific date"""
    
    conn = sqlite3.connect("football_data.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
    SELECT * FROM predictions
    WHERE DATE(timestamp) = ?
    ORDER BY p_home DESC
    """, (date,))
    
    predictions = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # Format for API
    return jsonify({
        "date": date,
        "predictions": predictions,
        "count": len(predictions)
    })

@app.route("/api/injuries/<team>", methods=["GET"])
def get_team_injuries(team):
    """Get current injuries for a team"""
    
    conn = sqlite3.connect("football_data.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
    SELECT DISTINCT player, status, expected_return, source
    FROM injuries
    WHERE team = ?
    AND timestamp = (SELECT MAX(timestamp) FROM injuries WHERE team = ?)
    """, (team, team))
    
    injuries = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({
        "team": team,
        "injuries": injuries,
        "count": len(injuries)
    })

@app.route("/api/odds/<match_id>", methods=["GET"])
def get_match_odds(match_id):
    """Get best odds for a match from all bookmakers"""
    
    # This would query aggregated odds data
    # Implementation depends on your odds collection strategy
    
    return jsonify({
        "match_id": match_id,
        "best_odds": {
            "home": 1.95,
            "draw": 3.50,
            "away": 4.20,
            "bookmaker": "Betfair"
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

---

## 12. RISK ASSESSMENT: Reliability Scorecard

```
SOURCE                          | RELIABILITY | FRESHNESS | COVERAGE | NOTES
--------------------------------|-------------|-----------|----------|---
Football-Data.org              |    9/10     | 5-15 min  |   PL     | CRITICAL PATH
Open-Meteo                     |   10/10     | Real-time | Worldwide| Never fails
Twitter API                    |    8/10     | Real-time | All      | Rate limits
Reddit praw                    |    8/10     | Real-time | All      | API changes
Transfermarkt                  |    9/10     | Daily     | All      | Best injury data
FBref scraping                 |    8/10     | Weekly    | All      | Slow updates
API-Football                   |    8/10     | Real-time | PL       | Rate limited (free)
Kaggle datasets                |    7/10     | Monthly   | Historic | Depends on uploader
OddsPortal scraping            |    7/10     | Real-time | All      | ToS dependent
RSS feeds                      |    8/10     | 15-60 min | All      | Lag on breaking news
--------------------------------|-------------|-----------|----------|---
COMBINED PIPELINE              |    9/10     | Real-time | PL       | Redundancy across sources
```

**Resilience Strategy:**
1. **Dual sources for critical data** (e.g., Football-Data + API-Football)
2. **Cache layer** (store last 24h of data locally)
3**Fallback to historical averages** if source fails
4. **Alert on data gaps** (log and notify)

---

## 13. BOOTSTRAPPING ROADMAP

### Week 1: Foundation
- [ ] Register for all free APIs
- [ ] Build basic data collector
- [ ] Set up database
- [ ] Deploy to server (e.g., Heroku free tier)
- [ ] First dashboard: Fixtures + standings
- **Revenue Goal:** $0 (establishing credibility)

### Week 2: Enhance Data
- [ ] Add scraping (Transfermarkt, team sites)
- [ ] Implement Reddit monitoring
- [ ] Create injury alert system
- [ ] Build CLI tool for subscribers
- **Revenue Goal:** $50-100/week (manual tips)

### Week 3: Predict
- [ ] Deploy Poisson model
- [ ] Generate match predictions
- [ ] Create prediction API
- [ ] Compare to market odds (value detection)
- **Revenue Goal:** $200-300/week (prediction subscribers)

### Week 4+: Scale
- [ ] Add betting recommendations
- [ ] Automated cron jobs
- [ ] Telegram/Slack alerts
- [ ] Monthly subscription ($9.99-19.99)
- **Revenue Goal:** $500-1000+/month
- **Then:** Invest back into paid APIs

---

## 14. COST ANALYSIS: Bootstrap vs. Paid

```
FREE BOOTSTRAP (Month 1):
├─ Servers:           $0 (Heroku free / your own machine)
├─ APIs:              $0 (all free tiers)
├─ Databases:         $0 (SQLite / free cloud)
├─ Time:              40 hours (1 week full-time)
└─ TOTAL:             $0

PAID APIS (Month 2, if revenue > $500):
├─ API-Football:      $49/month
├─ Understat:         $99/month
├─ Betfair API:       $100+/month (if betting)
└─ Total if all 3:    $248/month

ROI CALCULATION:
If you charge $9.99/month per customer:
- Break-even: 25 customers (covers all paid APIs)
- Profit threshold: 50+ customers ($500/month - $250 costs)
- With good product: 200+ customers achievable in 6 months
```

---

## 15. LEGAL & ETHICAL CONSIDERATIONS

### What's Legal:
✅ Scraping **public data** (not behind login)  
✅ Scraping **published news** (RSS feeds, websites)  
✅ Using **free API tiers** (within rate limits)  
✅ **Transforming data** (creating new value from public info)  
✅ **Betting on predictions** (in jurisdictions allowing it)  

### What Requires Caution:
⚠️ Scraping at **excessive frequency** (causes server load)  
⚠️ Using **competitor's APIs** without permission  
⚠️ Betting **without proper licensing** in your jurisdiction  
⚠️ Using **copyrighted statistical models** without attribution  
⚠️ **Misleading customers** about data sources or accuracy

### ToS Compliance:
- **Football-Data.org:** Scraping allowed, attribute properly
- **Transfermarkt:** Scraping allowed (be respectful on rate limits)
- **Twitter/X:** API v2 allows 450k tweets/month free
- **Kaggle:** Datasets are open, check individual licenses
- **Reddit:** praw library follows ToS, no aggressive scraping

### Recommendation:
Start with APIs and public data sources, avoid aggressive scraping until you understand the legal landscape in your jurisdiction.

---

## CONCLUSION: The Path Forward

**You can bootstrap a complete sports data system for $0 with:**

1. **Real-time fixture data** → Football-Data.org
2. **Team news & injuries** → Transfermarkt + team websites + Reddit
3. **Weather integration** → Open-Meteo
4. **Statistical models** → Poisson + xG (open source)
5. **Predictions** → Compare to market odds
6. **Revenue generation** → Sell predictions + alerts

**Timeline: Days to launch**, not months.

**Economics:** Reinvest early revenue ($500+) into paid APIs for better data quality, then scale.

**Key insight:** Most valuable sports data is *already free*. The competitive advantage is in:
- Data integration (combining multiple sources)
- Model quality (better predictions than bookmakers)
- Speed (faster updates than competitors)
- Niche expertise (knowing which signals matter)

Start now. Move fast. Iterate with real data.

---

**Document Last Updated:** August 2026  
**Status:** Ready for implementation  
**Next Step:** Choose Week 1 tasks and begin building
