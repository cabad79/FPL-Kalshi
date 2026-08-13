# Análisis del Ecosistema FPL + Plan de Implementación MCP Server en Go

> **Fecha**: 12 de agosto de 2026  
> **Workspace**: `C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi`  
> **Objetivo**: Analizar el ecosistema de APIs del Fantasy Premier League (FPL) y diseñar un plan para crear un servidor MCP (Model Context Protocol) en Go.

---

## 1. Resumen Ejecutivo

El Fantasy Premier League (FPL) expone una **API REST pública (no documentada oficialmente)** en `https://fantasy.premierleague.com/api/`. Aunque no hay documentación oficial de la Premier League, la comunidad ha mapeado exhaustivamente los endpoints, los esquemas de datos y las autenticaciones requeridas.

**Ya existe un MCP Server para FPL** implementado en Python (`rishijatia/fantasy-pl-mcp`), lo cual representa una referencia valiosa, pero **no existe uno en Go**, lo que abre la oportunidad de construir una implementación nativa con mejor rendimiento, tipado fuerte y concurrencia eficiente.

---

## 2. Arquitectura de la API de FPL

### 2.1 Base URL
```
https://fantasy.premierleague.com/api/
```

### 2.2 Endpoints Documentados (Comunidad)

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/bootstrap-static/` | GET | No | Datos estáticos principales: jugadores, equipos, gameweeks, configuración |
| `/fixtures/` | GET | No | Partidos del fixtures de la temporada |
| `/element-summary/{element_id}/` | GET | No | Resumen detallado de un jugador específico |
| `/event/{event_id}/live/` | GET | No | Datos en vivo de un gameweek |
| `/event-status/` | GET | No | Estado actual del gameweek |
| `/dream-team/{event_id}/` | GET | No | Mejor XI oficial del gameweek |
| `/team/set-piece-notes/` | GET | No | Información de cobradores de tiros de esquina, penales, etc. |
| `/stats/most-valuable-teams/` | GET | No | Equipos más valiosos |
| `/entry/{manager_id}/` | GET | No | Perfil de un manager |
| `/entry/{manager_id}/history/` | GET | No | Historial del manager |
| `/entry/{manager_id}/transfers/` | GET | No | Historial de transferencias |
| `/entry/{manager_id}/event/{event_id}/picks/` | GET | No | Alineación de un manager en un gameweek |
| `/leagues-classic/{league_id}/standings/` | GET | No | Clasificación de liga clásica |
| `/leagues-h2h-matches/league/{league_id}/` | GET | No | Partidos de liga H2H |
| `/league/{league_id}/cup-status/` | GET | No | Estado de la copa de liga |
| `/my-team/{manager_id}/` | GET | **Sí** (cookie) | Equipo del usuario autenticado |
| `/me/` | GET | **Sí** (cookie) | Perfil del usuario autenticado |
| `/entry/{manager_id}/transfers-latest/` | GET | **Sí** (cookie) | Últimas transferencias |

### 2.3 Esquema de Datos Clave (`bootstrap-static/`)

El endpoint más importante retorna una estructura JSON monolítica con las siguientes secciones:

```json
{
  "events": [                 // Array de 38 gameweeks
    {
      "id": 1,
      "name": "Gameweek 1",
      "deadline_time": "2025-08-15T17:30:00Z",
      "average_entry_score": 54,
      "finished": true,
      "is_current": false,
      "is_next": false,
      "is_previous": false
    }
  ],
  "game_settings": {          // Configuración del juego
    "league_join_private_max": 30,
    "league_join_public_max": 5,
    "squad_squadplay": 11,
    "squad_squadsize": 15,
    "squad_team_limit": 3,
    "squad_total_spend": 1000,
    "transfers_cap": 1,
    "transfers_sell_on_fee": 0.5,
    "timezone": "Europe/London"
  },
  "phases": [                 // Fases de la temporada
    {
      "id": 1,
      "name": "Overall",
      "start_event": 1,
      "stop_event": 38,
      "highest_score": 123
    }
  ],
  "teams": [                  // 20 equipos de la Premier League
    {
      "id": 1,
      "name": "Arsenal",
      "short_name": "ARS",
      "strength": 5,
      "strength_overall_home": 1350,
      "strength_overall_away": 1350,
      "strength_attack_home": 1350,
      "strength_attack_away": 1350,
      "strength_defence_home": 1350,
      "strength_defence_away": 1350
    }
  ],
  "total_players": 12802828,  // Total de managers registrados
  "elements": [               // ~600 jugadores ("elements")
    {
      "id": 1,
      "first_name": "Bukayo",
      "second_name": "Saka",
      "web_name": "Saka",
      "team": 1,
      "element_type": 3,      // 1=GK, 2=DEF, 3=MID, 4=FWD
      "now_cost": 105,        // Precio en 0.1m (£10.5m)
      "total_points": 186,
      "points_per_game": 6.2,
      "minutes": 2808,
      "goals_scored": 12,
      "assists": 14,
      "clean_sheets": 10,
      "goals_conceded": 28,
      "own_goals": 0,
      "penalties_saved": 0,
      "penalties_missed": 1,
      "yellow_cards": 3,
      "red_cards": 0,
      "saves": 0,
      "bonus": 18,
      "bps": 520,
      "influence": 850.4,
      "creativity": 650.2,
      "threat": 780.5,
      "ict_index": 208.1,
      "form": "7.0",
      "value_form": "0.7",
      "value_season": "17.7",
      "cost_change_start": 5,
      "cost_change_event": 0,
      "cost_change_start_falls": 0,
      "cost_change_event_falls": 0,
      "selected_by_percent": "25.4",
      "transfers_in": 1250000,
      "transfers_out": 450000,
      "transfers_in_event": 12000,
      "transfers_out_event": 5000,
      "event_points": 8,
      "ep_this": "6.5",       // Expected points this gameweek
      "ep_next": "7.2",       // Expected points next gameweek
      "chance_of_playing_next_round": 100,
      "chance_of_playing_this_round": 100,
      "news": "",
      "news_added": null,
      "status": "a",          // a=available, i=injured, s=suspended, n=unavailable
      "photo": "123456.jpg",
      "code": 123456,
      "value_season": "17.7",
      "value_form": "0.7",
      "in_dreamteam": false,
      "dreamteam_count": 3,
      "penalties_order": 2,
      "corners_and_indirect_freekicks_order": 1,
      "direct_freekicks_order": null
    }
  ],
  "element_stats": [          // Métricas disponibles por jugador
    {
      "label": "Minutes played",
      "name": "minutes"
    },
    {
      "label": "Goals scored",
      "name": "goals_scored"
    }
    // ... etc
  ],
  "element_types": [          // Posiciones
    {
      "id": 1,
      "plural_name": "Goalkeepers",
      "plural_name_short": "GKP",
      "singular_name": "Goalkeeper",
      "singular_name_short": "GKP",
      "squad_select": 2,
      "squad_min_play": 1,
      "squad_max_play": 1
    },
    {
      "id": 2,
      "plural_name": "Defenders",
      "plural_name_short": "DEF",
      "singular_name": "Defender",
      "singular_name_short": "DEF",
      "squad_select": 5,
      "squad_min_play": 3,
      "squad_max_play": 5
    },
    {
      "id": 3,
      "plural_name": "Midfielders",
      "plural_name_short": "MID",
      "singular_name": "Midfielder",
      "singular_name_short": "MID",
      "squad_select": 5,
      "squad_min_play": 2,
      "squad_max_play": 5
    },
    {
      "id": 4,
      "plural_name": "Forwards",
      "plural_name_short": "FWD",
      "singular_name": "Forward",
      "singular_name_short": "FWD",
      "squad_select": 3,
      "squad_min_play": 1,
      "squad_max_play": 3
    }
  ],
  "chips": [                  // Chips disponibles
    {
      "id": 1,
      "name": "bboost",
      "limit": 1,
      "description": "Bench Boost"
    },
    {
      "id": 2,
      "name": "freehit",
      "limit": 1,
      "description": "Free Hit"
    },
    {
      "id": 3,
      "name": "wildcard",
      "limit": 2,
      "description": "Wildcard"
    },
    {
      "id": 4,
      "name": "3xc",
      "limit": 1,
      "description": "Triple Captain"
    }
  ]
}
```

### 2.4 Esquema de Datos de Fixtures (`fixtures/`)

```json
[
  {
    "id": 1,
    "event": 1,                    // Gameweek ID
    "finished": true,
    "finished_provisional": true,
    "kickoff_time": "2025-08-15T19:00:00Z",
    "team_h": 1,                   // Home team ID
    "team_a": 2,                   // Away team ID
    "team_h_score": 2,
    "team_a_score": 1,
    "team_h_difficulty": 3,        // Dificultad del partido (1-5)
    "team_a_difficulty": 4,
    "pulse_id": 12345,
    "stats": [                     // Estadísticas detalladas
      {
        "identifier": "goals",
        "a": [],
        "h": [{"value": 1, "element": 123}]
      }
    ]
  }
]
```

### 2.5 Esquema de Datos en Vivo (`event/{event_id}/live/`)

```json
{
  "elements": [
    {
      "id": 1,
      "stats": {
        "minutes": 90,
        "goals_scored": 1,
        "assists": 0,
        "clean_sheets": 1,
        "goals_conceded": 0,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "saves": 2,
        "bonus": 3,
        "bps": 35,
        "influence": 45.2,
        "creativity": 30.1,
        "threat": 25.6,
        "ict_index": 10.09,
        "total_points": 10,
        "in_dreamteam": true
      },
      "explain": [
        {
          "fixture": 1,
          "stats": [
            {"identifier": "minutes", "points": 2, "value": 90},
            {"identifier": "goals_scored", "points": 6, "value": 1},
            {"identifier": "clean_sheets", "points": 1, "value": 1},
            {"identifier": "bonus", "points": 3, "value": 3}
          ]
        }
      ]
    }
  ]
}
```

---

## 3. Autenticación

### 3.1 Endpoints Públicos
La mayoría de los endpoints no requieren autenticación. Solo se necesita enviar un `User-Agent` apropiado.

### 3.2 Endpoints Privados (Autenticación por Cookie)

Los endpoints privados (`/my-team/{manager_id}/`, `/me/`, etc.) requieren una **cookie de sesión** obtenida al iniciar sesión en `https://fantasy.premierleague.com`.

