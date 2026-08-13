# Análisis de lo Rescatable: FPL MCP Server (Python)

> **Fecha**: 12 de agosto de 2026  
> **Objeto de análisis**: `rishijatia/fantasy-pl-mcp` v0.1.7  
> **Objetivo**: Identificar qué código se puede rescatar, qué debe refactorizarse, y qué debe reescribirse para construir una versión mejorada en Python.

---

## 1. Inventario Completo del Codebase

| # | Archivo | Líneas (aprox) | Estado | Responsabilidad |
|---|---------|---------------|--------|-----------------|
| 1 | `__main__.py` | ~180 | ⚠️ Refactorizar | Entry point, registro de resources/tools/prompts |
| 2 | `config.py` | ~70 | ❌ Reescribir | Configuración global, secrets hardcodeados |
| 3 | `cli.py` | ~150 | ⚠️ Refactorizar | CLI interactivo para setup de credenciales |
| 4 | `fpl/api.py` | ~220 | ⚠️ Refactorizar | Cliente HTTP, caché, rate limiting, schema validation |
| 5 | `fpl/auth_manager.py` | ~200 | ❌ Reescribir | Autenticación OIDC, manejo de tokens |
| 6 | `fpl/cache.py` | ~170 | ⚠️ Refactorizar | Caché en disco con TTL |
| 7 | `fpl/credential_manager.py` | ~170 | ❌ Reescribir | Encriptación de credenciales (insegura) |
| 8 | `fpl/rate_limiter.py` | ~60 | ✅ Rescatable | Rate limiter basado en ventana deslizante |
| 9 | `fpl/resources/players.py` | ~280 | ⚠️ Refactorizar | Resource handlers de jugadores |
| 10 | `fpl/resources/teams.py` | ~80 | ✅ Rescatable | Resource handlers de equipos |
| 11 | `fpl/resources/gameweeks.py` | ~130 | ✅ Rescatable | Resource handlers de gameweeks |
| 12 | `fpl/resources/fixtures.py` | ~480 | ⚠️ Refactorizar | Resource handlers de fixtures |
| 13 | `fpl/resources/player_nicknames.py` | ~15 | ✅ Rescatable | Mapeo de nicknames de jugadores |
| 14 | `fpl/tools/players.py` | ~280 | ⚠️ Refactorizar | Tool handlers de jugadores |
| 15 | `fpl/tools/fixtures.py` | ~240 | ⚠️ Refactorizar | Tool handlers de fixtures |
| 16 | `fpl/tools/gameweeks.py` | ~120 | ✅ Rescatable | Tool handlers de gameweeks |
| 17 | `fpl/tools/live.py` | ~140 | ✅ Rescatable | Tool handlers de live scores |
| 18 | `fpl/tools/analysis.py` | ~420 | ⚠️ Refactorizar | Tool handlers de análisis y comparación |
| 19 | `fpl/tools/advice.py` | ~170 | ✅ Rescatable | Tool handlers de consejos (suggest_captain) |
| 20 | `fpl/tools/leagues.py` | ~650 | ⚠️ Refactorizar | Tool handlers de ligas y analytics |
| 21 | `fpl/tools/manager.py` | ~? | ⚠️ Refactorizar | Tool handlers de manager (no se obtuvo) |
| 22 | `fpl/utils/difficulty.py` | ~50 | ✅ Rescatable | Fórmula de dificultad de fixtures |
| 23 | `fpl/utils/concurrency.py` | ~40 | ✅ Rescatable | `gather_limited` para concurrencia controlada |
| 24 | `fpl/utils/params.py` | ~50 | ✅ Rescatable | `unwrap` para normalizar parámetros de tools |
| 25 | `fpl/utils/gameweek.py` | ~60 | ✅ Rescatable | Helpers para determinar gameweek actual/siguiente |
| 26 | `fpl/utils/position_utils.py` | ~60 | ✅ Rescatable | Normalización de posiciones (GKP/DEF/MID/FWD) |
| 27 | `schemas/*.json` | ~? | ⚠️ Refactorizar | JSON schemas para validación |

**Totales**:
- ✅ Rescatable directamente: ~8 archivos
- ⚠️ Refactorizar: ~15 archivos
- ❌ Reescribir: ~3 archivos

---

## 2. Análisis por Componente

### 2.1 ✅ RESCATABLE (Copiar/Adaptar con mínimos cambios)

#### 2.1.1 `fpl/utils/difficulty.py` — Fórmula de Dificultad

```python
def fixture_score(fixtures: List[Dict[str, Any]], key: str = "difficulty") -> float:
    if not fixtures:
        return 0.0
    avg_difficulty = sum(f[key] for f in fixtures) / len(fixtures)
    return round((6 - avg_difficulty) * 2, 1)

def assess_fixtures(score: float) -> str:
    if score >= 8: return "Excellent fixtures"
    if score >= 6: return "Good fixtures"
    if score >= 4: return "Average fixtures"
    return "Difficult fixtures"
```

