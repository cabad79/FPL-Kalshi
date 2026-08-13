# Auditoría de seguridad e integración: MCP para Kalshi

**Fecha:** 2026-08-12
**Proyecto auditado:** `9crusher/mcp-server-kalshi` v0.2.3 (commit `867d12c`, 2026-07-27)
**Veredicto:** ✅ Apto para usar, con las mitigaciones indicadas abajo.

---

## 1. Por qué este proyecto y no otros

Se compararon los principales MCP de Kalshi en GitHub:

| Proyecto | Evaluación |
|---|---|
| **9crusher/mcp-server-kalshi** ⭐ elegido | Demo por defecto, gate de confirmación en órdenes, tests offline (50/50 pasan), CI con lint+tipos, credenciales opcionales, firma RSA-PSS correcta |
| BrainDAO/mcp-kalshi (@iqai) | Correcto, pero arranca apuntando a prod y sin preview de órdenes |
| shaanmajid/prediction-mcp | Multi-plataforma (Kalshi+Polymarket), "early development" |
| joinQuantish/kalshi-mcp | ❌ Proyecto abandonado, opera vía DFlow/Solana (no la API oficial), maneja wallets y claves cripto en una base de datos — superficie de ataque enorme |
| pipeworx-io/mcp-kalshi | ❌ Gateway remoto de terceros: tus credenciales saldrían de tu máquina |

## 2. Qué hace bien (validado en el código)

- **Sandbox por defecto:** `KALSHI_ENV=demo` es el default; producción requiere opt-in explícito (`config.py`).
- **Gate de confirmación:** `create_order` y `amend_order` devuelven un *preview* con costo estimado y NO ejecutan nada salvo `confirm=true` (`server.py:515`).
- **Clave nunca sale de tu máquina:** la RSA privada solo se usa localmente para firmar (RSA-PSS/SHA-256, esquema correcto según docs de Kalshi). Los headers firmados son los oficiales.
- **Credenciales con `SecretStr`:** no se imprimen en logs ni reprs.
- **Validación de entrada:** esquemas Pydantic con límites (precio 1–99¢, count > 0), y anotaciones MCP `readOnly`/`destructive` correctas.
- **Tests y CI serios:** suite offline completa (50 tests), ruff/black/mypy en CI, dependencias acotadas (`mcp>=1.28.1,<2`).
- **Sin dependencias sospechosas:** solo mcp, httpx, cryptography, pypdf, pydantic.

## 3. Hallazgos y mitigaciones

### H1 — SSRF en `fetch_rules_pdf` (medio)
Acepta una `url` arbitraria y descarga el contenido. Un prompt injection podría hacer que el agente lea URLs internas (metadata cloud, localhost).
**Mitigación:** aplicar `parche_ssrf_pdf.py` (incluido) que restringe a hosts de Kalshi vía HTTPS.

### M1 — Override de `BASE_URL` puede despistar (bajo-medio)
Si alguien configura `BASE_URL` manual, `is_production` lo infiere por la cadena "demo". Un apuntador malicioso podría redirigir tus credenciales firmadas a otro servidor.
**Mitigación:** no usar `BASE_URL`; dejar que `KALSHI_ENV` derive la URL oficial (ya configurado así en `.env.example`).

### M2 — Clave privada sin passphrase y sin chequeo de permisos (bajo-medio)
El loader abre el PEM sin contraseña y no verifica permisos del archivo.
**Mitigación:** el script `instalar_seguro.sh` fuerza `chmod 600` sobre la clave y `700` sobre el directorio.

### B1 — Sin rate limiting propio
El servidor no limita ráfagas; exceder los límites de tu tier en Kalshi genera 429 (no ban), pero conviene que el agente espacie llamadas.

### B2 — `cancel_order` no pide confirmación
Es destructivo pero reduce exposición; riesgo aceptable.

## 4. ¿Riesgo de ban por usar este MCP? No

Kalshi no distingue entre este MCP y un script propio: ambos usan la API oficial con tu API key firmada con RSA. El riesgo de suspensión viene de violar reglas de mercado (wash trades, spoofing, información privilegiada), no de la herramienta. El riesgo real de un MCP es el **robo de credenciales** si el código fuera malicioso — por eso se eligió un proyecto auditable, pequeño (~1.450 líneas) y con versión fijada.

## 5. Checklist de instalación segura

1. `bash instalar_seguro.sh` — crea `~/.kalshi` con permisos y fija la versión.
2. Clave privada en `~/.kalshi/private-key.pem` con `chmod 600`.
3. Config del cliente: usar `claude_desktop_config.json` incluido — versión fijada `mcp-server-kalshi==0.2.3`, `KALSHI_ENV=demo`.
4. Nunca commitear `.env` ni el PEM; nunca pegarlos en chats ni en MCPs de terceros.
5. Validar en demo durante al menos una semana antes de `KALSHI_ENV=prod`.
6. Al pasar a prod: usa una API key dedicada solo para el MCP (revocable sin afectar tu cuenta), y aplica el parche SSRF si compilas desde fuente.
7. Regla operativa para el agente: toda orden pasa por el preview (`confirm=false`) y un humano aprueba antes de re-ejecutar con `confirm=true`.

## 6. Archivos de esta integración

| Archivo | Propósito |
|---|---|
| `claude_desktop_config.json` | Config lista para Claude Desktop / Cursor (versión fijada, demo) |
| `.env.example` | Variables endurecidas |
| `instalar_seguro.sh` | Instalación con permisos correctos y versión fijada |
| `parche_ssrf_pdf.py` | Mitigación del hallazgo H1 (incluye pruebas) |
