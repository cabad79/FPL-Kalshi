# Análisis de Viabilidad y Seguridad: FPL MCP Server Existente (Python)

> **Fecha**: 12 de agosto de 2026  
> **Objeto de análisis**: `rishijatia/fantasy-pl-mcp` (Python)  
> **Analista**: Especialista MCP + Go  

---

## 1. Resumen Ejecutivo

El repositorio `rishijatia/fantasy-pl-mcp` es un servidor MCP funcional y relativamente maduro para Fantasy Premier League. Sin embargo, presenta **riesgos de seguridad significativos**, **deuda técnica acumulada** y **limitaciones arquitectónicas** que hacen que construir una alternativa en Go sea no solo viable, sino recomendable.

### Veredicto: ⚠️ USAR CON PRECAUCIÓN / RECONSTRUIR EN GO RECOMENDADO

| Dimensión | Calificación | Observación |
|-----------|-------------|-------------|
| **Funcionalidad** | ⭐⭐⭐⭐☆ (4/5) | 20+ tools, 11 resources, autenticación OIDC |
| **Seguridad** | ⭐⭐⭐☆☆ (2.5/5) | Encriptación débil, secrets en disco, side-channel risks |
| **Calidad de Código** | ⭐⭐⭐☆☆ (3/5) | Acoplamiento alto, circular imports, tipado laxo |
| **Mantenibilidad** | ⭐⭐☆☆☆ (2/5) | Singletons globales, estado mutable compartido |
| **Performance** | ⭐⭐⭐☆☆ (3/5) | Python + asyncio, caché en disco lenta |
| **Testing** | ⭐⭐☆☆☆ (2/5) | Tests básicos, cobertura insuficiente |

---

## 2. Arquitectura del Repositorio Existente

### 2.1 Estructura de Archivos

```
fpl-mcp/
├── src/fpl_mcp/
│   ├── __main__.py              # Entry point + registro de recursos/tools/prompts
│   ├── config.py                # Configuración global con valores hardcodeados
│   ├── cli.py                   # CLI para setup de credenciales
│   ├── fpl/
│   │   ├── api.py               # Cliente HTTP (httpx) con schema validation
│   │   ├── auth_manager.py      # Gestión de autenticación OIDC (singleton)
│   │   ├── cache.py             # Caché en disco (diskcache) con TTL
│   │   ├── credential_manager.py # Encriptación de credenciales (PBKDF2 + Fernet)
│   │   ├── rate_limiter.py      # Rate limiter basado en ventana deslizante
│   │   ├── resources/           # Handlers de recursos MCP
│   │   │   ├── players.py
│   │   │   ├── teams.py
│   │   │   ├── gameweeks.py
│   │   │   └── fixtures.py
│   │   ├── tools/               # Handlers de tools MCP
│   │   │   ├── players.py
│   │   │   ├── fixtures.py
│   │   │   ├── gameweeks.py
│   │   │   ├── live.py
│   │   │   ├── advice.py
│   │   │   ├── analysis.py
│   │   │   ├── manager.py
│   │   │   └── leagues.py
│   │   └── utils/               # Utilidades
│   │       ├── concurrency.py
│   │       ├── difficulty.py
│   │       └── gameweek.py
│   └── schemas/                 # JSON schemas para validación
├── pyproject.toml
└── tests/
```

### 2.2 Dependencias Clave

```toml
[project.dependencies]
"mcp>=1.2.0,<2.0.0"    # SDK MCP Python (FastMCP) — BLOQUEADO en 1.x
"httpx>=0.24.0"         # Cliente HTTP async
"python-dotenv"         # Variables de entorno
"diskcache"             # Caché persistente en disco
"jsonschema"            # Validación JSON
"requests"              # Cliente HTTP sync (para auth)
"cryptography"          # Encriptación de credenciales

[dev-dependencies]
"pytest>=7.0.0"
"pytest-asyncio>=0.23.0"
"black", "flake8", "isort", "mypy"
```

---

## 3. Análisis de Seguridad 🔒

### 3.1 CRÍTICO: Encriptación de Credenciales — Clave Derivada Predecible