**Veredicto**: ✅ **Copiar exactamente**. La fórmula `(6 - avg_difficulty) * 2` es el estándar de facto del ecosistema FPL. Bien documentada, bien testeada.

---

#### 2.1.2 `fpl/utils/concurrency.py` — `gather_limited`

```python
async def gather_limited(
    coros: Iterable[Awaitable[Any]],
    limit: int = 5,
    return_exceptions: bool = False,
) -> List[Any]:
    semaphore = asyncio.Semaphore(limit)
    async def _run(coro: Awaitable[Any]) -> Any:
        async with semaphore:
            return await coro
    return await asyncio.gather(
        *(_run(c) for c in coros), return_exceptions=return_exceptions
    )
```

**Veredicto**: ✅ **Copiar exactamente**. Patrón asyncio estándar, limpio, sin dependencias. Esencial para no saturar la API de FPL cuando se consultan múltiples equipos de una liga.

---

#### 2.1.3 `fpl/utils/params.py` — `unwrap`

```python
def unwrap(value: Any, *keys: str, default: Any = _MISSING) -> Any:
    if not isinstance(value, dict):
        return value
    for key in keys:
        if key in value:
            return value[key]
    if default is _MISSING:
        return str(value)
    return default
```

**Veredicto**: ✅ **Copiar exactamente**. Solución elegante al problema real de que algunos MCP clients envuelven parámetros en dicts.

---

#### 2.1.4 `fpl/utils/gameweek.py` — Helpers de Gameweek

```python
async def get_current_gameweek_id() -> Optional[int]:
    gameweeks = await api.get_gameweeks()
    for gw in gameweeks:
        if gw.get("is_current"):
            return gw.get("id")
    for gw in gameweeks:
        if gw.get("is_next"):
            gw_id = gw.get("id")
            return max(1, gw_id - 1) if gw_id else None
    return None
```

**Veredicto**: ✅ **Copiar con inyección de dependencias**. La lógica es correcta, pero hay que eliminar la dependencia global `from ..api import api`.

---

#### 2.1.5 `fpl/utils/position_utils.py` — Normalización de Posiciones

```python
POSITION_MAPPINGS = {
    "GKP": "GKP", "DEF": "DEF", "MID": "MID", "FWD": "FWD",
    "goalkeeper": "GKP", "goalie": "GKP", "keeper": "GKP",
    "defender": "DEF", "fullback": "DEF", "center-back": "DEF", "cb": "DEF",
    # ... etc
}

def normalize_position(position_term: Optional[str]) -> Optional[str]:
    if not position_term:
        return None
    normalized = position_term.lower().strip()
    for term, code in POSITION_MAPPINGS.items():
        if normalized == term.lower():
            return code
    # ... partial matches
    return position_term
```

**Veredicto**: ✅ **Copiar y expandir**. El mapeo es completo y útil. Se puede agregar más aliases según se necesite.

---

#### 2.1.6 `fpl/resources/player_nicknames.py` — Nicknames

```python
NICKNAMES = {
    "kdb": "kevin de bruyne",
    "vvd": "virgil van dijk",
    "taa": "trent alexander-arnold",
    "mo salah": "mohamed salah",
    "son": "heung-min son",
    "rashford": "marcus rashford",
}
```

**Veredicto**: ✅ **Copiar y mantener actualizado**. Data, no lógica. Fácil de mantener.

---

#### 2.1.7 `fpl/rate_limiter.py` — Rate Limiter

```python
class RateLimiter:
    def __init__(self, max_requests: int = 20, per_seconds: int = 60):
        self.request_times: List[float] = []
        self.max_requests = max_requests
        self.time_window = per_seconds
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        while True:
            async with self._lock:
                now = time.time()
                self.request_times = [t for t in self.request_times if now - t < self.time_window]
                if len(self.request_times) < self.max_requests:
                    self.request_times.append(now)
                    return True
                wait_time = self.time_window - (now - self.request_times[0])
            await asyncio.sleep(max(0.01, wait_time))
```

**Veredicto**: ✅ **Copiar con mejoras menores**. Funciona bien pero:
- Agregar backoff exponencial para 429s
- Considerar `asyncio.Queue` en lugar de lista
- Hacer configurable por environment variables

---

#### 2.1.8 `fpl/resources/teams.py` — Resource de Equipos

**Veredicto**: ✅ **Copiar con inyección de dependencias**. Lógica simple, sin problemas de seguridad.

---

### 2.2 ⚠️ REFACTORIZAR (Funciona pero necesita mejoras significativas)

