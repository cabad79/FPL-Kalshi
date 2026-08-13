"""External data integration: Understat, Reddit, SofaScore."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class UnderstatData:
    """Expected Goals and Assists from Understat."""

    player_id: int
    player_name: str
    team: str
    position: str
    xg: float  # Expected Goals
    xa: float  # Expected Assists
    xg_per_90: float
    xa_per_90: float
    last_updated: str


@dataclass
class RedditAlert:
    """Injury alert from r/FantasyPL."""

    player_id: int
    player_name: str
    team: str
    alert_type: str  # "injury", "suspension", "rotation_risk", "positive_news"
    severity: int  # 1-5, where 5 is critical
    source_url: str
    posted_at: str
    content: str


class UnderstatService:
    """Fetch xG/xA data from Understat.

    Note: Understat web scraping requires BeautifulSoup4 or Selenium.
    This is a skeleton implementation; production use requires API key.

    Installation:
        pip install beautifulsoup4 requests
    """

    BASE_URL = "https://understat.com/api"

    @staticmethod
    def get_player_stats(player_name: str, team: str) -> dict[str, Any] | None:
        """Get xG/xA stats for a player from Understat.

        Args:
            player_name: Player's full name.
            team: Team short code (e.g., 'MUN', 'ARS').

        Returns:
            Dict with xG, xA, and per-90 metrics, or None if not found.

        Example:
            >>> stats = UnderstatService.get_player_stats("Bruno Fernandes", "MUN")
            >>> stats["xg"]  # 2.5
            >>> stats["xa"]  # 1.2
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning(
                "Understat integration requires: pip install beautifulsoup4 requests"
            )
            return None

        # In production, use Understat API with authentication
        # For now, this is a web scrape skeleton
        # Real implementation would call: GET /api/league/epl/
        # with specific season and match filters

        logger.info(f"Fetching Understat data for {player_name} ({team})")

        # Placeholder: return None (requires actual API integration)
        return None

    @staticmethod
    def calculate_xg_boost(player_stats: dict[str, float]) -> float:
        """Boost expected points using xG/xA metrics.

        Args:
            player_stats: Dict with xg, xa, xg_per_90, xa_per_90.

        Returns:
            Adjusted ep_next multiplier (e.g., 1.15 = +15% boost).
        """
        if not player_stats:
            return 1.0

        xg = player_stats.get("xg", 0)
        xa = player_stats.get("xa", 0)
        xg_per_90 = player_stats.get("xg_per_90", 0)

        # Formula: Boost if xG is high relative to expected
        # ep_next += (xg * 0.5) + (xa * 1.0)
        boost = 1.0 + (xg * 0.05) + (xa * 0.10)

        return min(boost, 1.5)  # Cap at +50% boost


class RedditService:
    """Fetch injury alerts from r/FantasyPL.

    Installation:
        pip install praw
    """

    SUBREDDIT = "FantasyPL"
    ALERT_KEYWORDS = ["injury", "out", "ruled out", "suspended", "positive news", "return"]

    @staticmethod
    def get_injury_alerts(hours: int = 48) -> list[RedditAlert]:
        """Get recent injury alerts from r/FantasyPL.

        Args:
            hours: Lookback window (default 48h before deadline).

        Returns:
            List of alerts sorted by recency.

        Example:
            >>> alerts = RedditService.get_injury_alerts(hours=48)
            >>> alerts[0].player_name  # "Harry Kane"
            >>> alerts[0].severity  # 5
        """
        try:
            import praw
        except ImportError:
            logger.warning(
                "Reddit integration requires: pip install praw\n"
                "Also set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET env vars"
            )
            return []

        # In production:
        # reddit = praw.Reddit(
        #     client_id=os.getenv("REDDIT_CLIENT_ID"),
        #     client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        #     user_agent="fpl-mcp-v1"
        # )
        # subreddit = reddit.subreddit(RedditService.SUBREDDIT)

        logger.info(f"Fetching injury alerts from r/{RedditService.SUBREDDIT}")

        # Placeholder: return empty list (requires PRAW authentication)
        return []

    @staticmethod
    def parse_alert_severity(content: str) -> int:
        """Parse alert severity from post content.

        Args:
            content: Post text.

        Returns:
            Severity 1-5 (5 = critical, likely to miss next GW).
        """
        content_lower = content.lower()

        # Critical severity keywords
        critical = ["ruled out", "will miss", "6 weeks", "out for season"]
        if any(keyword in content_lower for keyword in critical):
            return 5

        # High severity
        high = ["doubt", "likely miss", "2-3 weeks", "significant"]
        if any(keyword in content_lower for keyword in high):
            return 4

        # Medium severity
        medium = ["minor", "1-2 weeks", "expected back"]
        if any(keyword in content_lower for keyword in medium):
            return 3

        # Low severity (positive news)
        low = ["positive", "back", "training", "no concerns"]
        if any(keyword in content_lower for keyword in low):
            return 2

        return 1  # Unknown

    @staticmethod
    def apply_injury_penalty(player_ep_next: float, injury_probability: float) -> float:
        """Apply injury risk penalty to ep_next.

        Args:
            player_ep_next: Original expected points.
            injury_probability: 0-1 probability of missing GW.

        Returns:
            Adjusted ep_next.
        """
        # Expected points if plays: ep_next
        # Expected points if benched: 0
        # Weighted average: ep_next * (1 - injury_probability)

        return player_ep_next * (1 - injury_probability)


