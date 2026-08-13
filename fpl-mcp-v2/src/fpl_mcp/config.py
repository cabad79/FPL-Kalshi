"""Application configuration via Pydantic Settings.

All configuration is loaded from environment variables prefixed with ``FPL_``
(e.g., ``FPL_OIDC_CLIENT_ID``). Optional overrides can be placed in a ``.env``
file at the project root.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FPLConfig(BaseSettings):
    """Centralised configuration for the FPL MCP server.

    Values are read from environment variables (with ``FPL_`` prefix) or
    from a ``.env`` file. No secrets are hard-coded; ``oidc_client_id`` is
    required and must be provided by the operator.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FPL_",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Required
    # ------------------------------------------------------------------
    oidc_client_id: str = Field(
        default=...,
        description="OIDC client ID for FPL authentication (no default).",
    )

    # ------------------------------------------------------------------
    # API Configuration
    # ------------------------------------------------------------------
    api_base_url: str = "https://fantasy.premierleague.com/api"
    oidc_authority: str = "https://account.premierleague.com/as"
    token_url: str = ""
    user_agent: str = "fpl-mcp-v2/2.0.0"

    @property
    def resolved_token_url(self) -> str:
        """Return the absolute token endpoint URL.

        If ``token_url`` is explicitly set, it is used directly; otherwise
        the URL is derived from ``oidc_authority``.
        """
        return self.token_url or f"{self.oidc_authority}/token"

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------
    rate_limit_max: int = Field(default=20, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)

    # ------------------------------------------------------------------
    # Cache TTLs (seconds)
    # ------------------------------------------------------------------
    cache_ttl_bootstrap: int = 3600
    cache_ttl_fixtures: int = 3600
    cache_ttl_live: int = 30
    cache_ttl_auth: int = 300
    cache_ttl_private: int = 60

    # ------------------------------------------------------------------
    # League
    # ------------------------------------------------------------------
    league_results_limit: int = Field(default=50, le=100)

    # ------------------------------------------------------------------
    # Captain Algorithm Weights
    # ------------------------------------------------------------------
    captain_weight_expected_points: float = 0.35
    captain_weight_form: float = 0.25
    captain_weight_ppg: float = 0.20
    captain_weight_fixtures: float = 0.20