#### 2.2.1 `fpl/resources/players.py` — Resource de Jugadores

**Problemas identificados**:

1. **Re-calcula todo en cada request**:
```python
async def get_players_resource(...) -> List[Dict[str, Any]]:
    data = await api.get_bootstrap_static()  # ~2-3MB
    # Reconstruye 600+ jugadores desde cero CADA VEZ
    for player in data["elements"]:
        # ... 30+ campos por jugador
```

2. **Sin tipado de datos**: Todo es `Dict[str, Any]`. Errores en runtime.

3. **Logging excesivo en producción**:
```python
logging.info(f"Team map: {team_map}")  # Esto loguea TODO el diccionario
logging.info(f"Position map: {position_map}")
```

4. **Búsqueda por nombre O(n) sin índice**:
```python
async def find_players_by_name(name: str, limit: int = 5):
    all_players = await get_players_resource()  # ¡Reconstruye 600+ jugadores!
    for player in all_players:  # Búsqueda lineal
```

**Refactorización propuesta**:
- Usar **Pydantic models** para tipado fuerte y validación
- **Pre-computar** el dataset formateado una vez por hora
- **Indexar** por nombre, web_name, y ID para búsquedas O(1)
- Eliminar logging de datos completos

```python
# NUEVO: Pydantic models
from pydantic import BaseModel, Field
from typing import Literal

class Player(BaseModel):
    id: int
    name: str
    web_name: str
    team: str
    team_short: str
    position: Literal["GKP", "DEF", "MID", "FWD"]
    price: float = Field(..., ge=3.5, le=15.0)
    form: float
    points: int
    # ... etc

# NUEVO: PlayerRepository con índices
class PlayerRepository:
    def __init__(self):
        self._players: list[Player] = []
        self._by_id: dict[int, Player] = {}
        self._by_name: dict[str, list[Player]] = {}  # índice invertido
        self._last_update: datetime | None = None
    
    async def refresh(self):
        data = await self._api.get_bootstrap_static()
        self._players = [self._format_player(p) for p in data["elements"]]
        self._by_id = {p.id: p for p in self._players}
        self._build_name_index()
    
    def search(self, query: str, limit: int = 5) -> list[Player]:
        # Búsqueda por índice invertido en memoria — O(1) lookup
        tokens = query.lower().split()
        # ... scoring y ranking
```

---

#### 2.2.2 `fpl/resources/fixtures.py` — Resource de Fixtures

**Problemas identificados**:

1. **Cálculo de blank/double gameweeks ineficiente**:
```python
async def get_blank_gameweeks(num_gameweeks: int = 5):
    all_gameweeks = await api.get_gameweeks()      # API call
    all_fixtures = await api.get_fixtures()         # API call  
    team_data = await api.get_teams()               # API call (ya en bootstrap!)
```

2. **Reconstruye team_map en cada función**:
```python
teams_data = await api.get_teams()  # Ya está en bootstrap-static
```

3. **Historial de gameweeks sin batching eficiente**:
```python
# Actual: un call por jugador
summaries = await gather_limited(
    (api.get_player_summary(player_id) for player_id in player_ids),
    limit=5,
)
```

**Refactorización propuesta**:
- Usar datos de `bootstrap-static` en lugar de llamadas redundantes
- Cachear resultados de blank/double GW como propiedades derivadas
- Optimizar batching para historial

---

#### 2.2.3 `fpl/api.py` — Cliente HTTP

**Problemas identificados**:

1. **Schema validation es un no-op la mayoría del tiempo**:
```python
def validate_data(self, data, schema=None) -> bool:
    if not schema and not self.schema:
        return True  # Siempre pasa si no hay schema
    try:
        jsonschema.validate(instance=data, schema=schema or self.schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.warning(f"Schema validation failed...")  # Solo warning, no falla
        return False
```

2. **El schema es un snapshot que drift cada temporada**:
```python
# FPL reshapes its payload every year
LEGACY_STATIC_SCHEMA_PATH = SCHEMAS_DIR / "static_schema.json"
```

3. **Fix de null values hardcodeado**:
```python
if 'phases' in data:
    for phase in data['phases']:
        if phase.get('highest_score') is None:
            phase['highest_score'] = 0
```

4. **Singleton global**:
```python
api = FPLAPI()  # Creado al importar el módulo
```

**Refactorización propuesta**:
- Eliminar JSON schema validation (no aporta valor, drift constante)
- Usar **Pydantic** para validación estructural con `Optional` fields
- Eliminar fixes hardcodeados, usar modelos con defaults
- Convertir a clase inyectable, no singleton

