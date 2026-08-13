# Análisis Comparativo: Python vs Node.js/TypeScript para MCP Server FPL

## TL;DR — Recomendación

**Terminar el Python existente adaptando `mcp.server.MCPServer` (MCP 2.0)**. El código ya está 95% hecho, la adaptación de la capa MCP es trivial (~50 líneas de cambio), y evita reescribir 4,500 líneas de lógica de negocio.

---

## Estado Actual

### Entorno Disponible
| Herramienta | Versión | Disponible | Nota |
|------------|---------|------------|------|
| Python | 3.11+ | ✅ | Runtime gestionado por Kimi |
| `mcp` (Python SDK) | 2.0.0 | ✅ | Instalado, pero `fastmcp` no existe |
| `mcp.server.MCPServer` | 2.0.0 | ✅ | **Clase de alto nivel que reemplaza a FastMCP** |
| Node.js | 24.15.0 | ✅ | Runtime interno de Kimi Desktop |
| npm | 11.12.1 | ✅ | En ruta absoluta (no en PATH) |
| npx | — | ✅ | En ruta absoluta |

### Código Existente (fpl-mcp-v2)
- **35 archivos**, ~4,500 líneas de código Python
- Arquitectura limpia: `domain/` → `repositories/` → `services/` → `presentation/`
- Contratos entre capas bien definidos en `CONTRACTS.md`
- pyproject.toml pide `mcp>=1.2.0,<2.0.0` pero el entorno tiene `mcp==2.0.0`

---

## Opciones Analizadas

### Opción 1: Python — Adaptar a `mcp.server.MCPServer` (MCP 2.0) ⭐ RECOMENDADA

**Qué hay que hacer:**
1. Cambiar `from mcp.server.fastmcp import FastMCP` → `from mcp.server import MCPServer`
2. Cambiar `mcp = FastMCP(...)` → `mcp = MCPServer(...)`
3. Registrar tools con `mcp.add_tool(fn, name=..., description=...)` en lugar de decoradores
4. Usar `await mcp.run_stdio_async()` en lugar de `mcp.run()`

**Esfuerzo estimado:** 1-2 horas (solo la capa `presentation/`)

**Ventajas:**
- ✅ **95% del código ya está hecho** — dominio, servicios, repositorios, infraestructura listos
- ✅ `MCPServer` en MCP 2.0 tiene API casi idéntica a FastMCP (`add_tool`, `add_resource`, `add_prompt`)
- ✅ `keyring` nativo para credenciales seguras (sin dependencias nativas problemáticas)
- ✅ Async/await nativo con `httpx`
- ✅ Pydantic para validación de modelos ya integrado
- ✅ pytest + pytest-asyncio para testing
- ✅ Typer para CLI ya implementado

**Desventajas:**
- ⚠️ MCP 2.0 es relativamente nuevo, documentación aún en evolución
- ⚠️ Menos ejemplos en la comunidad que MCP 1.x + FastMCP

**Riesgo:** BAJO. La API de `MCPServer` es estable y documentada.

---

### Opción 2: Python — Downgrade a MCP 1.x + FastMCP

**Qué hay que hacer:**
1. Forzar instalación de `mcp>=1.2.0,<2.0.0` (FastMCP existe aquí)
2. El código actual de `fpl-mcp-v2` funcionaría con cambios mínimos

**Esfuerzo estimado:** 30 minutos si el downgrade funciona

**Ventajas:**
- ✅ Código actual funcionaría casi sin cambios
- ✅ FastMCP tiene más ejemplos y comunidad
- ✅ Documentación más madura

**Desventajas:**
- ❌ **Downgrade ha fallado repetidamente** — pip sigue instalando 2.0.0
- ❌ MCP 1.x está en modo legacy; la evolución del protocolo va por 2.0
- ❌ Futuras features del protocolo no estarán disponibles

**Riesgo:** ALTO. El downgrade es técnicamente imposible en este entorno por conflictos de dependencias.

---

### Opción 3: TypeScript — `@prefecthq/fastmcp-ts` (Framework oficial)

**Qué hay que hacer:**
1. Crear proyecto Node.js desde cero
2. Instalar `@prefecthq/fastmcp-ts` (basado en SDK v2 oficial)
3. Reimplementar toda la arquitectura: dominio, servicios, repositorios, infraestructura
4. Traducir Pydantic models a Zod schemas o TypeScript interfaces
5. Reimplementar auth con `keytar` o variables de entorno
6. Reimplementar cache, rate limiting, HTTP client

**Esfuerzo estimado:** 6-10 horas (reescritura completa)

**Ventajas:**
- ✅ TypeScript tiene tipado estático superior a Python+mypy
- ✅ `@prefecthq/fastmcp-ts` soporta legacy + modern spec (2026-07-28)
- ✅ Distribución con `npm install` / `npx` es más amigable que `pip`
- ✅ Async/await nativo en Node.js

**Desventajas:**
- ❌ **Reescribir 4,500 líneas desde cero**
- ❌ No hay `keyring` nativo en Node.js — `keytar` requiere compilación nativa (puede fallar en Windows sin Visual Studio Build Tools)
- ❌ Traducir Pydantic → Zod es trabajo manual y propenso a errores
- ❌ httpx en Python es más ergonómico que `fetch`/`axios` en Node.js para nuestro caso
- ❌ Testing: vitest/jest en lugar de pytest (menos familiar si el equipo es Python-first)

**Riesgo:** MEDIO. Es técnicamente viable, pero costoso.

---

### Opción 4: TypeScript — `mcp-framework` (Framework productivo)

