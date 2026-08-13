# Contratos entre Capas — FPL MCP v2

> Este documento define las interfaces entre las 4 capas del proyecto.
> Cada agente debe respetar estos contratos para garantizar integración sin problemas.

---

## 1. Capa de Dominio (`domain/`)

**Responsable**: Agente 1
**Contrato**: Define los Pydantic models que TODAS las demás capas usan.

### 1.1 Modelos Principales

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class Team(BaseModel):
    id: int
    name: str
    short_name: str
    strength: int = Field(..., ge=1, le=5)
    strength_overall_home: int
    strength_overall_away: int
    strength_attack_home: int
    strength_attack_away: int
    strength_defence_home: int
    strength_defence_away: int
    position: Optional[int] = None  # League position

class Gameweek(BaseModel):
    id: int
    name: str
    deadline_time: datetime
    average_entry_score: Optional[int] = None
    highest_score: Optional[int] = None
    finished: bool
    is_current: bool
    is_next: bool
    is_previous: bool
    data_checked: Optional[bool] = None
    most_selected: Optional[int] = None
    most_transferred_in: Optional[int] = None
    most_captained: Optional[int] = None
    most_vice_captained: Optional[int] = None
    chip_plays: Optional[list[dict]] = None

class PlayerStatus(str, Literal):
    AVAILABLE = "a"
    INJURED = "i"
    SUSPENDED = "s"
    UNAVAILABLE = "n"
    DUBIOUS = "d"

class Player(BaseModel):
    id: int
    first_name: str
    second_name: str
    web_name: str
    team_id: int
    element_type: int  # 1=GKP, 2=DEF, 3=MID, 4=FWD
    now_cost: int  # In 0.1m units
    total_points: int
    points_per_game: float
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: float
    creativity: float
    threat: float
    ict_index: float
    form: str
    value_form: str
    value_season: str
    cost_change_start: int
    cost_change_event: int
    selected_by_percent: str
    transfers_in: int
    transfers_out: int
    transfers_in_event: int
    transfers_out_event: int
    event_points: int
    ep_this: Optional[str] = None
    ep_next: Optional[str] = None
    chance_of_playing_next_round: Optional[int] = None
    chance_of_playing_this_round: Optional[int] = None
    news: str = ""
    status: str = "a"  # a, i, s, n, d
    in_dreamteam: bool = False
    dreamteam_count: int = 0
    expected_goals: Optional[str] = None
    expected_assists: Optional[str] = None
    expected_goal_involvements: Optional[str] = None
    expected_goals_conceded: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.second_name}"
    
    @property
    def price_millions(self) -> float:
        return self.now_cost / 10.0

class Fixture(BaseModel):
    id: int
    event: Optional[int] = None  # Gameweek ID
    finished: bool
    finished_provisional: bool
    kickoff_time: datetime
    team_h: int
    team_a: int
    team_h_score: Optional[int] = None
    team_a_score: Optional[int] = None
    team_h_difficulty: int = Field(..., ge=1, le=5)
    team_a_difficulty: int = Field(..., ge=1, le=5)
    pulse_id: Optional[int] = None

class ElementType(BaseModel):
    id: int
    plural_name: str
    plural_name_short: str
    singular_name: str
    singular_name_short: str
    squad_select: int
    squad_min_play: int
    squad_max_play: int

class GameSettings(BaseModel):
    squad_squadplay: int
    squad_squadsize: int
    squad_team_limit: int
    squad_total_spend: int
    transfers_cap: int
    transfers_sell_on_fee: float

class BootstrapStatic(BaseModel):
    events: list[Gameweek]
    game_settings: GameSettings
    teams: list[Team]
    total_players: int
    elements: list[Player]
    element_types: list[ElementType]

class LiveStats(BaseModel):
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: float
    creativity: float
    threat: float
    ict_index: float
    total_points: int
    in_dreamteam: bool = False

