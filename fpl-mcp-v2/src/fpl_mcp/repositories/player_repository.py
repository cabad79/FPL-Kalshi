"""Player repository with in-memory inverted index and fuzzy name search.

O(1) lookups by ID, fast fuzzy search via inverted token index.
"""

from __future__ import annotations

from typing import Any

from fpl_mcp.domain.player import Player
from fpl_mcp.infrastructure.cache import CacheTier, TieredCache
from fpl_mcp.infrastructure.fpl_client import FPLClient
from fpl_mcp.repositories.bootstrap_repository import BootstrapRepository
from fpl_mcp.utils.nicknames import NICKNAMES


class PlayerRepository:
    """Player data with in-memory indexing.

    Indexes are built lazily on first access and invalidated when
    the underlying bootstrap cache is refreshed.
    """

    _SUMMARY_TTL = 1800

    def __init__(self, client: FPLClient, cache: TieredCache) -> None:
        self._client = client
        self._cache = cache
        self._bootstrap_repo = BootstrapRepository(client, cache)
        # In-memory indices (rebuilt on cache miss / invalidation)
        self._by_id: dict[int, Player] = {}
        self._by_team: dict[int, list[Player]] = {}
        self._by_position: dict[str, list[Player]] = {}
        # Inverted token index: token -> set of player IDs
        self._inverted_index: dict[str, set[int]] = {}
        self._index_built = False

    def _position_from_element_type(self, element_type: int) -> str:
        """Map element_type int to FPL position code."""
        mapping = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return mapping.get(element_type, "UNK")

    def _tokenize(self, text: str) -> list[str]:
        """Normalize and tokenize a name for indexing."""
        return text.lower().strip().split()

    def _build_indices(self, players: list[Player]) -> None:
        """Build all in-memory indices from a player list."""
        self._by_id = {}
        self._by_team = {}
        self._by_position = {}
        self._inverted_index = {}

        for player in players:
            self._by_id[player.id] = player

            # Team index
            self._by_team.setdefault(player.team_id, []).append(player)

            # Position index
            pos = self._position_from_element_type(player.element_type)
            self._by_position.setdefault(pos, []).append(player)

            # Inverted name index
            tokens: set[str] = set()
            tokens.update(self._tokenize(player.first_name))
            tokens.update(self._tokenize(player.second_name))
            tokens.update(self._tokenize(player.web_name))
            tokens.update(self._tokenize(player.full_name))

            # Nickname index
            for nick, resolved in NICKNAMES.items():
                if resolved in player.full_name.lower():
                    tokens.add(nick.lower())

            for token in tokens:
                self._inverted_index.setdefault(token, set()).add(player.id)

        self._index_built = True

    async def _get_players(self) -> list[Player]:
        """Get all players, building indices if needed."""
        bootstrap = await self._bootstrap_repo.get_bootstrap()
        players = bootstrap.elements
        if not self._index_built:
            self._build_indices(players)
        return players

    async def get_all(self) -> list[Player]:
        """Get all players, cached via bootstrap."""
        return await self._get_players()

    async def get_by_id(self, player_id: int) -> Player | None:
        """O(1) lookup by player ID."""
        await self._get_players()  # Ensure indices are built
        return self._by_id.get(player_id)

    async def search_by_name(self, query: str, limit: int = 5) -> list[Player]:
        """Fuzzy name search with scoring.

        Scoring priority:
        1. Exact full/web name match (highest)
        2. Exact token match
        3. Prefix match
        4. Substring match

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of players ordered by relevance score.
        """
        players = await self._get_players()
        query_lower = query.lower().strip()
        query_tokens = self._tokenize(query_lower)

        # Check if query is a known nickname
        if query_lower in NICKNAMES:
            resolved = NICKNAMES[query_lower]
            query_tokens = self._tokenize(resolved)

        # Candidate IDs from inverted index
        candidate_ids: set[int] = set()
        for token in query_tokens:
            if token in self._inverted_index:
                if not candidate_ids:
                    candidate_ids = set(self._inverted_index[token])
                else:
                    candidate_ids &= self._inverted_index[token]

        # If no intersection, union all matching tokens
        if not candidate_ids:
            for token in query_tokens:
                candidate_ids |= self._inverted_index.get(token, set())

        # Fallback: if still no candidates, scan all players
        if not candidate_ids:
            candidate_ids = {p.id for p in players}

        # Score candidates
        scored: list[tuple[float, Player]] = []
        for pid in candidate_ids:
            player = self._by_id[pid]
            score = 0.0

            names_to_check = [
                player.full_name.lower(),
                player.web_name.lower(),
                f"{player.first_name} {player.second_name}".lower(),
            ]

            # Exact match
            if any(query_lower == name for name in names_to_check):
                score += 100.0
            # Prefix match
            elif any(name.startswith(query_lower) for name in names_to_check):
                score += 50.0
            # Substring match
            elif any(query_lower in name for name in names_to_check):
                score += 25.0

            # Token matches
            for token in query_tokens:
                if token in self._inverted_index and pid in self._inverted_index[token]:
                    score += 10.0

            scored.append((score, player))

        scored.sort(key=lambda x: (-x[0], x[1].web_name))
        return [player for _, player in scored[:limit]]

    async def get_by_team(self, team_id: int) -> list[Player]:
        """Get all players for a given team ID."""
        await self._get_players()
        return self._by_team.get(team_id, [])

    async def get_by_position(self, position: str) -> list[Player]:
        """Get all players for a given position code (GKP/DEF/MID/FWD)."""
        await self._get_players()
        return self._by_position.get(position.upper(), [])

    async def get_summary(self, player_id: int) -> dict[str, Any]:
        """Get element-summary for a player.

        Cached with a shorter TTL than bootstrap since it changes more frequently.
        """
        cache_key = f"player_summary:{player_id}"

        async def _fetch() -> dict[str, Any]:
            return await self._client.get_player_summary(player_id)

        return await self._cache.get_or_fetch(
            cache_key,
            _fetch,
            tier=CacheTier.PUBLIC,
            ttl=self._SUMMARY_TTL,
        )