**Flujo de autenticación:**
1. POST a `https://users.premierleague.com/accounts/login/` con:
   - `login`: email
   - `password`: contraseña
   - `app`: `plfpl-web`
   - `redirect_uri`: `https://fantasy.premierleague.com/`
2. Extraer las cookies `pl_profile` y `sessionid`
3. Incluirlas en requests posteriores como `Cookie: pl_profile=...; sessionid=...`

---

## 4. Estado Actual del Ecosistema MCP para FPL

### 4.1 MCP Existente: `rishijatia/fantasy-pl-mcp`

| Aspecto | Detalle |
|---------|---------|
| **Lenguaje** | Python 3.10+ |
| **Distribución** | PyPI (`pip install fpl-mcp`) |
| **Recursos** | 11 recursos (`fpl://static/players`, `fpl://fixtures`, etc.) |
| **Tools** | 20+ tools (búsqueda, comparación, análisis, autenticación) |
| **Autenticación** | Soportada (endpoints privados) |
| **Live scores** | Sí |
| **League analytics** | Sí |

**Recursos disponibles:**
- `fpl://static/players` — Todos los jugadores
- `fpl://static/players/{name}` — Búsqueda por nombre
- `fpl://static/teams` — Todos los equipos
- `fpl://gameweeks/current` — Gameweek actual
- `fpl://gameweeks/all` — Todos los gameweeks
- `fpl://fixtures` — Todos los fixtures
- `fpl://fixtures/gameweek/{gameweek_id}` — Fixtures por gameweek
- `fpl://fixtures/team/{team_name}` — Fixtures por equipo
- `fpl://players/{player_name}/fixtures` — Fixtures de un jugador
- `fpl://gameweeks/blank` — Blank gameweeks
- `fpl://gameweeks/double` — Double gameweeks

