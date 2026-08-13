# Dockerfile - FPL MCP v2 (servidor propio, arquitectura en capas)
# Ejecuta sobre stdio transport (MCP estándar) — requiere stdin_open/tty en docker-compose.

FROM python:3.11-slim-bookworm

# ─── Seguridad: no correr como root ──────────────────────────────────
RUN groupadd -r fplmcp && useradd -r -g fplmcp -d /app -s /bin/bash fplmcp

WORKDIR /app

# ─── Instalar dependencias primero (cache de capas) ──────────────────
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ─── Variables de entorno por defecto ────────────────────────────────
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FPL_OIDC_CLIENT_ID=""

RUN mkdir -p /app/.credentials && chown -R fplmcp:fplmcp /app

USER fplmcp

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import fpl_mcp; print('OK')" || exit 1

ENTRYPOINT ["python", "-m", "fpl_mcp"]
