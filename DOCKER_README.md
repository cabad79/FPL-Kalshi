# 🐳 MCP Kalshi + FPL - Entorno Docker de Pruebas

> **Actualizado:** 2026-08-12 | Ahora incluye **dos MCPs**: Kalshi (mercados de predicción) + FPL (Fantasy Premier League)

---

## 🚀 Inicio Rápido (Windows)

```batch
cd C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi
run-docker.bat
```

Selecciona la opción **1** para iniciar **ambos MCPs**.

---

## 🚀 Inicio Rápido (Linux / macOS / Git Bash)

```bash
cd ~/Downloads/FPL-Kalshi
chmod +x run-docker.sh
./run-docker.sh
```

---

## 📋 Requisitos Previos

| Requisito | Versión | Descargar |
|-----------|---------|-----------|
| Docker Desktop | 4.20+ | [docker.com](https://www.docker.com/products/docker-desktop) |
| Docker Compose | 2.20+ | Incluido en Docker Desktop |
| Clave privada Kalshi | RSA 2048+ | [kalshi.com/account/api-keys](https://kalshi.com/account/api-keys) *(solo para Kalshi)* |

> **Nota:** El MCP de FPL **NO requiere credenciales**. Usa la API pública de Fantasy Premier League.

---

## 🔌 Configuración con Claude Desktop

Edita `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "kalshi-demo": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "C:\\Users\\carlos.jaramillo\\Downloads\\FPL-Kalshi\\.kalshi\\private-key.pem:/app/.kalshi/private-key.pem:ro",
        "-e", "KALSHI_ENV=demo",
        "-e", "KALSHI_KEY_ID=tu_key_id",
        "kalshi-mcp-demo"
      ]
    },
    "fpl": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "ghcr.io/nguyenanhducs/fpl-mcp-server:latest"
      ]
    }
  }
}
```

---

## 🛠️ Herramientas disponibles

### FPL MCP (nguyenanhducs/fpl-mcp-server)

| Tool | Descripción |
|------|-------------|
| `search_players` | Buscar jugadores por nombre (fuzzy matching) |
| `get_player_stats` | Estadísticas completas de un jugador |
| `get_players_by_position` | Filtrar por posición (GK/DEF/MID/FWD) |
| `get_team_info` | Información de un equipo de la Premier League |
| `get_fixtures` | Fixtures de una jornada específica |
| `get_current_gameweek` | GW actual, deadline, estado |
| `get_manager_team` | Equipo de un manager por GW |
| `get_league_standings` | Tabla de una mini-liga |
| `get_transfer_trends` | Jugadores más transferidos in/out |
| `get_captain_picks` | Mejores opciones de capitán |
| `get_dream_team` | Mejor XI de la jornada |
| `compare_players` | Comparar 2+ jugadores lado a lado |
| `get_set_piece_takers` | Cobradores de penaltis, faltas, corners |
| `analyze_team_fixtures` | Análisis de fixtures por equipo |
| `get_player_fixtures` | Fixtures futuros de un jugador |

### Kalshi MCP (9crusher/mcp-server-kalshi v0.2.3)

| Tool | Descripción |
|------|-------------|
| `get_markets` | Listar mercados disponibles |
| `get_market` | Detalle de un mercado |
| `create_order` | Crear orden (con gate `confirm=true`) |
| `get_balance` | Saldo de la cuenta |
| `get_positions` | Posiciones abiertas |
| `cancel_order` | Cancelar orden |
| `fetch_rules_pdf` | Descargar reglas del mercado *(parcheado anti-SSRF)* |

---

## 📂 Estructura del Entorno

```
FPL-Kalshi/
├── docker-compose.yml          # Orquesta Kalshi + FPL
├── Dockerfile                  # Imagen Kalshi (segura)
├── run-docker.bat              # Launcher Windows
├── run-docker.sh               # Launcher Linux/macOS
├── .kalshi/
│   └── private-key.pem         # Tu clave Kalshi (chmod 600)
├── .env                        # Variables Kalshi
├── logs/                       # Logs persistentes
└── DOCKER_README.md            # Este archivo
```

---

## 🧪 Flujo de Prueba Recomendado

### Día 1 — Probar FPL (sin riesgo)
```bash
# Iniciar solo FPL
docker-compose up -d fpl-mcp

# Ver logs
docker logs -f fpl-mcp-demo

# Probar en Claude:
# "Busca a Haaland en FPL"
# "¿Cuál es el fixture de Arsenal en GW1?"
# "Compara a Salah vs Saka"
```

### Día 2-3 — Probar Kalshi en demo
```bash
# Iniciar Kalshi (requiere clave)
docker-compose up -d kalshi-mcp

# En Claude:
# "Muestra mi balance en Kalshi demo"
# "Lista los mercados de Premier League"
# "Preview de una orden (confirm=false)"
```

### Día 4+ — Ambos juntos
```bash
# Iniciar ambos
docker-compose up -d

# En Claude:
# "¿Qué mercados de Kalshi correlacionan con los fixtures favorables de FPL?"
# "Compara los precios de Haaland en FPL vs las odds de Kalshi"
```

---

## ⚠️ Seguridad

| Medida | Kalshi | FPL |
|--------|--------|-----|
| Requiere credenciales | ✅ Sí (API key + RSA) | ❌ No (API pública) |
| Entorno por defecto | `demo` | Producción (solo lectura) |
| Riesgo de pérdida | Bajo (demo) | Cero (solo lectura) |
| Parche SSRF | ✅ Aplicado | N/A |

---

## 📝 Comandos útiles

```bash
# Ver estado de ambos contenedores
docker ps -a | grep mcp

# Logs en tiempo real (ambos)
docker-compose logs -f

# Detener solo FPL
docker-compose stop fpl-mcp

# Detener solo Kalshi
docker-compose stop kalshi-mcp

# Reiniciar FPL
docker-compose restart fpl-mcp

# Ver herramientas registradas en FPL MCP
docker exec fpl-mcp-demo python -c "from fpl_mcp_server import list_tools; list_tools()"
```

---

**Documento generado el 2026-08-12** | MCPs: `nguyenanhducs/fpl-mcp-server` + `9crusher/mcp-server-kalshi` v0.2.3