**Tools disponibles:**
- `search_fpl_players`
- `get_player_information`
- `analyze_players`
- `compare_players`
- `get_price_changes`
- `get_gameweek_status`
- `analyze_player_fixtures`
- `analyze_fixtures`
- `get_blank_gameweeks`
- `get_double_gameweeks`
- `get_gameweek_live_scores`
- `get_dream_team`
- `suggest_captain`
- `check_fpl_authentication`
- `update_fpl_credentials`
- `get_my_team` (auth)
- `get_my_current_team` (auth)
- `get_team` (auth)
- `get_manager` (auth)
- `get_manager_info` (auth)
- `get_manager_transfer_history`
- `get_league_standings` (auth)
- `get_league_analytics` (auth)

### 4.2 Oportunidad: MCP en Go

**No existe un MCP Server para FPL en Go.** Esto representa una oportunidad porque:

1. **Rendimiento**: Go ofrece mejor concurrencia y menor latencia que Python
2. **Tipado fuerte**: Los esquemas de datos de FPL son complejos; Go permite modelarlos con structs con validación en compile time
3. **Binary nativo**: Un solo ejecutable sin dependencias de runtime
4. **Manejo eficiente de JSON**: La API de FPL retorna payloads grandes (~2-3MB en `bootstrap-static/`); Go decodifica más rápido
5. **Caché en memoria**: Ideal para mantener datos de `bootstrap-static/` en caché

