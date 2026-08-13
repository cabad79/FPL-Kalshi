"""Async HTTP client for the Fantasy Premier League API.

Pure async with httpx. Never uses requests (sync).
"""

from typing import Any

import httpx

from fpl_mcp.infrastructure.rate_limiter import RateLimiter


class FPLClient:
    """Async HTTP client for FPL API endpoints.

    All public methods acquire the rate limiter before making a request.
    Retries with exponential backoff are applied for 429 and 5xx status codes.

    Args:
        http_client: Pre-configured httpx.AsyncClient.
        rate_limiter: Rate limiter instance (injected, not a singleton).
        base_url: Base URL for FPL API (e.g. https://fantasy.premierleague.com/api).
        user_agent: User-Agent string sent with every request.
    """

    _MAX_RETRIES = 3
    _RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        rate_limiter: RateLimiter,
        base_url: str,
        user_agent: str,
    ) -> None:
        self._http = http_client
        self._rate_limiter = rate_limiter
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

    async def _get(self, path: str) -> Any:
        """Make a rate-limited GET request with retries.

        Args:
            path: API path relative to base_url (must start with /).

        Returns:
            Parsed JSON response.

        Raises:
            httpx.HTTPStatusError: On non-retryable 4xx/5xx after all retries.
            httpx.RequestError: On network-level failure.
        """
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(1, self._MAX_RETRIES + 1):
            await self._rate_limiter.acquire_with_backoff(attempt=attempt - 1)
            try:
                response = await self._http.get(url, headers=self._headers())
                if response.status_code in self._RETRY_STATUS_CODES and attempt < self._MAX_RETRIES:
                    last_error = httpx.HTTPStatusError(
                        f"Retryable status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in self._RETRY_STATUS_CODES:
                    raise
            except httpx.RequestError:
                # Network errors are retryable
                if attempt >= self._MAX_RETRIES:
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Unexpected end of retry loop")  # pragma: no cover

    async def get_bootstrap_static(self) -> dict[str, Any]:
        """GET /bootstrap-static/"""
        return await self._get("/bootstrap-static/")

    async def get_fixtures(self) -> list[dict[str, Any]]:
        """GET /fixtures/"""
        return await self._get("/fixtures/")

    async def get_player_summary(self, element_id: int) -> dict[str, Any]:
        """GET /element-summary/{element_id}/"""
        return await self._get(f"/element-summary/{element_id}/")

    async def get_live_event(self, event_id: int) -> dict[str, Any]:
        """GET /event/{event_id}/live/"""
        return await self._get(f"/event/{event_id}/live/")

    async def get_event_status(self) -> dict[str, Any]:
        """GET /event-status/"""
        return await self._get("/event-status/")

    async def get_dream_team(self, event_id: int) -> dict[str, Any]:
        """GET /dream-team/{event_id}/"""
        return await self._get(f"/dream-team/{event_id}/")

    async def get_league_standings(self, league_id: int) -> dict[str, Any]:
        """GET /leagues-classic/{league_id}/standings/"""
        return await self._get(f"/leagues-classic/{league_id}/standings/")

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()