```python
# NUEVO: Con Pydantic
from pydantic import BaseModel, Field, validator
from typing import Optional

class Phase(BaseModel):
    id: int
    name: str
    start_event: int
    stop_event: int
    highest_score: int = 0  # Default automático

class BootstrapStatic(BaseModel):
    events: list[Gameweek]
    game_settings: GameSettings
    phases: list[Phase]
    teams: list[Team]
    total_players: int
    elements: list[Player]
    # ... etc
    
    @validator('phases', each_item=True)
    def default_highest_score(cls, v):
        if v.highest_score is None:
            v.highest_score = 0
        return v

class FPLClient:
    def __init__(self, http_client: httpx.AsyncClient, cache: Cache):
        self._http = http_client
        self._cache = cache
    
    async def get_bootstrap_static(self) -> BootstrapStatic:
        data = await self._cache.get_or_fetch("bootstrap", self._fetch_bootstrap)
        return BootstrapStatic.model_validate(data)  # Validación estructural
```

---

#### 2.2.4 `fpl/cache.py` — Sistema de Caché

**Problemas identificados**:

1. **Caché en disco para TODO, incluso datos sensibles**:
```python
class FPLCache:
    def __init__(self, cache_dir=CACHE_DIR, default_ttl=CACHE_TTL):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = Cache(str(cache_dir))  # diskcache — PERSISTE EN DISCO
```

2. **Sin separación entre caché pública y privada**:
```python
# Datos públicos (bootstrap-static) y privados (my-team) van al mismo cache
await cache.get_or_fetch("my_team_12345", ..., ttl=60)
await cache.get_or_fetch("bootstrap_static", ..., ttl=3600)
```

3. **Locks en memoria para claves de disco**:
```python
self._locks: Dict[str, asyncio.Lock] = {}
# Lock en RAM para acceso a disco — no protege entre procesos
```

**Refactorización propuesta**:
- **Caché pública**: En memoria (dict) con TTL, para bootstrap/fixtures/teams
- **Caché privada**: En memoria SIN persistencia, para my-team/transfers
- **Caché en disco**: Solo para datos que realmente necesitan persistir (token rotation)

```python
from enum import Enum

class CacheTier(Enum):
    PUBLIC = "public"      # Memoria, TTL largo, no sensitive
    PRIVATE = "private"    # Memoria, TTL corto, nunca a disco
    PERSISTENT = "persistent"  # Disco encriptado, solo tokens

class TieredCache:
    def __init__(self):
        self._public: dict[str, tuple[Any, datetime]] = {}
        self._private: dict[str, tuple[Any, datetime]] = {}
        self._persistent: SecureCache  # Encriptado, solo tokens
    
    async def get_or_fetch(
        self, 
        key: str, 
        fetch_func: Callable,
        tier: CacheTier,
        ttl: int
    ) -> Any:
        # Según el tier, usa la caché apropiada
```

---

#### 2.2.5 `fpl/tools/advice.py` — `suggest_captain`

**Problemas identificados**:

1. **Weights hardcodeados**:
```python
_WEIGHTS = {
    "expected_points": 0.35,
    "form": 0.25,
    "points_per_game": 0.20,
    "fixtures": 0.20,
}
```

2. **Sin explicabilidad detallada del ranking**:

**Veredicto**: ⚠️ **Refactorizar**. El algoritmo es sólido pero debería:
- Hacer weights configurables
- Agregar confianza/intervalo al score
- Permitir override manual de componentes

---

#### 2.2.6 `fpl/tools/analysis.py` — `analyze_players` y `compare_players`

**Problemas identificados**:

1. **Función gigante (420 líneas)**:
```python
async def analyze_players(...):
    # 200+ líneas de filtrado
    # 100+ líneas de sorting
    # 100+ líneas de estadísticas
    # 50+ líneas de gameweek history
```

2. **Duplicación de lógica de gameweek history**:
```python
# Misma lógica de sumar stats que aparece en:
# - analyze_players()
# - compare_players()  
# - get_player_info()
# - get_player_gameweek_history()
```

3. **Sin paginación**: `filtered_players[:limit]` carga TODO en memoria

**Refactorización propuesta**:
- Separar en clases: `PlayerFilter`, `PlayerSorter`, `StatsAggregator`
- Extraer lógica común de gameweek history a `StatsService`
- Implementar streaming/lazy loading para grandes datasets

---

#### 2.2.7 `fpl/tools/leagues.py` — Analytics de Ligas

**Problemas identificados**:

1. **Función más grande del codebase (~650 líneas)**:
```python
async def _get_league_analytics(...):
    # Routing por analysis_type
    # 5 ramas diferentes (overview, historical, team_composition, decisions, fixtures)
    # Cada rama con lógica completamente diferente
```

2. **Duplicación masiva**:
```python
# Limit to top N teams — aparece 8 veces en el archivo
if len(league_data["standings"]) > LEAGUE_RESULTS_LIMIT:
    league_data["standings"] = league_data["standings"][:LEAGUE_RESULTS_LIMIT]
    league_data["limited_to_top"] = LEAGUE_RESULTS_LIMIT
```