---

## 5. Arquitectura Propuesta: MCP Server FPL en Go

### 5.1 Stack Tecnológico

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| **Lenguaje** | Go 1.23+ | Concurrencia nativa, performance, tipado fuerte |
| **MCP SDK** | `github.com/mark3labs/mcp-go` | SDK oficial y más maduro para Go |
| **Transporte** | stdio (primario), SSE (futuro) | stdio para integración con Claude Desktop |
| **HTTP Client** | `net/http` + `github.com/hashicorp/go-retryablehttp` | Retry automático, rate limiting |
| **Cache** | In-memory (`sync.RWMutex` + `time.Timer`) | Datos de bootstrap-static cambian poco |
| **Config** | `github.com/spf13/viper` + env vars | Flexible y estándar |
| **Logging** | `log/slog` (stdlib) | Nativo, estructurado |
| **Testing** | `testing` + `stretchr/testify` | Estándar Go |

### 5.2 Estructura del Proyecto

```
fpl-mcp-go/
├── cmd/
│   └── fpl-mcp/
│       └── main.go              # Entry point
├── internal/
│   ├── fpl/
│   │   ├── client.go            # HTTP client para la API de FPL
│   │   ├── auth.go              # Autenticación por cookie
│   │   ├── cache.go             # Caché en memoria con TTL
│   │   ├── types.go             # Structs para todos los esquemas JSON
│   │   └── endpoints.go         # Wrappers para cada endpoint
│   ├── mcp/
│   │   ├── server.go            # Inicialización del servidor MCP
│   │   ├── resources.go         # Definición de recursos
│   │   ├── tools.go             # Definición de tools
│   │   └── handlers.go          # Handlers para tools/resources
│   └── config/
│       └── config.go            # Configuración del servidor
├── pkg/
│   └── utils/
│       └── helpers.go           # Funciones utilitarias
├── go.mod
├── go.sum
├── README.md
├── Makefile
└── .github/
    └── workflows/
        └── ci.yml               # CI/CD con tests y release
```

### 5.3 Modelo de Dominio (Structs Principales)