class LiveElement(BaseModel):
    id: int
    stats: LiveStats
    explain: list[dict] = []

class LiveEvent(BaseModel):
    elements: list[LiveElement]

class DreamTeamEntry(BaseModel):
    element: int
    points: int
    position: int
```

**Archivos a producir**:
- `src/fpl_mcp/domain/__init__.py` (exporta todos los modelos)
- `src/fpl_mcp/domain/player.py`
- `src/fpl_mcp/domain/team.py`
- `src/fpl_mcp/domain/fixture.py`
- `src/fpl_mcp/domain/gameweek.py`
- `src/fpl_mcp/domain/bootstrap.py` (BootstrapStatic, GameSettings, ElementType)
- `src/fpl_mcp/domain/live.py` (LiveStats, LiveElement, LiveEvent, DreamTeamEntry)

---

## 2. Capa de Configuración (`config.py`)

**Responsable**: Agente 1
**Contrato**: Configuración centralizada via Pydantic Settings. Las demás capas reciben config inyectada.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class FPLConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FPL_",
        extra="ignore",
    )
    
    # Required
    oidc_client_id: str = Field(default=...)
    
    # API Configuration
    api_base_url: str = "https://fantasy.premierleague.com/api"
    oidc_authority: str = "https://account.premierleague.com/as"
    token_url: str = ""
    user_agent: str = "fpl-mcp-v2/2.0.0"
    
    @property
    def resolved_token_url(self) -> str:
        return self.token_url or f"{self.oidc_authority}/token"
    
    # Rate Limiting
    rate_limit_max: int = Field(default=20, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)
    
    # Cache TTLs (seconds)
    cache_ttl_bootstrap: int = 3600
    cache_ttl_fixtures: int = 3600
    cache_ttl_live: int = 30
    cache_ttl_auth: int = 300
    cache_ttl_private: int = 60
    
    # League
    league_results_limit: int = Field(default=50, le=100)
    
    # Captain Algorithm Weights
    captain_weight_expected_points: float = 0.35
    captain_weight_form: float = 0.25
    captain_weight_ppg: float = 0.20
    captain_weight_fixtures: float = 0.20
```

---

## 3. Capa de Seguridad (`infrastructure/credentials.py`, `infrastructure/auth_service.py`)

**Responsable**: Agente 1
**Contrato**: Provee autenticación segura sin persistir tokens en disco plano.

### 3.1 Credenciales (OS Keyring)

```python
import keyring
from keyring.errors import PasswordDeleteError

class SecureCredentialManager:
    """Stores credentials in OS keyring. No DIY encryption."""
    SERVICE_NAME: str = "fpl-mcp-v2"
    REFRESH_TOKEN_KEY: str = "refresh_token"
    TEAM_ID_KEY: str = "team_id"
    
    def store_credentials(self, refresh_token: str, team_id: str) -> None: ...
    def load_credentials(self) -> tuple[str | None, str | None]: ...
    def clear_credentials(self) -> None: ...
    def has_credentials(self) -> bool: ...
```

### 3.2 Auth Service

```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass(frozen=True)
class TokenSet:
    access_token: str
    refresh_token: str
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() >= self.expires_at - timedelta(seconds=60)

class FPLAuthService:
    """OIDC authentication with refresh token rotation."""
    
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        credentials: SecureCredentialManager,
        token_url: str,
        client_id: str,
    ) -> None:
        ...
    
    async def authenticate(self) -> TokenSet:
        """Get valid access token, refreshing if needed. Thread-safe."""
        ...
    
    async def make_authed_request(self, url: str) -> dict[str, Any]:
        """Make authenticated GET request."""
        ...
    
    async def get_my_team(self, team_id: int) -> dict[str, Any]:
        """Get authenticated user's team."""
        ...
    
    async def get_team_for_gameweek(self, team_id: int, gameweek: int) -> dict[str, Any]:
        """Get team picks for a specific gameweek."""
        ...
    
    async def get_entry_data(self, team_id: int) -> dict[str, Any]:
        """Get manager profile."""
        ...
    
    async def get_entry_transfers(self, team_id: int) -> list[dict]:
        """Get transfer history."""
        ...
```

