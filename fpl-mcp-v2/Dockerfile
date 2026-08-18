# Multi-stage build for Kalshi Football Markets MCP v0.4.0
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY fpl-mcp-v2/pyproject.toml pyproject.toml
COPY fpl-mcp-v2/src/ src/
COPY fpl-mcp-v2/tests/ tests/

# Build wheel
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/*

# Copy application code
COPY fpl-mcp-v2/src/ src/
COPY fpl-mcp-v2/tests/ tests/
COPY fpl-mcp-v2/pyproject.toml pyproject.toml
COPY models/ ./models/

# Install application in development mode
RUN pip install -e .

# Create non-root user for security
RUN useradd -m -u 1000 kalshi && chown -R kalshi:kalshi /app
USER kalshi

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port for MCP server
EXPOSE 8000

# Environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV KALSHI_API_URL=https://api.kalshi.com
ENV LOG_LEVEL=INFO

# Start the MCP server
CMD ["fpl-mcp-v2", "--host", "0.0.0.0", "--port", "8000"]