```go
package fpl

// BootstrapStatic representa la respuesta completa de /bootstrap-static/
type BootstrapStatic struct {
    Events       []Gameweek    `json:"events"`
    GameSettings GameSettings  `json:"game_settings"`
    Phases       []Phase       `json:"phases"`
    Teams        []Team        `json:"teams"`
    TotalPlayers int           `json:"total_players"`
    Elements     []Player      `json:"elements"`
    ElementStats []ElementStat `json:"element_stats"`
    ElementTypes []ElementType `json:"element_types"`
    Chips        []Chip        `json:"chips"`
}

type Gameweek struct {
    ID                int       `json:"id"`
    Name              string    `json:"name"`
    DeadlineTime      time.Time `json:"deadline_time"`
    AverageEntryScore int       `json:"average_entry_score"`
    Finished          bool      `json:"finished"`
    IsCurrent         bool      `json:"is_current"`
    IsNext            bool      `json:"is_next"`
    IsPrevious        bool      `json:"is_previous"`
}

type Team struct {
    ID                  int    `json:"id"`
    Name                string `json:"name"`
    ShortName           string `json:"short_name"`
    Strength            int    `json:"strength"`
    StrengthOverallHome int    `json:"strength_overall_home"`
    StrengthOverallAway int    `json:"strength_overall_away"`
    StrengthAttackHome  int    `json:"strength_attack_home"`
    StrengthAttackAway  int    `json:"strength_attack_away"`
    StrengthDefenceHome int    `json:"strength_defence_home"`
    StrengthDefenceAway int    `json:"strength_defence_away"`
}

type Player struct {
    ID                              int     `json:"id"`
    FirstName                       string  `json:"first_name"`
    SecondName                      string  `json:"second_name"`
    WebName                         string  `json:"web_name"`
    Team                            int     `json:"team"`
    ElementType                     int     `json:"element_type"`
    NowCost                         int     `json:"now_cost"`
    TotalPoints                     int     `json:"total_points"`
    PointsPerGame                   float64 `json:"points_per_game"`
    Minutes                         int     `json:"minutes"`
    GoalsScored                     int     `json:"goals_scored"`
    Assists                         int     `json:"assists"`
    CleanSheets                     int     `json:"clean_sheets"`
    GoalsConceded                   int     `json:"goals_conceded"`
    OwnGoals                        int     `json:"own_goals"`
    PenaltiesSaved                  int     `json:"penalties_saved"`
    PenaltiesMissed                 int     `json:"penalties_missed"`
    YellowCards                     int     `json:"yellow_cards"`
    RedCards                        int     `json:"red_cards"`
    Saves                           int     `json:"saves"`
    Bonus                           int     `json:"bonus"`
    BPS                             int     `json:"bps"`
    Influence                       float64 `json:"influence"`
    Creativity                      float64 `json:"creativity"`
    Threat                          float64 `json:"threat"`
    ICTIndex                        float64 `json:"ict_index"`
    Form                            string  `json:"form"`
    ValueForm                       string  `json:"value_form"`
    ValueSeason                     string  `json:"value_season"`
    CostChangeStart                 int     `json:"cost_change_start"`
    CostChangeEvent                 int     `json:"cost_change_event"`
    SelectedByPercent               string  `json:"selected_by_percent"`
    TransfersIn                     int     `json:"transfers_in"`
    TransfersOut                    int     `json:"transfers_out"`
    TransfersInEvent                int     `json:"transfers_in_event"`
    TransfersOutEvent               int     `json:"transfers_out_event"`
    EventPoints                     int     `json:"event_points"`
    EPThis                          string  `json:"ep_this"`
    EPNext                          string  `json:"ep_next"`
    ChanceOfPlayingNextRound        int     `json:"chance_of_playing_next_round"`
    ChanceOfPlayingThisRound        int     `json:"chance_of_playing_this_round"`
    News                            string  `json:"news"`
    Status                          string  `json:"status"` // a, i, s, n, d
    InDreamteam                     bool    `json:"in_dreamteam"`
    DreamteamCount                  int     `json:"dreamteam_count"`
}

type Fixture struct {
    ID                   int       `json:"id"`
    Event                int       `json:"event"`
    Finished             bool      `json:"finished"`
    FinishedProvisional  bool      `json:"finished_provisional"`
    KickoffTime          time.Time `json:"kickoff_time"`
    TeamH                int       `json:"team_h"`
    TeamA                int       `json:"team_a"`
    TeamHScore           *int      `json:"team_h_score"`
    TeamAScore           *int      `json:"team_a_score"`
    TeamHDifficulty      int       `json:"team_h_difficulty"`
    TeamADifficulty      int       `json:"team_a_difficulty"`
}

type LiveEvent struct {
    Elements []LiveElement `json:"elements"`
}

type LiveElement struct {
    ID     int          `json:"id"`
    Stats  LiveStats    `json:"stats"`
    Explain []ExplainEntry `json:"explain"`
}

type LiveStats struct {
    Minutes        int     `json:"minutes"`
    GoalsScored    int     `json:"goals_scored"`
    Assists        int     `json:"assists"`
    CleanSheets    int     `json:"clean_sheets"`
    GoalsConceded  int     `json:"goals_conceded"`
    OwnGoals       int     `json:"own_goals"`
    PenaltiesSaved int     `json:"penalties_saved"`
    PenaltiesMissed int    `json:"penalties_missed"`
    YellowCards    int     `json:"yellow_cards"`
    RedCards       int     `json:"red_cards"`
    Saves          int     `json:"saves"`
    Bonus          int     `json:"bonus"`
    BPS            int     `json:"bps"`
    Influence      float64 `json:"influence"`
    Creativity     float64 `json:"creativity"`
    Threat         float64 `json:"threat"`
    ICTIndex       float64 `json:"ict_index"`
    TotalPoints    int     `json:"total_points"`
    InDreamteam    bool    `json:"in_dreamteam"`
}
```