class OwnershipService:
    """Ownership-based contrarian analysis."""

    @staticmethod
    def calculate_contrarian_score(
        player_ownership_pct: float,
        player_ep_next: float,
        contrarian_mode: bool = True,
    ) -> float:
        """Calculate ownership-adjusted expected points.

        Args:
            player_ownership_pct: Selected by % (0-100).
            player_ep_next: Base expected points.
            contrarian_mode: If True, fade high-ownership players.

        Returns:
            Adjusted ep_next with ownership factor.
        """
        if not contrarian_mode:
            return player_ep_next

        # Contrarian adjustment: penalize heavily-owned players
        # Formula: ep_next * (1 - (ownership/100) * 0.3)
        # At 50% ownership: ep_next * 0.85 (15% penalty)
        # At 100% ownership: ep_next * 0.70 (30% penalty)

        ownership_factor = 1.0 - ((player_ownership_pct / 100) * 0.3)
        return player_ep_next * max(ownership_factor, 0.5)  # Floor at -50%

    @staticmethod
    def identify_differential_picks(
        squad: list[Any],
        avg_ownership: float = 25.0,
    ) -> list[dict[str, Any]]:
        """Identify low-ownership differential picks in squad.

        Args:
            squad: List of Player objects.
            avg_ownership: Ownership threshold (default 25%).

        Returns:
            List of low-ownership players with upside.
        """
        differentials = []
        for player in squad:
            ownership = float(player.selected_by_percent or 0)
            if ownership < avg_ownership:
                differentials.append(
                    {
                        "name": player.web_name,
                        "ownership": ownership,
                        "ep_next": float(player.ep_next or 0),
                        "upside": "High",
                    }
                )

        return sorted(differentials, key=lambda x: x["ownership"])


class GameweekService:
    """Handle double gameweeks (DGW) and blank gameweeks (BGW)."""

    @staticmethod
    def detect_special_gameweeks(
        fixtures: list[Any],
        teams: dict[int, Any],
    ) -> dict[int, str]:
        """Detect double gameweeks (DGW) and blank gameweeks (BGW).

        Args:
            fixtures: List of Fixture objects for the gameweek.
            teams: Dict of Team objects.

        Returns:
            Dict mapping team_id -> "dgw", "bgw", or "normal".
        """
        gameweek_status = {}

        # Count fixtures per team this gameweek
        fixture_count = {}
        for fixture in fixtures:
            fixture_count[fixture.team_h] = fixture_count.get(fixture.team_h, 0) + 1
            fixture_count[fixture.team_a] = fixture_count.get(fixture.team_a, 0) + 1

        for team_id, count in fixture_count.items():
            if count == 2:
                gameweek_status[team_id] = "dgw"  # Double gameweek
            elif count == 0:
                gameweek_status[team_id] = "bgw"  # Blank gameweek
            else:
                gameweek_status[team_id] = "normal"

        return gameweek_status

    @staticmethod
    def calculate_dgw_bonus(
        player_ep_next: float,
        team_status: str,
    ) -> float:
        """Adjust ep_next for DGW/BGW.

        Args:
            player_ep_next: Original expected points.
            team_status: "dgw", "bgw", or "normal".

        Returns:
            Adjusted ep_next.
        """
        if team_status == "dgw":
            # Double gameweek: ~1.5x points opportunity
            return player_ep_next * 1.5
        elif team_status == "bgw":
            # Blank gameweek: player unavailable
            return 0.0
        else:
            return player_ep_next
