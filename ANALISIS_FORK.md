# Análisis completo del fork: cabad79/kalshi-dev-mcp

**Fecha:** 2026-08-12
**Repositorio:** https://github.com/cabad79/kalshi-dev-mcp
**Resultado de verificación:** ✅ Código 100% idéntico al upstream auditado (commit `867d12c` de `9crusher/mcp-server-kalshi`, v0.2.3). Diff archivo-por-archivo sin diferencias. Tests: **50/50 pasan**.

---

## 1. Verificación de integridad del fork

| Verificación | Resultado |
|---|---|
| Diff completo vs upstream (`867d12c`) | Sin diferencias en ningún archivo |
| Último commit | `867d12c` — "Merge pull request #9 from 9crusher/bump-deps" |
| Suite de tests offline | 50/50 pasan en tu copia |
| Historial git | Íntegro, sin commits extraños ni force-pushes |
| Conclusión | Tu fork hereda exactamente la auditoría previa: mismo veredicto de seguridad, mismos hallazgos (H1 SSRF, M1, M2) y mismas mitigaciones |

## 2. Mapa de arquitectura

```
src/mcp_server_kalshi/
├── server.py          (619 líneas) — Capa MCP: registro de herramientas, handlers,
│                        instrucciones dinámicas al LLM, gates de confirmación
├── config.py          (84 líneas)  — Settings con Pydantic: entorno demo/prod,
│                        credenciales SecretStr, derivación de URLs oficiales
└── kalshi_client/
    ├── base.py        (172 líneas) — HTTP async (httpx) + firma RSA-PSS por request
    ├── client.py      (230 líneas) — 20 endpoints de la Trade API v2 + traductor
    │                                 de órdenes intuitivas (buy/sell yes/no → payload V2)
    ├── schemas.py     (305 líneas) — Validación Pydantic de todas las entradas
    └── pdf.py         (32 líneas)  — Descarga y extracción de PDFs de reglas
```

**Diseño en capas limpio:** el servidor MCP nunca toca HTTP directamente; pasa por `schemas` (validación) → `client` (endpoints) → `base` (transporte firmado). Separación correcta de responsabilidades.

### Flujo de una orden (trayecto crítico de seguridad)

```
LLM llama create_order
  → CreateOrderRequest (Pydantic: precio 1-99¢, count>0)   [schemas.py]
  → build_create_order_payload (traduce buy/sell+yes/no    [client.py]
    al modelo V2 de Kalshi: book side bid/ask, YES-leg)
  → ¿confirm=false? → devuelve PREVIEW con costo estimado  [server.py:515]
  → ¿confirm=true?  → KalshiAuth firma timestamp+method+path [base.py]
                    → POST firmado a /portfolio/orders
```

### Detalle arquitectónico destacable

El servidor **inyecta el entorno activo (demo/prod) en las `instructions` del MCP** (`server.py:55`). Como las instructions están siempre en el contexto del modelo, el LLM no puede "asumir" que está en demo — es una defensa bien pensada contra errores de dinero real. Pocos MCPs de trading hacen esto.

### Traductor de órdenes (pieza más delicada)

`build_create_order_payload` convierte el modelo intuitivo (buy/sell + yes/no + precio en centavos) al modelo de libro de Kalshi V2 (side bid/ask sobre la pierna YES, precio en dólares). La equivalencia buy NO @ p ≡ sell YES @ 100−p está bien implementada y cubierta por `tests/test_orders.py`. Es el código donde un bug costaría dinero real — y está bien testeado.

## 3. Hallazgos de seguridad (heredados, con estado)

| ID | Severidad | Hallazgo | Mitigación |
|---|---|---|---|
| H1 | Media | `fetch_rules_pdf` acepta URL arbitraria → SSRF | `parche_ssrf_pdf.py` (incluido) |
| M1 | Baja-media | `BASE_URL` override puede despistar el entorno | No usar el override; config ya lo evita |
| M2 | Baja-media | PEM sin passphrase ni chequeo de permisos | `instalar_seguro.sh` (chmod 600/700) |
| B1 | Baja | Sin rate limiting propio | Espaciar llamadas del agente |
| B2 | Baja | `cancel_order` sin confirmación | Aceptable (reduce exposición) |

## 4. Observaciones menores de arquitectura

- **Estado global en importación:** `settings` y `kalshi_client` se construyen al importar `server.py`. Funciona para stdio, pero dificulta tests de integración con distintas configs (lo resuelven parcheando en tests).
- **Cliente HTTP persistente con creación lazy:** correcto para stdio de larga duración; el cierre (`aclose`) existe pero el proceso stdio normalmente termina por señal — riesgo menor de conexiones colgadas.
- **WebSocket definido pero sin herramientas:** `ws_base_url` existe en config pero no hay tools de streaming. Oportunidad de mejora (feeds de precios en tiempo real).
- **Dependencias bien acotadas:** solo 6 runtime deps, todas mantenidas; `mcp` fijado a `<2` evita breaking changes.

## 5. Roadmap sugerido para tu fork

1. **Aplicar el parche SSRF** (`parche_ssrf_pdf.py`) y subirlo como primer commit propio
2. **Añadir test de regresión** para el parche (el repo tiene buena cultura de tests — mantenerla)
3. **GitHub Actions ya incluidas** (`ci.yml`): actívalas en tu fork para que cada push corra lint+tipos+tests
4. **Opcional — herramientas WebSocket** para orderbook en tiempo real (útil para tu análisis de mercados de fútbol: detectar movimientos de precio en mercados de Premier League)
5. **Opcional — modo read-only**: una variable `KALSHI_READ_ONLY=true` que desregistre las tools de trading, para fases de puro análisis con cero riesgo de órdenes accidentales