---

## 4. Capa de Infraestructura HTTP (`infrastructure/fpl_client.py`)

**Responsable**: Agente 2
**Contrato**: Cliente HTTP async puro. Devuelve dicts que la capa de repositorios convierte a Pydantic models.

```python
import httpx

class FPLClient:
    """Async HTTP client for FPL API."""
    
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        rate_limiter: RateLimiter,
        base_url: str,
        user_agent: str,
    ) -> None:
        ...
    
    async def get_bootstrap_static(self) -> dict[str, Any]:
        """GET /bootstrap-static/"""
        ...
    
    async def get_fixtures(self) -> list[dict[str, Any]]:
        """GET /fixtures/"""
        ...
    
    async def get_player_summary(self, element_id: int) -> dict[str, Any]:
        """GET /element-summary/{element_id}/"""
        ...
    
    async def get_live_event(self, event_id: int) -> dict[str, Any]:
        """GET /event/{event_id}/live/"""
        ...
    
    async def get_event_status(self) -> dict[str, Any]:
        """GET /event-status/"""
        ...
    
    async def get_dream_team(self, event_id: int) -> dict[str, Any]:
        """GET /dream-team/{event_id}/"""
        ...
    
    async def get_league_standings(self, league_id: int) -> dict[str, Any]:
        """GET /leagues-classic/{league_id}/standings/"""
        ...
    
    async def close(self) -> None:
        ...
```

---

## 5. Capa de Caché (`infrastructure/cache.py`)

**Responsable**: Agente 2
**Contrato**: Caché con 3 tiers. Datos privados NUNCA persisten en disco.

```python
from enum import Enum
from typing import Callable, Any

class CacheTier(Enum):
    PUBLIC = "public"          # Memory only, long TTL, non-sensitive
    PRIVATE = "private"        # Memory only, short TTL, sensitive
    PERSISTENT = "persistent"  # Secure storage, tokens only

class TieredCache:
    """Three-tier cache system."""
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        tier: CacheTier,
        ttl: int | None = None,
    ) -> Any:
        """Get from cache or fetch and store."""
        ...
    
    def invalidate(self, key: str | None = None, tier: CacheTier | None = None) -> None:
        """Invalidate cache entries."""
        ...
    
    def get_stats(self) -> dict[str, Any]:
        ...
```

**Reglas de uso**:
| Tipo de dato | Tier | TTL |
|-------------|------|-----|
| `bootstrap-static` | PUBLIC | 3600s |
| `fixtures` | PUBLIC | 3600s |
| `teams` | PUBLIC | 3600s |
| `element-summary/{id}` | PUBLIC | 1800s |
| `event/{id}/live` | PUBLIC | 30s |
| `my-team/{id}` | PRIVATE | 60s |
| `entry/{id}/event/{gw}/picks` | PRIVATE | 300s (histórico: 30 días) |
| `refresh_token` | PERSISTENT | Hasta rotación |

---

## 6. Capa de Repositorios (`repositories/`)

**Responsable**: Agente 2
**Contrato**: Abstracción de acceso a datos. Expone métodos de alto nivel.

