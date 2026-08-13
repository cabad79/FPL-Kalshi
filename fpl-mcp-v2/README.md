# fpl-mcp-v2

Servidor MCP (Model Context Protocol) para Fantasy Premier League: expone datos de
jugadores, equipos, fixtures y gameweeks como resources, herramientas de análisis
(capitanía, transferencias, ligas) y prompts de asistencia FPL.

## Arquitectura

```
domain/         → Modelos (Player, Team, Fixture, Gameweek, BootstrapStatic)
infrastructure/ → HTTP client, cache, rate limiter, credenciales, auth
repositories/   → Acceso a datos (bootstrap, player, fixture)
services/       → Lógica de negocio (captain, fixture, league, live, player)
presentation/   → Capa MCP (tools.py, resources.py, prompts.py) vía FastMCP
```

## Uso local

```bash
pip install -e ".[dev]"
python -m fpl_mcp          # modo servidor MCP (stdio)
python -m fpl_mcp setup    # CLI: configuración
```

## Docker

```bash
docker build -t fpl-mcp-v2:local .
docker run -i --rm fpl-mcp-v2:local
```

Requiere `FPL_OIDC_CLIENT_ID` como variable de entorno para features autenticadas
(mi equipo, ligas, transferencias). Los datos públicos (jugadores, fixtures,
gameweeks) no requieren credenciales.
