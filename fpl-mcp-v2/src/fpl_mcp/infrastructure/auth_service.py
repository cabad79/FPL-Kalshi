"""OIDC authentication service for FPL private endpoints.

Handles refresh-token rotation, thread-safe token refresh, and
authenticated HTTP requests. All network I/O is async via ``httpx``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx

from .credentials import SecureCredentialManager

logger = logging.getLogger(__name__)


class AuthenticationError(RuntimeError):
    """Raised when FPL authentication fails or no credentials are configured."""


@dataclass(frozen=True)
class TokenSet:
    """Immutable container for an access-token session.

    Attributes:
        access_token: The short-lived JWT access token.
        refresh_token: The long-lived refresh token (may be rotated).
        expires_at: UTC datetime when the access token expires.
    """

    access_token: str
    refresh_token: str
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Return ``True`` if the token expires within the next 60 seconds."""
        return datetime.now() >= self.expires_at - timedelta(seconds=60)


class FPLAuthService:
    """OIDC authentication layer for Fantasy Premier League.

    This service is **stateful** (it caches the current ``TokenSet`` in
    memory) but **safe for concurrent use**: all token mutations are
    protected by an ``asyncio.Lock``.  Refresh-token rotation is
    persisted immediately via ``SecureCredentialManager`` so that
    process restarts do not lose the latest token.

    Args:
        http_client: An ``httpx.AsyncClient`` instance (injected).
        credentials: Keyring-backed credential manager (injected).
        token_url: Absolute URL of the OIDC token endpoint.
        client_id: OIDC client ID registered with the FPL identity provider.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        credentials: SecureCredentialManager,
        token_url: str,
        client_id: str,
    ) -> None:
        self._http = http_client
        self._credentials = credentials
        self._token_url = token_url
        self._client_id = client_id

        self._token: TokenSet | None = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Token lifecycle
    # ------------------------------------------------------------------

    async def authenticate(self) -> TokenSet:
        """Return a valid ``TokenSet``, refreshing if necessary.

        This method is fully thread-safe: concurrent callers will block
        on the internal lock and share the same refreshed token.

        Raises:
            AuthenticationError: If no refresh token is configured or the
                token endpoint returns an error.

        Returns:
            A valid, non-expired ``TokenSet``.
        """
        async with self._lock:
            if self._token is not None and not self._token.is_expired:
                logger.debug("Reusing cached access token.")
                return self._token

            refresh_token, team_id = self._credentials.load_credentials()
            if not refresh_token:
                raise AuthenticationError(
                    "No refresh token configured. Run 'fpl-mcp-config setup' first."
                )

            logger.debug("Refreshing access token via OIDC token endpoint.")
            response = await self._http.post(
                self._token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise AuthenticationError(
                    f"Token refresh failed: {exc.response.status_code} {exc.response.text}"
                ) from exc

            data: dict[str, Any] = response.json()

            # Token rotation: the IdP may issue a new refresh token.
            new_refresh = data.get("refresh_token", refresh_token)
            if new_refresh != refresh_token:
                logger.info("Refresh token rotated; persisting new token to keyring.")
                self._credentials.store_credentials(new_refresh, team_id or "")

            expires_in = data.get("expires_in", 3600)
            self._token = TokenSet(
                access_token=data["access_token"],
                refresh_token=new_refresh,
                expires_at=datetime.now() + timedelta(seconds=expires_in),
            )
            logger.debug("Access token acquired, expires in %s seconds.", expires_in)
            return self._token

    # ------------------------------------------------------------------
    # Authenticated helpers
    # ------------------------------------------------------------------

    async def make_authed_request(self, url: str) -> dict[str, Any]:
        """Execute an authenticated GET request.

        Automatically attaches the ``X-API-Authorization: Bearer <token>``
        header using the current access token.

        Args:
            url: Fully-qualified URL to request.

        Returns:
            Parsed JSON response body.

        Raises:
            AuthenticationError: If the token cannot be obtained.
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        token = await self.authenticate()
        headers = {"X-API-Authorization": f"Bearer {token.access_token}"}
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_my_team(self, team_id: int) -> dict[str, Any]:
        """Fetch the authenticated user's current squad.

        Endpoint: ``GET /api/my-team/{team_id}/``
        """
        url = f"https://fantasy.premierleague.com/api/my-team/{team_id}/"
        return await self.make_authed_request(url)

    async def get_team_for_gameweek(self, team_id: int, gameweek: int) -> dict[str, Any]:
        """Fetch a team's picks for a specific gameweek.

        Endpoint: ``GET /api/entry/{team_id}/event/{gameweek}/picks/``
        """
        url = (
            f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek}/picks/"
        )
        return await self.make_authed_request(url)

    async def get_entry_data(self, team_id: int) -> dict[str, Any]:
        """Fetch a manager's public profile data.

        Endpoint: ``GET /api/entry/{team_id}/``
        """
        url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
        return await self.make_authed_request(url)

    async def get_entry_transfers(self, team_id: int) -> list[dict[str, Any]]:
        """Fetch a team's transfer history.

        Endpoint: ``GET /api/entry/{team_id}/transfers/``
        """
        url = f"https://fantasy.premierleague.com/api/entry/{team_id}/transfers/"
        data = await self.make_authed_request(url)
        # The endpoint returns a raw list; normalise to list[dict].
        return data if isinstance(data, list) else []