**Qué hay que hacer:**
1. `npx mcp create fpl-mcp` — scaffolding automático
2. Implementar class-based tools con Zod validation
3. Reimplementar toda la lógica de negocio
4. Configurar auth (tiene built-in JWT/API Key/OAuth 2.1)

**Esfuerzo estimado:** 5-8 horas

**Ventajas:**
- ✅ CLI scaffolding (`mcp create`) acelera setup inicial
- ✅ 50% menos boilerplate que SDK oficial
- ✅ Class-based tools con Zod validation automática
- ✅ Auth built-in
- ✅ Usado por Vercel, Next.js, LocalStack

**Desventajas:**
- ❌ **Reescribir todo desde cero** igual que opción 3
- ❌ Framework menos maduro que `@prefecthq/fastmcp-ts`
- ❌ Misma problemática de `keytar`/credenciales que opción 3
- ❌ Abstracciones más opinionadas — menos control

**Riesgo:** MEDIO-ALTO. Framework con menos adopción que el oficial.

---

## Matriz de Decisión

| Criterio | Python MCP 2.0 ⭐ | Python 1.x (downgrade) | TS fastmcp-ts | TS mcp-framework |
|----------|------------------|----------------------|---------------|------------------|
| Código existente reusable | ~95% | ~95% | 0% | 0% |
| Esfuerzo de implementación | 1-2h | 30min* | 6-10h | 5-8h |
| Credenciales seguras (keyring) | ✅ Nativo | ✅ Nativo | ⚠️ keytar | ⚠️ keytar |
| Tipado | 🟡 mypy | 🟡 mypy | ✅ Estático | ✅ Estático |
| Testing maduro | ✅ pytest | ✅ pytest | 🟡 vitest | 🟡 vitest |
| Soporte protocolo moderno | ✅ 2026-07-28 | ❌ Legacy | ✅ Dual | ✅ Dual |
| Distribución final | pip | pip | npm/npx | npm/npx |
| Riesgo técnico | 🟢 Bajo | 🔴 Alto | 🟡 Medio | 🟡 Medio-Alto |
| Documentación / ejemplos | 🟡 Creciendo | ✅ Madura | 🟡 Creciendo | 🟡 Creciendo |

\* Solo si el downgrade funciona, lo cual ha fallado repetidamente.

---

## Mi Recomendación Detallada

### Ir con Python MCP 2.0 + `mcp.server.MCPServer`

**Razones:**

1. **Costo de oportunidad**: Reescribir a TypeScript consume 6-10 horas de trabajo que podrían invertirse en features (soporte Kalshi, análisis predictivo, integración con más ligas).

2. **La API es casi idéntica**: `MCPServer.add_tool()` tiene la misma firma que `FastMCP.add_tool()`. El cambio es mecánico.

3. **El código de negocio es el activo valioso**: Los 35 archivos de dominio, servicios, repositorios e infraestructura son puros Python sin dependencia de MCP. Solo ~5 archivos en `presentation/` tocan MCP.

4. **Credenciales**: Python `keyring` funciona en Windows/Mac/Linux sin compilación nativa. `keytar` en Node.js requiere `node-gyp` + Visual Studio Build Tools en Windows — un punto de fallo innecesario.

5. **MCP 2.0 es el futuro**: La versión 2.0 del protocolo trae mejoras de seguridad (OAuth 2.1, stateless mode) y el SDK Python ya las implementa. No tiene sentido atarse a legacy.

### Plan de Acción (si eliges Python MCP 2.0)

```
1. Actualizar pyproject.toml: "mcp>=2.0.0" (ya está instalado)
2. Reescribir src/fpl_mcp/presentation/server.py:
   - Cambiar FastMCP → MCPServer
   - Usar mcp.add_tool() en lugar de decoradores
   - Usar await mcp.run_stdio_async()
3. Reescribir src/fpl_mcp/presentation/resources.py (si usa decoradores @resource)
4. Reescribir src/fpl_mcp/presentation/prompts.py (si usa decoradores @prompt)
5. Actualizar src/fpl_mcp/__main__.py para usar run_stdio_async()
6. Ejecutar tests existentes para verificar que nada se rompió
7. Probar con MCP Inspector
```

**Tiempo estimado total**: 1-2 horas.

---

## Si Aún Prefieres TypeScript

Entiendo que TypeScript puede ser más atractivo por:
- Mejor distribución (`npx fpl-mcp` vs `pip install fpl-mcp-v2`)
- Tipado estático más robusto
- Ecosistema npm más amplio

En ese caso, mi recomendación sería:
1. **Usar `@prefecthq/fastmcp-ts`** (no `fastmcp` de punkpeye, que es legacy)
2. **No usar `keytar`** — usar variables de entorno o archivo de credenciales en `%APPDATA%` con DPAPI en Windows
3. Reutilizar los contratos de `CONTRACTS.md` como especificación
4. Implementar en este orden: dominio (Zod schemas) → infraestructura HTTP → repositorios → servicios → presentation

---

## Conclusión

| Escenario | Decisión |
|-----------|----------|
| Quieres un MCP server funcional **hoy** | Python MCP 2.0 |
| El equipo prefiere TypeScript a largo plazo | Python MCP 2.0 ahora, migrar a TS cuando el protocolo estabilice |
| Quieres reescribir como ejercicio de aprendizaje | TypeScript `@prefecthq/fastmcp-ts` |
| Necesitas el mejor tipado posible | TypeScript, pero aceptando el costo de reescritura |

La respuesta honesta: **Python MCP 2.0 es el camino de mayor valor con menor riesgo.**
