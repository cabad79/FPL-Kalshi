# Resumen del Proyecto: Integración y Auditoría de MCP para Kalshi

**Fecha:** 2026-08-12
**Objetivo:** Seleccionar, auditar e integrar de forma segura un servidor MCP para operar/analizar mercados de Kalshi (complemento al análisis estadístico de fútbol Premier League), verificando que no comprometa la cuenta ni las credenciales.

---

## 1. Contexto y pregunta inicial

**Pregunta:** ¿Usar un MCP con Kalshi congela o banea la cuenta?

**Respuesta validada:** No. Un MCP usa la API oficial de Kalshi con API key + firma RSA — Kalshi no distingue entre un MCP y un script propio. El riesgo de suspensión proviene de violar reglas de mercado (wash trades, spoofing, información privilegiada), no de la herramienta. El riesgo real de los MCPs es el **robo de credenciales** con software no auditado, mitigado eligiendo código abierto auditable y fijando versiones.

## 2. Selección del MCP (comparativa GitHub)

| Proyecto | Decisión | Motivo |
|---|---|---|
| **9crusher/mcp-server-kalshi v0.2.3** | ✅ Elegido | Demo por defecto, gate `confirm=true` en órdenes, 50 tests offline, CI completo, credenciales opcionales, firma RSA-PSS correcta |
| BrainDAO/mcp-kalshi | Descartado | Arranca en prod, sin preview de órdenes |
| shaanmajid/prediction-mcp | Descartado | Multi-plataforma, "early development" |
| joinQuantish/kalshi-mcp | ❌ Descartado | Abandonado; opera vía Solana/DFlow con wallets en BD — superficie de ataque enorme |
| pipeworx-io/mcp-kalshi | ❌ Descartado | Gateway remoto: las credenciales salen de la máquina local |

## 3. Auditoría de seguridad (hallazgos)

| ID | Severidad | Hallazgo | Mitigación entregada |
|---|---|---|---|
| H1 | Media | `fetch_rules_pdf` acepta URL arbitraria → riesgo SSRF vía prompt injection | `parche_ssrf_pdf.py` (whitelist de hosts Kalshi, solo HTTPS) |
| M1 | Baja-media | Override de `BASE_URL` puede despistar el entorno demo/prod | Config que evita el override |
| M2 | Baja-media | Clave PEM sin passphrase ni chequeo de permisos | `instalar_seguro.sh` (chmod 600/700) |
| B1 | Baja | Sin rate limiting propio | Espaciar llamadas del agente |
| B2 | Baja | `cancel_order` sin confirmación | Aceptable (reduce exposición) |

**Fortalezas verificadas:** sandbox por defecto, preview de órdenes con costo estimado antes de ejecutar, credenciales con `SecretStr`, validación Pydantic con límites (precio 1–99¢), entorno inyectado en las instructions del MCP (el LLM siempre sabe si está en demo o prod), 50/50 tests pasan, dependencias mínimas y acotadas.

## 4. Análisis de arquitectura

**Diseño en capas limpio** (~1.450 líneas):

```
server.py      → Capa MCP: herramientas, handlers, gates de confirmación
config.py      → Settings Pydantic: demo/prod, credenciales, URLs oficiales
kalshi_client/
  base.py      → HTTP async (httpx) + firma RSA-PSS por request
  client.py    → 20 endpoints Trade API v2 + traductor de órdenes
  schemas.py   → Validación de todas las entradas
  pdf.py       → Extracción de PDFs de reglas de mercado
```

- **Flujo crítico de órdenes:** validación Pydantic → traducción buy/sell+yes/no al modelo V2 de Kalshi → preview obligatorio → firma y envío solo con `confirm=true`.
- **Código más delicado** (traductor de órdenes): bien implementado y el mejor testeado.
- **Oportunidad:** WebSocket configurado pero sin herramientas de streaming (ideal para feeds de precios en tiempo real de mercados de fútbol).

## 5. Verificación del fork del usuario

- **Repositorio:** https://github.com/cabad79/kalshi-dev-mcp
- **Resultado:** ✅ Código 100% idéntico al upstream auditado (commit `867d12c`); diff completo sin diferencias; historial git íntegro; 50/50 tests pasan en la copia local.
- Toda la auditoría aplica directamente al fork.

## 6. Entregables generados

| Archivo | Contenido |
|---|---|
| `INFORME_AUDITORIA.md` | Auditoría completa: comparativa, hallazgos, checklist de instalación segura |
| `ANALISIS_FORK.md` | Verificación del fork + mapa de arquitectura + roadmap |
| `claude_desktop_config.json` | Config MCP lista (versión fijada `==0.2.3`, entorno demo) |
| `.env.example` | Variables endurecidas |
| `instalar_seguro.sh` | Instalación con permisos correctos y versión fijada |
| `parche_ssrf_pdf.py` | Mitigación del hallazgo H1, con pruebas incluidas |

## 7. Checklist operativo pendiente

1. [ ] Ejecutar `instalar_seguro.sh` y colocar la clave privada con `chmod 600`
2. [ ] Configurar el cliente MCP con la versión fijada y `KALSHI_ENV=demo`
3. [ ] Validar en sandbox mínimo una semana antes de considerar prod
4. [ ] Aplicar el parche SSRF como primer commit propio del fork
5. [ ] Activar GitHub Actions (CI ya incluido) en el fork
6. [ ] Al pasar a prod: API key dedicada y revocable solo para el MCP
7. [ ] Regla de oro: toda orden pasa por preview (`confirm=false`) con aprobación humana antes de ejecutar

## 8. Próximos pasos sugeridos

- Herramientas WebSocket para orderbook en tiempo real (mercados de fútbol Premier League)
- Modo `KALSHI_READ_ONLY=true` para fases de puro análisis con cero riesgo de órdenes
- Integración del análisis FPL/scouting con señales de mercados de predicción de Kalshi