```python
class PlayerRepository:
    """Player data with in-memory indexing."""
    
    def __init__(self, client: FPLClient, cache: TieredCache) -> None:
        ...
    
    async def get_all(self) -> list[Player]:
        """Get all players, cached."""
        ...
    
    async def get_by_id(self, player_id: int) -> Player | None:
        """O(1) lookup by ID."""
        ...
    
    async def search_by_name(self, query: str, limit: int = 5) -> list[Player]:
        """Fuzzy name search with scoring."""
        ...
    
    async def get_summary(self, player_id: int) -> dict[str, Any]:
        """Get element-summary."""
        ...

class FixtureRepository:
    def __init__(self, client: FPLClient, cache: TieredCache) -> None:
        ...
    
    async def get_all(self) -> list[Fixture]:
        ...
    
    async def get_by_gameweek(self, gameweek_id: int) -> list[Fixture]:
        ...
    
    async def get_by_team(self, team_id: int) -> list[Fixture]:
        ...
    
    async def get_player_fixtures(self, player_id: int, num: int = 5) -> list[dict]:
        """Upcoming fixtures for a player's team."""
        ...
    
    async def get_blank_gameweeks(self, num_gameweeks: int = 5) -> list[dict]:
        """Blank gameweeks in range."""
        ...
    
    async def get_double_gameweeks(self, num_gameweeks: int = 5) -> list[dict]:
        """Double gameweeks in range."""
        ...

class BootstrapRepository:
    def __init__(self, client: FPLClient, cache: TieredCache) -> None:
        ...
    
    async def get_bootstrap(self) -> BootstrapStatic:
        """Get and validate bootstrap-static."""
        ...
    
    async def get_teams(self) -> list[Team]:
        ...
    
    async def get_gameweeks(self) -> list[Gameweek]:
        ...
    
    async def get_current_gameweek(self) -> Gameweek | None:
        ...
    
    async def get_next_gameweek(self) -> Gameweek | None:
        ...
```

---

## 7. Capa de Servicios (`services/`)

**Responsable**: Agente 3
**Contrato**: Lógica de negocio. Recibe repositorios inyectados.

```python
class PlayerService:
    def __init__(self, player_repo: PlayerRepository, fixture_repo: FixtureRepository) -> None:
        ...
    
    async def search(self, query: str, position: str | None = None, 
                     team: str | None = None, limit: int = 5) -> list[Player]:
        ...
    
    async def compare(self, player_names: list[str], 
                      metrics: list[str] | None = None) -> dict[str, Any]:
        ...
    
    async def analyze(self, filters: PlayerFilters) -> PlayerAnalysisResult:
        ...
    
    async def get_top_players(self, metric: str = "points", 
                               position: str | None = None, 
                               limit: int = 10) -> list[Player]:
        ...
    
    async def get_price_changes(self, direction: str | None = None) -> dict[str, Any]:
        ...

class FixtureService:
    def __init__(self, fixture_repo: FixtureRepository, player_repo: PlayerRepository,
                 bootstrap_repo: BootstrapRepository) -> None:
        ...
    
    async def analyze_player_fixtures(self, player_id: int, num: int = 5) -> FixtureAnalysis:
        ...
    
    async def analyze_team_fixtures(self, team_id: int, num: int = 5) -> FixtureAnalysis:
        ...
    
    async def get_blank_gameweeks(self, num: int = 5) -> list[BlankGameweek]:
        ...
    
    async def get_double_gameweeks(self, num: int = 5) -> list[DoubleGameweek]:
        ...

class CaptainService:
    def __init__(self, player_repo: PlayerRepository, fixture_repo: FixtureRepository,
                 auth_service: FPLAuthService, config: FPLConfig) -> None:
        ...
    
    async def suggest(self, team_id: int | None = None, 
                      gameweek_id: int | None = None) -> CaptainSuggestion:
        """Rank squad by captain score with per-component breakdown."""
        ...

class LeagueService:
    def __init__(self, auth_service: FPLAuthService, player_repo: PlayerRepository,
                 bootstrap_repo: BootstrapRepository, config: FPLConfig) -> None:
        ...
    
    async def get_standings(self, league_id: int) -> LeagueStandings:
        ...
    
    async def get_team_composition(self, league_id: int, gameweek: int | None = None) -> LeagueComposition:
        ...
    
    async def get_historical_performance(self, league_id: int, 
                                          start_gw: int | None = None,
                                          end_gw: int | None = None) -> HistoricalPerformance:
        ...
```

---

