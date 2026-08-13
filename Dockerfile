# Dockerfile - MCP Kalshi (Seguro)
# Basado en la auditoría de seguridad del 2026-08-12
# Repositorio: 9crusher/mcp-server-kalshi v0.2.3

FROM python:3.12-slim-bookworm

# ─── Seguridad: no correr como root ──────────────────────────────────
RUN groupadd -r kalshi && useradd -r -g kalshi -d /app -s /bin/bash kalshi

# ─── Dependencias del sistema ────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ─── Directorio de trabajo ───────────────────────────────────────────
WORKDIR /app

# ─── Clonar el repositorio auditado (versión fijada) ─────────────────
# Commit auditado: 867d12c (v0.2.3)
RUN git clone --depth 1 --branch v0.2.3 https://github.com/9crusher/mcp-server-kalshi.git . 2>/dev/null || \
    (git init && git remote add origin https://github.com/9crusher/mcp-server-kalshi.git && \
     git fetch --depth 1 origin v0.2.3 && git checkout FETCH_HEAD)

# ─── Instalar dependencias Python ────────────────────────────────────
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir \
        mcp>=1.28.1,<2 \
        httpx \
        cryptography \
        pypdf \
        pydantic \
        pydantic-settings

# ─── Copiar parches de seguridad ─────────────────────────────────────
# El parche SSRF se copiará desde el host si existe
COPY parche_ssrf_pdf.py /tmp/parche_ssrf_pdf.py

# ─── Aplicar parche SSRF si existe ───────────────────────────────────
RUN if [ -f /tmp/parche_ssrf_pdf.py ]; then \
        python /tmp/parche_ssrf_pdf.py --check || \
        (echo "⚠️ Parche SSRF no aplicado automáticamente. Aplicar manualmente."); \
    fi

# ─── Crear directorio para credenciales ──────────────────────────────
RUN mkdir -p /app/.kalshi && \
    chown -R kalshi:kalshi /app && \
    chmod 700 /app/.kalshi

# ─── Variables de entorno por defecto (seguras) ──────────────────────
ENV KALSHI_ENV=demo
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ─── Healthcheck ─────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_server_kalshi; print('OK')" || exit 1

# ─── Usuario no-root ─────────────────────────────────────────────────
USER kalshi

# ─── Puerto (si se usa modo HTTP/SSE en el futuro) ───────────────────
EXPOSE 8080

# ─── Entrypoint ──────────────────────────────────────────────────────
ENTRYPOINT ["python", "-m", "mcp_server_kalshi"]