### 5.4 Recursos MCP a Implementar

| URI | Descripción | Cache TTL |
|-----|-------------|-----------|
| `fpl://static/bootstrap` | Datos estáticos completos | 5 min |
| `fpl://static/players` | Lista de jugadores | Hereda de bootstrap |
| `fpl://static/players/{name}` | Jugador por nombre | Hereda de bootstrap |
| `fpl://static/teams` | Lista de equipos | Hereda de bootstrap |
| `fpl://static/teams/{name}` | Equipo por nombre | Hereda de bootstrap |
| `fpl://gameweeks/current` | Gameweek actual | 1 min |
| `fpl://gameweeks/all` | Todos los gameweeks | Hereda de bootstrap |
| `fpl://gameweeks/blank` | Blank gameweeks | 5 min |
| `fpl://gameweeks/double` | Double gameweeks | 5 min |
| `fpl://fixtures/all` | Todos los fixtures | 5 min |
| `fpl://fixtures/gameweek/{id}` | Fixtures por gameweek | 5 min |
| `fpl://fixtures/team/{team_name}` | Fixtures por equipo | 5 min |
| `fpl://live/{gameweek_id}` | Puntajes en vivo | 30 seg |
| `fpl://dream-team/{gameweek_id}` | Dream team | 5 min |

### 5.5 Tools MCP a Implementar

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `search_players` | Buscar jugadores por nombre, equipo, posición | `name`, `team`, `position`, `min_price`, `max_price`, `min_form` |
| `get_player_details` | Detalles completos de un jugador | `player_name` o `player_id` |
| `compare_players` | Comparar 2+ jugadores | `player_names[]` o `player_ids[]` |
| `get_top_players` | Top jugadores por métrica | `metric`, `position`, `limit`, `gameweeks` |
| `get_price_changes` | Cambios de precio del gameweek | `filter` (rises/falls/all) |
| `get_gameweek_status` | Estado actual del gameweek | — |
| `get_fixtures` | Obtener fixtures | `gameweek`, `team`, `from`, `to` |
| `analyze_fixtures` | Analizar dificultad de fixtures | `team`, `player`, `position`, `next_n` |
| `get_live_scores` | Puntajes en vivo | `gameweek_id` |
| `get_dream_team` | Dream team de un gameweek | `gameweek_id` |
| `suggest_captain` | Sugerir capitán | `gameweek_id` |
| `get_my_team` | Mi equipo (requiere auth) | — |
| `get_manager_history` | Historial de un manager | `manager_id` |
| `get_league_standings` | Clasificación de liga | `league_id` |
| `get_blank_double_gameweeks` | Blank y double gameweeks | — |
| `get_set_piece_notes` | Cobradores de balón parado | — |
| `get_transfer_recommendations` | Recomendaciones de transferencia | `budget`, `position`, `metric` |
| `get_value_picks` | Jugadores con mejor relación valor/precio | `position`, `budget`, `min_form` |