**Archivo**: `credential_manager.py`

```python
def _generate_key(self, salt: bytes) -> bytes:
    """Generate encryption key from system-specific data"""
    node = uuid.getnode()           # MAC address (puede ser aleatorio)
    machine_id = str(node).encode()
    username = getpass.getuser().encode()
    home_path = str(Path.home()).encode()
    platform_info = platform.node().encode()
    
    key_material = machine_id + username + home_path + platform_info
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_material))
    return key
```

#### Vectores de Ataque Identificados

| Riesgo | Severidad | Explicación |
|--------|-----------|-------------|
| **MAC address aleatorio** | 🔴 Alta | `uuid.getnode()` retorna valores aleatorios en VMs, containers, WSL. Esto hace que la clave sea impredecible incluso para el usuario legítimo |
| **Salt público** | 🟡 Media | El salt de 16 bytes se almacena en el archivo encriptado (`salt + encrypted_data`). Un atacante con acceso al archivo tiene el salt |
| **Material de clave predecible** | 🟡 Media | `username + home_path + platform_info` son valores fácilmente obtenibles de cualquier sistema comprometido |
| **Sin protección contra fuerza bruta** | 🟡 Media | Aunque 600k iteraciones es decente, el espacio de búsqueda del key_material es pequeño |
| **Permisos de archivo** | 🟢 Baja | `os.chmod(0o600)` es correcto, pero no protege contra backup tools, sync (Dropbox), o copias |

#### Impacto
- Si un atacante obtiene el archivo `credentials.enc`, puede derivar la clave con esfuerzo moderado
- El refresh token de FPL es un secret de larga duración — su compromiso permite acceso persistente a la cuenta
- **No hay 2FA** en el flujo de autenticación de FPL

#### Comparativa con Mejores Prácticas

| Aspecto | Implementación Actual | Mejor Práctica | Gap |
|---------|----------------------|----------------|-----|
| Almacenamiento de secrets | Archivo encriptado en disco | OS Keyring (macOS Keychain, Windows DPAPI, Linux Secret Service) | Crítico |
| Derivación de clave | PBKDF2 con material predecible | Argon2id con secret adicional | Alto |
| Rotación de tokens | Automática (PingOne) | Automática + revocación manual | OK |
| Segregación de credenciales | Archivo único | Por-cliente, con namespace | Medio |

### 3.2 ALTO: Secrets Hardcodeados en Código Fuente

**Archivo**: `config.py`

```python
FPL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
FPL_OIDC_CLIENT_ID = "bfcbaf69-aade-4c1b-8f00-c1cb8a193030"
```

| Riesgo | Explicación |
|--------|-------------|
| User-Agent hardcodeado | Finge ser Chrome. Si FPL bloquea este UA, todos los usuarios fallan simultáneamente |
| Client ID hardcodeado | Este es un public client ID de la SPA de FPL. Técnicamente público, pero centraliza el riesgo |
| Falta de rotación | Si el client ID se revoca, no hay mecanismo de fallback |

### 3.3 ALTO: Autenticación OIDC — Uso de Refresh Token Fuera de Contexto

**Archivo**: `auth_manager.py`

```python
async def _request_token(self, refresh_token: str) -> requests.Response:
    data = {
        "grant_type": "refresh_token",
        "client_id": FPL_OIDC_CLIENT_ID,
        "refresh_token": refresh_token,
    }
    return await loop.run_in_executor(
        None,
        lambda: self._session.post(FPL_TOKEN_URL, data=data, headers=headers),
    )
```

| Riesgo | Explicación |
|--------|-------------|
| **Sin PKCE** | El flujo de refresh token no usa PKCE (no aplica), pero el token se obtuvo originalmente con PKCE en el browser |
| **Rotación de tokens no atómica** | Si el proceso crash después de obtener el nuevo refresh token pero antes de persistirlo, el token queda huérfano |
| **Condición de carrera** | Dos instancias del MCP server pueden competir por el mismo refresh token; solo una gana |
| **Sin validación de audience** | No se verifica que el access token sea para el client_id correcto |

