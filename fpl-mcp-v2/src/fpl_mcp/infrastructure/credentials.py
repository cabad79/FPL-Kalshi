"""Secure credential storage using the OS keyring.

Never persists tokens or secrets to plain disk. All sensitive data is
handled by the platform-native credential store (Keychain on macOS,
DPAPI on Windows, Secret Service on Linux).
"""

import logging

import keyring
from keyring.errors import PasswordDeleteError

logger = logging.getLogger(__name__)


class SecureCredentialManager:
    """Manages FPL refresh tokens and team IDs via the OS keyring.

    This class intentionally does **not** implement its own encryption.
    It delegates entirely to the operating system's secure credential
    store, which is backed by hardware-backed keystores where available.
    """

    SERVICE_NAME: str = "fpl-mcp-v2"
    REFRESH_TOKEN_KEY: str = "refresh_token"
    TEAM_ID_KEY: str = "team_id"

    def store_credentials(self, refresh_token: str, team_id: str) -> None:
        """Persist refresh token and team ID to the OS keyring.

        Args:
            refresh_token: The OIDC refresh token to store.
            team_id: The FPL team (entry) ID associated with the token.
        """
        keyring.set_password(self.SERVICE_NAME, self.REFRESH_TOKEN_KEY, refresh_token)
        keyring.set_password(self.SERVICE_NAME, self.TEAM_ID_KEY, team_id)
        logger.info("Credentials stored securely in OS keyring.")

    def load_credentials(self) -> tuple[str | None, str | None]:
        """Retrieve refresh token and team ID from the OS keyring.

        Returns:
            A tuple of ``(refresh_token, team_id)``. Either value may be
            ``None`` if it has not been stored.
        """
        refresh_token = keyring.get_password(self.SERVICE_NAME, self.REFRESH_TOKEN_KEY)
        team_id = keyring.get_password(self.SERVICE_NAME, self.TEAM_ID_KEY)
        return refresh_token, team_id

    def clear_credentials(self) -> None:
        """Remove all stored credentials from the OS keyring.

        Silently ignores missing entries so the operation is idempotent.
        """
        for key in (self.REFRESH_TOKEN_KEY, self.TEAM_ID_KEY):
            try:
                keyring.delete_password(self.SERVICE_NAME, key)
            except PasswordDeleteError:
                logger.debug("No credential found for %s; nothing to delete.", key)
        logger.info("Credentials cleared from OS keyring.")

    def has_credentials(self) -> bool:
        """Return ``True`` if a refresh token is present in the keyring."""
        return keyring.get_password(self.SERVICE_NAME, self.REFRESH_TOKEN_KEY) is not None