---

## 6. Plan de Implementación (Sprints)

### Sprint 0: Setup y Fundamentos (Día 1-2)

- [ ] Inicializar módulo Go: `go mod init github.com/carlosjaramillo/fpl-mcp-go`
- [ ] Instalar dependencias: `mcp-go`, `go-retryablehttp`, `viper`
- [ ] Crear estructura de directorios
- [ ] Definir structs principales en `internal/fpl/types.go`
- [ ] Implementar cliente HTTP básico en `internal/fpl/client.go`
- [ ] Implementar sistema de caché TTL en `internal/fpl/cache.go`
- [ ] Tests unitarios para cliente y caché

### Sprint 1: Endpoints Públicos Core (Día 3-5)

- [ ] Implementar `GetBootstrapStatic()` con cache
- [ ] Implementar `GetFixtures()` con cache
- [ ] Implementar `GetElementSummary(elementID)`
- [ ] Implementar `GetEventLive(eventID)`
- [ ] Implementar `GetEventStatus()`
- [ ] Implementar `GetDreamTeam(eventID)`
- [ ] Implementar `GetSetPieceNotes()`
- [ ] Tests de integración para cada endpoint
- [ ] Benchmarks de latencia

### Sprint 2: Servidor MCP Base (Día 6-8)

- [ ] Inicializar servidor MCP con `mcp-go`
- [ ] Definir Resources (estáticos: players, teams, gameweeks)
- [ ] Implementar Resource handlers
- [ ] Definir Tools básicas (search_players, get_player_details, get_fixtures)
- [ ] Implementar Tool handlers
- [ ] Manejo de errores y logging estructurado
- [ ] Tests end-to-end con MCP Inspector

### Sprint 3: Tools Avanzadas (Día 9-12)

- [ ] Implementar `compare_players` con análisis de métricas
- [ ] Implementar `get_top_players` con filtros
- [ ] Implementar `analyze_fixtures` con dificultad
- [ ] Implementar `suggest_captain` con algoritmo de scoring
- [ ] Implementar `get_price_changes`
- [ ] Implementar `get_value_picks`
- [ ] Implementar `get_transfer_recommendations`
- [ ] Optimizar queries con pre-computación

### Sprint 4: Autenticación y Endpoints Privados (Día 13-15)

- [ ] Implementar flujo de autenticación por cookie
- [ ] Implementar `GetMyTeam()`
- [ ] Implementar `GetManagerHistory()`
- [ ] Implementar `GetLeagueStandings()`
- [ ] Implementar `GetManagerTransferHistory()`
- [ ] Manejo seguro de credenciales (env vars)
- [ ] Tests con credenciales de prueba

### Sprint 5: Polish y Release (Día 16-18)

- [ ] README completo con instrucciones de instalación
- [ ] Configuración para Claude Desktop / Cursor
- [ ] Makefile con targets: build, test, lint, release
- [ ] CI/CD con GitHub Actions
- [ ] Cross-compilation para Windows, macOS, Linux
- [ ] GitHub Release con binarios
- [ ] Homebrew formula (opcional)

---