3. **Manejo de gameweek ranges duplicado**:
```python
# Misma lógica de parseo de start_gw/end_gw en:
# - get_teams_historical_data()
# - _get_league_analytics()
# - _get_league_fixture_analysis()
```

4. **Dependencia circular oculta**:
```python
from .simplified_decision import get_simplified_league_decision_analysis
```

**Refactorización propuesta**:
- Dividir en 5 archivos separados (uno por analysis_type)
- Extraer `GameweekRangeParser` como servicio compartido
- Crear `LeagueDataPipeline` con steps configurables

---

#### 2.2.8 `__main__.py` — Entry Point

**Problemas identificados**:

1. **Import side-effects**:
```python
from .fpl.resources import players, teams, gameweeks, fixtures
from .fpl.tools import register_advice_tools, register_analysis_tools, ...
# Cada import puede ejecutar código (singletons se crean)
```

2. **Cleanup con atexit problemático**:
```python
def cleanup_auth():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()  # Crea loop solo para cleanup
    # ... puede bloquear
atexit.register(cleanup_auth)
```

**Refactorización propuesta**:
- Usar `typer` o `click` para CLI
- Separar registro de inicialización
- Usar `asyncio.run()` con cleanup en `finally`

---

### 2.3 ❌ REESCRIBIR (Roto, inseguro, o anti-patrón grave)

#### 2.3.1 `fpl/credential_manager.py` — Encriptación de Credenciales

**CRÍTICO: Múltiples vulnerabilidades de seguridad**

```python
def _generate_key(self, salt: bytes) -> bytes:
    # PROBLEMA 1: uuid.getnode() retorna valores aleatorios en VMs/containers
    node = uuid.getnode()
    if (node >> 40) % 2:  # Si es aleatorio...
        machine_id = str(platform.uname()).encode()  # Aún más predecible
    
    # PROBLEMA 2: Material de clave completamente predecible
    key_material = (
        machine_id +           # MAC o uname
        getpass.getuser() +    # username
        str(Path.home()) +     # /home/username
        platform.node()        # hostname
    )
    
    # PROBLEMA 3: Salt almacenado junto con datos encriptados
    # El atacante tiene el salt + ciphertext
    return salt + encrypted_data
    
    # PROBLEMA 4: Sin autenticación de mensaje (no HMAC)
    # Fernet sí tiene HMAC, pero la clave es débil
```

**Reescritura completa requerida**:
```python
# NUEVO: Usar OS keyring en lugar de encriptación DIY
import keyring
from keyring.errors import PasswordDeleteError

class SecureCredentialManager:
    """Almacena credenciales en el keyring del OS. Zero encryption DIY."""
    
    SERVICE_NAME = "fpl-mcp"
    REFRESH_TOKEN_KEY = "refresh_token"
    TEAM_ID_KEY = "team_id"
    
    def store_credentials(self, refresh_token: str, team_id: str) -> None:
        keyring.set_password(self.SERVICE_NAME, self.REFRESH_TOKEN_KEY, refresh_token)
        keyring.set_password(self.SERVICE_NAME, self.TEAM_ID_KEY, team_id)
    
    def load_credentials(self) -> tuple[str | None, str | None]:
        refresh_token = keyring.get_password(self.SERVICE_NAME, self.REFRESH_TOKEN_KEY)
        team_id = keyring.get_password(self.SERVICE_NAME, self.TEAM_ID_KEY)
        return refresh_token, team_id
    
    def clear_credentials(self) -> None:
        try:
            keyring.delete_password(self.SERVICE_NAME, self.REFRESH_TOKEN_KEY)
            keyring.delete_password(self.SERVICE_NAME, self.TEAM_ID_KEY)
        except PasswordDeleteError:
            pass
```

**Ventajas**:
- Usa el keyring nativo del OS (Keychain en macOS, DPAPI en Windows, Secret Service en Linux)
- Claves gestionadas por el OS, no derivadas de datos predecibles
- No hay archivo en disco para robar
- Compatible con 2FA del OS (biométrico, etc.)

---

#### 2.3.2 `fpl/auth_manager.py` — Autenticación OIDC

**Problemas identificados**:

1. **Uso de `requests` (sync) dentro de async**:
```python
loop = asyncio.get_event_loop()
return await loop.run_in_executor(
    None,
    lambda: self._session.post(FPL_TOKEN_URL, data=data, headers=headers),
)
```

2. **Gestión de token rotation no atómica**:
```python
new_refresh = token_data.get("refresh_token")
if new_refresh and new_refresh != self._refresh_token:
    self._refresh_token = new_refresh
    try:
        self._credential_manager.update_refresh_token(new_refresh)
    except Exception as e:
        # Si falla, el próximo run falla
        logger.error("Failed to persist rotated refresh token...")
```