### 3.4 MEDIO: Caché en Disco con Datos Sensibles

**Archivo**: `cache.py`

```python
class FPLCache:
    def __init__(self, cache_dir=CACHE_DIR, default_ttl=CACHE_TTL):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = Cache(str(cache_dir))  # diskcache library
```

| Riesgo | Explicación |
|--------|-------------|
| **Datos de equipo en caché** | `get_my_team()` cachea picks del usuario en disco sin encriptar |
| **Historial de transferencias** | `get_entry_transfers()` cachea datos privados |
| **TTL fijo para datos auth** | No hay distinción entre caché pública y privada |
| **Directorio de caché world-readable** | `os.makedirs(exist_ok=True)` no establece permisos restrictivos |

### 3.5 MEDIO: Logging de Información Sensible

**Archivo**: `__main__.py`

```python
logger.info(f"Resource requested: fpl://static/players/{name}")
```

| Riesgo | Explicación |
|--------|-------------|
| **Player names en logs** | Los nombres de jugadores buscados quedan en logs del sistema |
| **Team IDs expuestos** | Información de equipo del usuario puede filtrarse |
| **Sin redacción** | No hay mecanismo para evitar logging de PII en modo producción |

### 3.6 BAJO: Rate Limiter — Sin Protección contra Bypass

**Archivo**: `rate_limiter.py`

```python
class RateLimiter:
    def __init__(self, max_requests=20, per_seconds=60):
        self.request_times = []
```

| Riesgo | Explicación |
|--------|-------------|
| **State en memoria** | Si el server se reinicia, el contador se resetea |
| **No compartido entre procesos** | Múltiples instancias del MCP no comparten el rate limiter |
| **Sin headers de rate limit** | No respeta los headers `X-RateLimit-*` que FPL podría enviar |

---

## 4. Análisis de Viabilidad: ¿Vale la pena reconstruir en Go?

### 4.1 Fortalezas del Implementación Python

| Aspecto | Detalle |
|---------|---------|
| ✅ **Funcionalidad completa** | 20+ tools, 11 resources, 5 prompts templates |
| ✅ **Autenticación OIDC** | Manejo de refresh tokens con rotación automática |
| ✅ **Caché persistente** | Sobrevive reinicios del servidor |
| ✅ **Rate limiting** | Protección básica contra abuso |
| ✅ **Schema validation** | JSON schemas para validar respuestas de FPL |
| ✅ **CLI interactivo** | `fpl-mcp-config setup` con guía paso a paso |
| ✅ **PyPI distribution** | Instalación con `pip install fpl-mcp` |
| ✅ **MIT License** | Open source, permite fork/modificación |

### 4.2 Debilidades del Implementación Python

| Aspecto | Detalle | Impacto |
|---------|---------|---------|
| ❌ **Singletons globales** | `api = FPLAPI()`, `cache = FPLCache()`, `_auth_manager = None` | Imposible de testear, acoplamiento global |
| ❌ **Circular imports** | `cache.py` importa `api.py` que importa `cache.py` | Fragilidad, dependencias ocultas |
| ❌ **Mix sync/async** | `auth_manager.py` usa `requests` (sync) dentro de `async` con `run_in_executor` | Ineficiencia, complejidad innecesaria |
| ❌ **Tipado laxo** | `List[Dict[str, Any]]` en todo el codebase | Sin garantías en compile time |
| ❌ **Error handling débil** | Muchos `try/except` genéricos que silencian errores | Debugging difícil, comportamiento inconsistente |
| ❌ **Caché en disco lenta** | `diskcache` escribe a filesystem para cada operación | Latencia alta en cada request |
| ❌ **MCP 1.x bloqueado** | `"mcp>=1.2.0,<2.0.0"` | No puede usar features nuevas del protocolo |
| ❌ **Sin tests de integración** | Solo tests unitarios básicos | Regresiones frecuentes |

### 4.3 Ventajas de una Reimplementación en Go