## 7. Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTE MCP                                   │
│  (Claude Desktop, Cursor, Windsurf, MCP Inspector)                  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ stdio / SSE
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FPL MCP SERVER (Go)                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  MCP Protocol Layer (github.com/mark3labs/mcp-go)          │   │
│  │  ├── Resources (fpl://static/*, fpl://live/*)              │   │
│  │  ├── Tools (search_players, compare_players, ...)          │   │
│  │  └── Prompts (opcional)                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Application Layer                                          │   │
│  │  ├── Resource Handlers                                      │   │
│  │  ├── Tool Handlers                                          │   │
│  │  ├── Business Logic (análisis, comparación, scoring)       │   │
│  │  └── Cache Manager (TTL, invalidación)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Infrastructure Layer                                       │   │
│  │  ├── FPL HTTP Client (retry, rate limiting, user-agent)    │   │
│  │  ├── Auth Manager (cookie-based session)                   │   │
│  │  ├── In-Memory Cache (bootstrap, fixtures, live)           │   │
│  │  └── Config Manager (viper + env vars)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              API FANTASY PREMIER LEAGUE                              │
│  https://fantasy.premierleague.com/api/                              │
│  ├── /bootstrap-static/                                              │
│  ├── /fixtures/                                                      │
│  ├── /element-summary/{id}/                                          │
│  ├── /event/{id}/live/                                               │
│  ├── /entry/{id}/                                                    │
│  ├── /leagues-classic/{id}/standings/                                │
│  ├── /my-team/{id}/        [auth]                                    │
│  └── /me/                  [auth]                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Configuración para Clientes MCP

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "fpl": {
      "command": "fpl-mcp",
      "args": [],
      "env": {
        "FPL_EMAIL": "",
        "FPL_PASSWORD": ""
      }
    }
  }
}
```

### Cursor / Windsurf

Agregar a la configuración de MCP:
```json
{
  "mcpServers": {
    "fpl": {
      "command": "fpl-mcp",
      "args": []
    }
  }
}
```

---

## 9. Consideraciones de Performance

| Aspecto | Estrategia |
|---------|-----------|
| **Payload grande** | `bootstrap-static/` retorna ~2-3MB. Cachear con TTL de 5 min. |
| **Rate limiting** | Implementar cliente con backoff exponencial. Máx 1 req/s. |
| **User-Agent** | Siempre enviar `User-Agent: fpl-mcp-go/1.0.0` |
| **Decodificación JSON** | Usar `json.Decoder` en lugar de `json.Unmarshal` para streams |
| **Concurrencia** | Cada tool handler corre en su propia goroutine |
| **Cache de fixtures** | Los fixtures de una temporada no cambian; cachear indefinidamente hasta próxima temporada |
| **Live scores** | TTL de 30 segundos; solo consultar si hay partidos en curso |

---

## 10. Referencias Clave

| Recurso | URL | Relevancia |
|---------|-----|------------|
| FPL OAS (OpenAPI Spec) | https://github.com/mcclowes/fpl-oas | Documentación comunitaria de la API |
| MCP Go SDK | https://github.com/mark3labs/mcp-go | SDK oficial para Go |
| MCP Go SDK (official) | https://github.com/modelcontextprotocol/go-sdk | SDK oficial alternativo |
| FPL MCP Python | https://github.com/rishijatia/fantasy-pl-mcp | Referencia de funcionalidades |
| FPL API TypeScript | https://github.com/jeppe-smith/fpl-api | Tipos de datos en TypeScript |
| FPL Forecast | https://github.com/daniel-mehta/fpl-forecast | Endpoints confirmados |

---

## 11. Conclusión

El ecosistema de FPL ofrece una **API REST pública robusta** con datos ricos sobre jugadores, equipos, fixtures, y estadísticas en vivo. Aunque existe un MCP Server en Python, **no hay uno en Go**, lo cual representa una oportunidad para construir una solución más performante, con tipado fuerte y mejor manejo de concurrencia.

El plan de implementación propuesto abarca **5 sprints de ~18 días**, comenzando desde los fundamentos (cliente HTTP, structs, caché), pasando por el servidor MCP con recursos y tools, hasta la autenticación y endpoints privados, finalizando con el release de binarios multiplataforma.

**Próximo paso recomendado**: Iniciar Sprint 0 — crear el módulo Go, definir los structs, y construir el cliente HTTP con caché.