3. **Singleton global**:
```python
_auth_manager = None
def get_auth_manager():
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = FPLAuthManager()
    return _auth_manager
```

**Reescritura propuesta**:
```python
import httpx
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TokenSet:
    access_token: str
    refresh_token: str
    expires_at: datetime

class FPLAuthService:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        credentials: SecureCredentialManager,
        token_url: str,
        client_id: str,
    ):
        self._http = http_client
        self._credentials = credentials
        self._token_url = token_url
        self._client_id = client_id
        self._token: TokenSet | None = None
        self._lock = asyncio.Lock()
    
    async def authenticate(self) -> TokenSet:
        async with self._lock:  # Previene condiciones de carrera
            if self._token and self._token.expires_at > datetime.now() + timedelta(minutes=5):
                return self._token
            
            refresh_token, _ = self._credentials.load_credentials()
            if not refresh_token:
                raise AuthenticationError("No refresh token configured")
            
            response = await self._http.post(
                self._token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "refresh_token": refresh_token,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            new_refresh = data.get("refresh_token", refresh_token)
            
            # Persistencia atómica
            self._credentials.store_credentials(new_refresh, team_id)
            
            self._token = TokenSet(
                access_token=data["access_token"],
                refresh_token=new_refresh,
                expires_at=datetime.now() + timedelta(seconds=data.get("expires_in", 3600)),
            )
            return self._token
```

---

#### 2.3.3 `config.py` — Configuración Global

**Problemas identificados**:

1. **Secrets en código fuente**:
```python
FPL_USER_AGENT = "Mozilla/5.0 ... Chrome/123.0.0.0 ..."
FPL_OIDC_CLIENT_ID = "bfcbaf69-aade-4c1b-8f00-c1cb8a193030"
```

2. **Import side-effects** (carga `.env` al importar):
```python
from dotenv import load_dotenv
load_dotenv()  # Se ejecuta al importar el módulo
```

3. **Paths resueltos en import time**:
```python
try:
    with resources.path("fpl_mcp", "__init__.py") as p:
        BASE_DIR = p.parent
except:
    BASE_DIR = pathlib.Path(__file__).parent.absolute()
```

**Reescritura propuesta**:
```python
# NUEVO: Configuración con Pydantic Settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class FPLConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # API Configuration (sobreescribible por env vars)
    fpl_base_url: str = "https://fantasy.premierleague.com/api"
    fpl_user_agent: str = Field(default="fpl-mcp/2.0.0")
    fpl_oidc_authority: str = "https://account.premierleague.com/as"
    fpl_oidc_client_id: str = Field(default=...)  # Requerido, no hardcodeado
    
    # Rate Limiting
    rate_limit_max: int = Field(default=20, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)
    
    # Caching
    cache_ttl_public: int = 3600
    cache_ttl_private: int = 60
    cache_ttl_live: int = 30
    
    # League
    league_results_limit: int = Field(default=50, le=100)

# Instancia lazy — no se resuelve hasta que se usa
_config: FPLConfig | None = None

def get_config() -> FPLConfig:
    global _config
    if _config is None:
        _config = FPLConfig()
    return _config
```

---

## 3. Arquitectura Propuesta: FPL MCP v2 (Python)

### 3.1 Estructura de Directorios

```
fpl-mcp-v2/
├── pyproject.toml
├── README.md
├── src/
│   └── fpl_mcp/
│       ├── __init__.py
│       ├── __main__.py              # Entry point minimalista
│       ├── server.py                # Inicialización MCP server
│       ├── config.py                # Pydantic Settings (NUEVO)
│       ├── cli.py                   # Typer CLI (REFACTORIZADO)
│       ├── domain/                  # MODELOS (NUEVO)
│       │   ├── __init__.py
│       │   ├── player.py            # Pydantic models
│       │   ├── team.py
│       │   ├── fixture.py
│       │   ├── gameweek.py
│       │   └── league.py
│       ├── services/                # LÓGICA DE NEGOCIO (NUEVO)
│       │   ├── __init__.py
│       │   ├── player_service.py
│       │   ├── fixture_service.py
│       │   ├── gameweek_service.py
│       │   ├── captain_service.py   # Algoritmo de suggest_captain
│       │   ├── comparison_service.py
│       │   └── league_service.py
│       ├── infrastructure/          # INFRAESTRUCTURA
│       │   ├── __init__.py
│       │   ├── fpl_client.py        # Cliente HTTP (REFACTORIZADO)
│       │   ├── cache.py             # TieredCache (REFACTORIZADO)
│       │   ├── rate_limiter.py      # ✅ Rescatable
│       │   ├── auth_service.py      # REESCRITO (keyring)
│       │   └── credentials.py       # REESCRITO (keyring)
│       ├── repositories/            # ACCESO A DATOS
│       │   ├── __init__.py
│       │   ├── player_repository.py # Con índices en memoria
│       │   ├── fixture_repository.py
│       │   └── bootstrap_repository.py
│       ├── presentation/            # CAPA MCP
│       │   ├── __init__.py
│       │   ├── resources.py         # Registro de resources
│       │   ├── tools.py             # Registro de tools
│       │   └── prompts.py           # Templates de prompts
│       └── utils/                   # UTILIDADES
│           ├── __init__.py
│           ├── concurrency.py       # ✅ gather_limited
│           ├── params.py            # ✅ unwrap
│           ├── difficulty.py        # ✅ fixture_score
│           ├── gameweek.py          # ✅ get_current_gameweek_id
│           ├── position.py          # ✅ normalize_position
│           └── nicknames.py         # ✅ NICKNAMES
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/                    # Respuestas mock de FPL API
```