| Dimensión | Python (existente) | Go (propuesto) | Ventaja |
|-----------|-------------------|----------------|---------|
| **Binario** | Requiere Python + venv + pip | Single binary | Go: zero dependencies |
| **Startup time** | ~1-2 segundos (import + JIT) | ~50ms | Go: 20x más rápido |
| **Memory** | ~40-80MB (Python + librerías) | ~5-15MB | Go: 5x menos RAM |
| **Concurrencia** | asyncio + GIL | Goroutines nativas | Go: verdadera paralelismo |
| **Tipado** | `Dict[str, Any]` | Structs con tags JSON | Go: errores en compile time |
| **Caché** | Disco (diskcache) | Memoria (sync.Map) | Go: 1000x más rápido |
| **Encriptación** | Fernet + PBKDF2 (custom) | OS keyring nativo | Go: más seguro |
| **Distribución** | PyPI | Go modules / GitHub releases | Go: cross-compile fácil |
| **Testing** | pytest + mocks | `testing` + httptest | Go: tests integrados |
| **Observability** | logging básico | OpenTelemetry nativo | Go: métricas, traces, logs |

### 4.4 Matriz de Decisión

```
                    ┌─────────────────────────────────────┐
                    │   ¿RECONSTRUIR EN GO?              │
                    └─────────────────────────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │  FORKEAR Y    │       │  USAR TAL     │       │  RECONSTRUIR  │
    │  MEJORAR      │       │  CUAL (con    │       │  EN GO        │
    │               │       │  precaución)  │       │               │
    └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
            │                       │                       │
    Esfuerzo: Medio          Esfuerzo: Bajo            Esfuerzo: Alto
    Riesgo: Medio            Riesgo: Alto              Riesgo: Bajo
    Seguridad: Mejora        Seguridad: Actual         Seguridad: Excelente
    Performance: Similar     Performance: Actual       Performance: Excelente
    Mantenimiento: Medio     Mantenimiento: Alto       Mantenimiento: Bajo
```

**Recomendación**: RECONSTRUIR EN GO. La deuda técnica del codebase Python es significativa y tocarlo implica riesgo. Una implementación limpia en Go ofrece mejor seguridad, performance y mantenibilidad.

---

## 5. Lecciones Aprendidas del Código Existente

### 5.1 Qué Hacer Diferente en Go

| Lección del Python | Implementación en Go |
|-------------------|----------------------|
| **No usar singletons globales** | Dependency injection con structs |
| **No mezclar sync/async** | Todo async con `net/http` + goroutines |
| **Separar caché pública vs privada** | `PublicCache` (memory) vs `PrivateCache` (memory + TTL corto, no persistir) |
| **Usar OS keyring para secrets** | `99designs/keyring` o `zalando/go-keyring` |
| **Structs tipados para todo** | `Player`, `Team`, `Fixture` con validación JSON |
| **No loggear PII** | Redactar nombres de jugadores en modo prod |
| **Rate limiter con backoff exponencial** | `cenkalti/backoff` integrado con HTTP client |
| **Schema validation opcional** | JSON Schema con `xeipuuv/gojsonschema` |
| **Tests de integración con FPL API** | `httptest` + snapshots de respuestas |

### 5.2 Qué Conservar del Código Existente

| Aspecto | Implementación Python | Implementación Go |
|---------|----------------------|----------------------|
| **Mapeo de nombres** | `NICKNAMES` dict con aliases | `map[string]string` con aliases |
| **Algoritmo de scoring** | Fixture difficulty + home/away | Mantener fórmula, implementar en Go |
| **Estrategia de caché** | TTL por tipo de dato | Mantener estrategia con TTL ajustados |
| **Flujo OIDC** | Refresh token → access token | Replicar exactamente para compatibilidad |
| **Prompts templates** | 5 prompts predefinidos | Reimplementar como templates Go |

---

## 6. Riesgos de Seguridad Específicos de la Integración FPL

### 6.1 Términos de Servicio de FPL

La API de FPL **no está documentada oficialmente** y no hay TOS explícito para desarrolladores. Sin embargo:

| Riesgo | Mitigación |
|--------|-----------|
| **Rate limiting por FPL** | Implementar backoff exponencial, cache agresivo, max 1 req/s |
| **Bloqueo de User-Agent** | Rotar UA o usar uno descriptivo (`fpl-mcp-go/1.0`) |
| **Cambios de endpoint** | Monitorear respuestas 404/410, fallback gracefully |
| **Revocación de tokens** | Manejar 401 con re-autenticación manual |

### 6.2 Exposición de Datos de Terceros

| Riesgo | Explicación |
|--------|-------------|
| **League standings públicos** | Al consultar una liga, se exponen datos de otros managers |
| **Manager profiles públicos** | `/entry/{id}/` es público; no hay consentimiento implícito |
| **Datos de picks** | Los picks de gameweeks pasados son públicos |

**Mitigación**: Documentar claramente que los datos consultados son públicos por diseño de FPL.

---

## 7. Recomendaciones de Seguridad para la Implementación Go

### 7.1 Checklist de Seguridad

- [ ] **Usar OS Keyring** para almacenar refresh tokens (`zalando/go-keyring`)
- [ ] **Nunca persistir** datos autenticados en caché de disco
- [ ] **Redactar PII** en logs de producción (nombres de jugadores, team IDs)
- [ ] **Validar todos los inputs** con JSON Schema antes de enviar a FPL API
- [ ] **Implementar circuit breaker** para fallos de autenticación
- [ ] **Usar context.Context** con timeouts en todas las llamadas HTTP
- [ ] **No hardcodear** client IDs; hacerlos configurables
- [ ] **Permisos restrictivos** en archivos de configuración (`0o600`)
- [ ] **Audit logging** separado de application logging
- [ ] **Content Security** — validar que las respuestas de FPL no contienen XSS

### 7.2 Arquitectura de Seguridad Propuesta (Go)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FPL MCP SERVER (Go) — Seguridad                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Input Validation                                  │   │
│  │  ├── JSON Schema validation (gojsonschema)                 │   │
│  │  ├── Parameter sanitization (no SQL/NoSQL injection)       │   │
│  │  └── Size limits (max payload 10MB)                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Authentication                                    │   │
│  │  ├── OS Keyring (go-keyring)                               │   │
│  │  ├── Refresh token rotation con persistencia atómica       │   │
│  │  ├── Access token en memoria (nunca en disco)              │   │
│  │  └── Circuit breaker para 401/403                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Caché Segregada                                   │   │
│  │  ├── PublicCache: bootstrap, fixtures, teams (memoria)     │   │
│  │  ├── PrivateCache: my-team, transfers (memoria, TTL 60s)   │   │
│  │  └── NO persistir datos privados en disco                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Audit & Observability                             │   │
│  │  ├── Logs estructurados con slog (redactados)              │   │
│  │  ├── Métricas OpenTelemetry (rate limit hits, cache hits)  │   │
│  │  └── Tracing distribuido para debugging                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│                     https://fantasy.premierleague.com/api            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Conclusión y Próximos Pasos

### Veredicto Final

El MCP server existente (`rishijatia/fantasy-pl-mcp`) es **funcional pero inseguro y difícil de mantener**. Sus problemas de seguridad (encriptación débil, secrets en disco, logging de PII) y su arquitectura (singletons globales, circular imports, mix sync/async) justifican plenamente una reimplementación desde cero en Go.

### Beneficios de Reconstruir en Go

1. **Seguridad**: OS keyring, sin persistencia de datos privados, input validation estricta
2. **Performance**: Binary nativo, caché en memoria, goroutines eficientes
3. **Mantenibilidad**: Dependency injection, structs tipados, tests integrados
4. **Distribución**: Cross-compile para Windows/macOS/Linux sin dependencias

### Riesgos de Reconstruir

1. **Tiempo de desarrollo**: ~2-3 semanas para alcanzar paridad de funcionalidades
2. **Compatibilidad**: Asegurar que los recursos/tools tengan las mismas URIs/firmas
3. **Comunidad**: El proyecto Python tiene usuarios establecidos

---

**Recomendación ejecutiva**: Proceder con la reimplementación en Go, utilizando el codebase Python como referencia funcional pero no como base de código. Priorizar seguridad y arquitectura limpia desde el día 1.