## 8. Capa de Presentación MCP (`presentation/`)

**Responsable**: Agente 4
**Contrato**: Expone Resources, Tools y Prompts al MCP server.

### 8.1 Resources (URIs)

```python
resources = [
    "fpl://static/players",
    "fpl://static/players/{name}",
    "fpl://static/teams", 
    "fpl://static/teams/{name}",
    "fpl://gameweeks/current",
    "fpl://gameweeks/all",
    "fpl://fixtures",
    "fpl://fixtures/gameweek/{gameweek_id}",
    "fpl://fixtures/team/{team_name}",
    "fpl://players/{player_name}/fixtures",
    "fpl://gameweeks/blank",
    "fpl://gameweeks/double",
]
```

### 8.2 Tools (Names)

```python
tools = [
    # Players
    "search_fpl_players",
    "get_player_information",
    "analyze_players", 
    "compare_players",
    "get_price_changes",
    # Fixtures & Gameweeks
    "get_gameweek_status",
    "analyze_player_fixtures",
    "analyze_fixtures",
    "get_blank_gameweeks",
    "get_double_gameweeks",
    # Live
    "get_gameweek_live_scores",
    "get_dream_team",
    # Auth/Manager
    "suggest_captain",
    "check_fpl_authentication",
    "update_fpl_credentials",
    "get_my_team",
    "get_manager",
    "get_manager_transfer_history",
    # Leagues
    "get_league_standings",
    "get_league_analytics",
]
```

### 8.3 Prompts

```python
prompts = [
    "transfer_advice_prompt",
    "player_analysis_prompt", 
    "team_rating_prompt",
    "differential_players_prompt",
    "chip_strategy_prompt",
]
```

### 8.4 Server Entry Point

```python
class FPLMCPServer:
    """MCP server initialization and registration."""
    
    def __init__(self, config: FPLConfig) -> None:
        ...
    
    def _register_resources(self) -> None:
        ...
    
    def _register_tools(self) -> None:
        ...
    
    def _register_prompts(self) -> None:
        ...
    
    async def run(self) -> None:
        ...
```

---

## 9. Capa CLI (`cli.py`)

**Responsable**: Agente 4
**Contrato**: CLI con Typer para setup y testing de credenciales.

```python
import typer

app = typer.Typer(name="fpl-mcp-v2")

@app.command()
def setup():
    """Interactive setup of FPL credentials."""
    ...

@app.command()
def test():
    """Test FPL authentication."""
    ...

@app.command()
def clear():
    """Clear stored credentials."""
    ...

@app.command()
def server():
    """Run the MCP server."""
    ...
```

---

## 10. Dependencias entre Agentes

```
Agente 1 (Foundation)
├── domain/ (models) ───────▶ Todos los demás agentes
├── config.py ──────────────▶ Todos los demás agentes
├── credentials.py ─────────▶ Agente 2 (AuthService lo usa)
└── auth_service.py ────────▶ Agente 2 (infra) + Agente 3 (services) + Agente 4 (presentation)

Agente 2 (Infra)
├── cache.py ───────────────▶ Agente 3 (services)
├── fpl_client.py ──────────▶ Agente 3 (repositories lo usan)
└── rate_limiter.py ────────▶ Agente 2 (fpl_client lo usa)

Agente 3 (Services)
├── player_service.py ──────▶ Agente 4 (tools)
├── fixture_service.py ─────▶ Agente 4 (tools)
├── captain_service.py ─────▶ Agente 4 (tools)
└── league_service.py ──────▶ Agente 4 (tools)

Agente 4 (Presentation)
├── resources.py ───────────▶ MCP Server
├── tools.py ───────────────▶ MCP Server
├── prompts.py ─────────────▶ MCP Server
├── server.py ──────────────▶ Entry point
└── cli.py ─────────────────▶ Entry point
```

**Nota**: Los agentes trabajan sobre archivos independientes. La integración se hará en un paso posterior uniendo todos los módulos.