### 3.2 Flujo de Datos

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  MCP Client │────▶│  Resources   │────▶│   Services      │
│  (Claude)   │     │  / Tools     │     │  (Business Logic)│
└─────────────┘     └──────────────┘     └─────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │ Repositories    │
                                        │ (In-memory idx) │
                                        └─────────────────┘
                                                  │
                          ┌───────────────────────┼───────────────────────┐
                          ▼                       ▼                       ▼
                   ┌─────────────┐       ┌──────────────┐       ┌─────────────────┐
                   │ PublicCache │       │ PrivateCache │       │   FPLClient     │
                   │  (memory)   │       │   (memory)   │       │   (HTTP API)    │
                   └─────────────┘       └──────────────┘       └─────────────────┘
```

### 3.3 Diagrama de Dependencias

```
                    ┌─────────────┐
                    │  __main__.py │
                    └──────┬──────┘
                           │ inyecta
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐ ┌──────────────┐ ┌────────────┐
    │   Config   │ │ FPLMCPServer │ │   Cache    │
    │  (Pydantic)│ │              │ │  (Tiered)  │
    └────────────┘ └──────┬───────┘ └────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Resources│  │  Tools   │  │ Prompts  │
    └────┬─────┘  └────┬─────┘  └──────────┘
         │             │
         ▼             ▼
    ┌─────────────────────────────┐
    │        Services             │
    │  Player | Fixture | League  │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │       Repositories          │
    │  (caché + índices + API)    │
    └─────────────────────────────┘
