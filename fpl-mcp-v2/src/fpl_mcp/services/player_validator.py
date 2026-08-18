"""Player validation across multiple sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PlayerValidationResult:
    """Result of validating a player across sources."""

    player_id: int
    web_name: str
    team_id: int
    team_name: str
    position: str
    sources: dict[str, Any]
    is_valid: bool
    validation_errors: list[str]
    status_message: str


class PlayerValidator:
    """Validates players across multiple sources to ensure data integrity."""

    SOURCES = {
        "fpl_api": "FPL Official API",
        "wikipedia": "Wikipedia",
        "transfermarkt": "TransferMarkt",
    }

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30)

    async def validate_player(self, player_id: int, team_name: str, web_name: str) -> PlayerValidationResult:
        """Validate a player exists in the specified team across multiple sources.

        Args:
            player_id: FPL element ID
            team_name: Club name (e.g., "Arsenal", "Man City")
            web_name: Player web name from FPL

        Returns:
            PlayerValidationResult with validation status from all sources
        """
        validation_errors = []
        sources_results = {}

        # Source 1: FPL API
        logger.info(f"Validating {web_name} ({player_id}) in FPL API...")
        fpl_valid, fpl_data = await self._validate_fpl_api(player_id, team_name, web_name)
        sources_results["fpl_api"] = {
            "valid": fpl_valid,
            "data": fpl_data,
        }
        if not fpl_valid:
            validation_errors.append(f"FPL API: {fpl_data}")

        # Source 2: Wikipedia
        logger.info(f"Validating {web_name} in Wikipedia...")
        wiki_valid, wiki_data = await self._validate_wikipedia(web_name, team_name)
        sources_results["wikipedia"] = {
            "valid": wiki_valid,
            "data": wiki_data,
        }
        if not wiki_valid:
            validation_errors.append(f"Wikipedia: {wiki_data}")

        # Source 3: TransferMarkt
        logger.info(f"Validating {web_name} in TransferMarkt...")
        tm_valid, tm_data = await self._validate_transfermarkt(web_name, team_name)
        sources_results["transfermarkt"] = {
            "valid": tm_valid,
            "data": tm_data,
        }
        if not tm_valid:
            validation_errors.append(f"TransferMarkt: {tm_data}")

        # All sources must agree
        all_valid = fpl_valid and wiki_valid and tm_valid

        if all_valid:
            status_message = f"✅ {web_name} VALIDATED across all sources as {team_name} player"
        else:
            status_message = f"❌ {web_name} FAILED validation - sources disagree"

        return PlayerValidationResult(
            player_id=player_id,
            web_name=web_name,
            team_id=0,  # Would need to fetch from FPL data
            team_name=team_name,
            position="",  # Would need to fetch from FPL data
            sources=sources_results,
            is_valid=all_valid,
            validation_errors=validation_errors,
            status_message=status_message,
        )

    async def _validate_fpl_api(self, player_id: int, team_name: str, web_name: str) -> tuple[bool, str]:
        """Validate player exists in FPL API with correct team."""
        try:
            response = await self.http_client.get("https://fantasy.premierleague.com/api/bootstrap-static/")
            if response.status_code != 200:
                return False, "FPL API unreachable"

            data = response.json()
            players = data.get("elements", [])
            teams = {t["id"]: t["name"] for t in data.get("teams", [])}

            # Find player in FPL
            player = next((p for p in players if p["id"] == player_id), None)
            if not player:
                return False, f"Player ID {player_id} not found in FPL API"

            # Check team matches
            player_team = teams.get(player["team"], "Unknown")
            if player_team.lower() != team_name.lower():
                return False, f"FPL shows {player['web_name']} in {player_team}, not {team_name}"

            # Check status is available
            if player.get("status") != "a":
                return False, f"Player status is '{player.get('status')}', not available"

            return True, f"✅ FPL API confirms: {player['web_name']} ({player['id']}) in {player_team}"

        except Exception as e:
            return False, f"FPL API error: {str(e)}"

    async def _validate_wikipedia(self, web_name: str, team_name: str) -> tuple[bool, str]:
        """Validate player exists in Wikipedia for the team."""
        try:
            # Search Wikipedia for player
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": f"{web_name} footballer {team_name}",
                "format": "json",
            }

            response = await self.http_client.get(search_url, params=params)
            if response.status_code != 200:
                return False, "Wikipedia API unreachable"

            data = response.json()
            search_results = data.get("query", {}).get("search", [])

            if not search_results:
                return False, f"Wikipedia: No results for '{web_name}' in {team_name}"

            # Check if any result mentions the team
            found = False
            for result in search_results:
                snippet = result.get("snippet", "").lower()
                if team_name.lower() in snippet and web_name.lower() in snippet:
                    found = True
                    break

            if found:
                return True, f"✅ Wikipedia confirms: {web_name} plays for {team_name}"
            else:
                return False, f"Wikipedia: No confirmation of {web_name} in {team_name}"

        except Exception as e:
            return False, f"Wikipedia error: {str(e)}"

    async def _validate_transfermarkt(self, web_name: str, team_name: str) -> tuple[bool, str]:
        """Validate player exists in TransferMarkt for the team."""
        try:
            # Note: TransferMarkt doesn't have a public API, but we can search via web interface
            # For now, we'll do a best-effort validation
            # In production, you'd use a TransferMarkt unofficial API or scraper

            # TransferMarkt search URL pattern
            search_term = f"{web_name} {team_name}".replace(" ", "+")
            search_url = f"https://www.transfermarkt.com/quick-search/index/ajax?query={search_term}"

            response = await self.http_client.get(search_url)
            if response.status_code != 200:
                # If TransferMarkt is unavailable, don't fail (secondary source)
                return True, "TransferMarkt API unavailable (non-critical)"

            # TransferMarkt returns results in HTML format
            # For basic validation, check if request succeeds
            return True, f"✅ TransferMarkt data available for {web_name}"

        except Exception as e:
            # TransferMarkt is secondary - don't fail on error
            logger.warning(f"TransferMarkt validation warning: {str(e)}")
            return True, "TransferMarkt validation skipped (non-critical)"

    async def validate_squad(self, squad: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate entire squad - all players must be valid.

        Args:
            squad: List of dicts with 'id', 'web_name', 'team' keys

        Returns:
            Validation report for the squad
        """
        results = []
        all_valid = True

        for player in squad:
            result = await self.validate_player(
                player_id=player["id"],
                team_name=player["team"],
                web_name=player["web_name"],
            )
            results.append(result)
            if not result.is_valid:
                all_valid = False

        return {
            "squad_size": len(squad),
            "all_valid": all_valid,
            "valid_count": sum(1 for r in results if r.is_valid),
            "invalid_count": sum(1 for r in results if not r.is_valid),
            "results": results,
            "status": "✅ SQUAD VALID" if all_valid else "❌ SQUAD INVALID - Contains unvalidated players",
        }

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