```

---

## 4. Plan de Migración Paso a Paso

### Fase 1: Fundamentos (Día 1-2)
- [ ] **Crear proyecto nuevo** con `uv` o `poetry`
- [ ] **Definir Pydantic models** (`domain/`) para todos los tipos FPL
- [ ] **Implementar `config.py`** con Pydantic Settings
- [ ] **Implementar `credentials.py`** con `keyring`
- [ ] **Implementar `auth_service.py`** con `httpx.AsyncClient`
- [ ] **Tests unitarios** para models, config, auth

### Fase 2: Infraestructura (Día 3-4)
- [ ] **Implementar `FPLClient`** con `httpx` (async puro, sin `requests`)
- [ ] **Implementar `TieredCache`** (public/private/persistent)
- [ ] **Copiar `rate_limiter.py`** ✅
- [ ] **Copiar `gather_limited`** ✅
- [ ] **Tests de integración** contra FPL API real (modo read-only)

### Fase 3: Repositorios (Día 5-6)
- [ ] **Implementar `BootstrapRepository`** con pre-computación e índices
- [ ] **Implementar `PlayerRepository`** con búsqueda por índice invertido
- [ ] **Implementar `FixtureRepository`** con blank/double GW cache
- [ ] **Benchmarks** de latencia vs implementación anterior

### Fase 4: Servicios (Día 7-10)
- [ ] **Implementar `PlayerService`** (search, filter, compare)
- [ ] **Implementar `FixtureService`** (analysis, blanks, doubles)
- [ ] **Implementar `CaptainService`** (algoritmo con weights configurables)
- [ ] **Implementar `LeagueService`** (standings, composition, analytics)
- [ ] **Tests de servicios** con mocks

### Fase 5: Capa MCP (Día 11-13)
- [ ] **Implementar `Resources`** (fpl://static/*)
- [ ] **Implementar `Tools`** (20+ tools con mismas firmas)
- [ ] **Implementar `Prompts`** (5 templates)
- [ ] **Tests end-to-end** con MCP Inspector

### Fase 6: Polish y Release (Día 14-16)
- [ ] **CLI** con `typer` (setup, test, clear)
- [ ] **README** completo
- [ ] **Configuración** para Claude Desktop / Cursor
- [ ] **CI/CD** con GitHub Actions (tests, lint, type-check)
- [ ] **Release** en PyPI

---

## 5. Tabla de Decisión: Rescatar vs Refactorizar vs Reescribir

| Archivo | Rescatar | Refactorizar | Reescribir | Justificación |
|---------|:--------:|:------------:|:----------:|---------------|
| `utils/difficulty.py` | ✅ | | | Fórmula estándar, bien documentada |
| `utils/concurrency.py` | ✅ | | | Patrón asyncio estándar |
| `utils/params.py` | ✅ | | | Utilidad simple y correcta |
| `utils/gameweek.py` | ✅ | | | Lógica correcta, solo inyectar deps |
| `utils/position_utils.py` | ✅ | | | Mapeo útil, solo expandir |
| `utils/nicknames.py` | ✅ | | | Data, no lógica |
| `rate_limiter.py` | ✅ | | | Funciona bien, agregar backoff |
| `resources/teams.py` | ✅ | | | Simple, sin problemas |
| `resources/gameweeks.py` | ✅ | | | Lógica correcta |
| `tools/gameweeks.py` | ✅ | | | Simple y funcional |
| `tools/live.py` | ✅ | | | Bien estructurado |
| `tools/advice.py` | | ✅ | | Algoritmo sólido, hacer configurable |
| `api.py` | | ✅ | | Eliminar schema validation, usar Pydantic |
| `cache.py` | | ✅ | | Separar tiers, eliminar persistencia de privados |
| `resources/players.py` | | ✅ | | Pre-computar, indexar, tipar |
| `resources/fixtures.py` | | ✅ | | Eliminar llamadas redundantes |
| `tools/players.py` | | ✅ | | Tipar, optimizar búsqueda |
| `tools/fixtures.py` | | ✅ | | Simplificar, eliminar duplicación |
| `tools/analysis.py` | | ✅ | | Dividir en clases, extraer lógica común |
| `tools/leagues.py` | | ✅ | | Dividir en 5 archivos, pipeline pattern |
| `__main__.py` | | ✅ | | Separar registro de init, usar typer |
| `cli.py` | | ✅ | | Migrar a `typer`, usar keyring |
| `config.py` | | | ❌ | Secrets hardcodeados, import side-effects |
| `auth_manager.py` | | | ❌ | Mix sync/async, singleton, race conditions |
| `credential_manager.py` | | | ❌ | Encriptación DIY insegura |

---

## 6. Comparativa: v1 (existente) vs v2 (propuesto)

| Aspecto | v1 (rishijatia) | v2 (propuesto) | Impacto |
|---------|----------------|----------------|---------|
| **Seguridad credenciales** | Fernet+PBKDF2 DIY | OS Keyring | 🔒 Crítico |
| **Tipado** | `Dict[str, Any]` | Pydantic models | 🛡️ Alto |
| **Caché datos privados** | Persiste en disco | Solo memoria | 🔒 Crítico |
| **HTTP client** | `httpx` + `requests` mix | `httpx` async puro | ⚡ Medio |
| **Arquitectura** | Singletons globales | Inyección de dependencias | 🏗️ Alto |
| **Búsqueda jugadores** | O(n) lineal | Índice invertido O(1) | ⚡ Alto |
| **Configuración** | Hardcodeado + `.env` | Pydantic Settings | 🛡️ Medio |
| **Testing** | Unit tests básicos | Unit + Integration + E2E | 🧪 Alto |
| **Documentación** | README + docstrings | README + API docs + Architecture Decision Records | 📖 Medio |
| **CLI** | `argparse` | `typer` | 🎯 Medio |

---

## 7. Conclusión

El codebase existente (`rishijatia/fantasy-pl-mcp`) tiene **~30% de código rescatable** (utilidades, fórmulas, mapeos), **~50% refactorizable** (resources, tools, cliente HTTP), y **~20% que debe reescribirse por completo** (seguridad, autenticación, configuración).

### Recomendación: Construir v2 desde cero, importando selectivamente

1. **No hacer fork**: La deuda técnica y los problemas de seguridad están distribuidos por todo el codebase
2. **Crear proyecto nuevo** con estructura limpia (domain/services/repositories/presentation)
3. **Copiar utilidades** (`difficulty.py`, `concurrency.py`, `params.py`, `gameweek.py`, `position_utils.py`, `nicknames.py`)
4. **Reescribir desde cero** la capa de seguridad (`credentials.py`, `auth_service.py`, `config.py`)
5. **Refactorizar** el resto con Pydantic, inyección de dependencias, y caché tiered

**Tiempo estimado**: 2-3 semanas para alcanzar paridad de funcionalidad con v1, con arquitectura enterprise-grade.
