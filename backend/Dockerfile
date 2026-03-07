# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Build-time deps: gcc + libpq-dev para compilar extensões C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .

# --no-compile evita .pyc durante install; cleanup agressivo reduz tamanho final
RUN pip install --no-cache-dir --user --no-compile -r requirements-prod.txt \
    # Bytecode e caches
    && find /root/.local -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete \
    && find /root/.local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true \
    # Diretórios de teste dos pacotes
    && find /root/.local -type d \( -name "tests" -o -name "test" -o -name "testing" \) \
    -exec rm -rf {} + 2>/dev/null; true \
    # Type stubs (não necessários em runtime)
    && find /root/.local -name "*.pyi" -delete \
    # Google API discovery cache: 93 MB de JSON para TODAS as APIs Google
    # O cliente re-faz o download em runtime se necessário (apenas 1ª chamada)
    && rm -rf /root/.local/lib/python3.11/site-packages/googleapiclient/discovery_cache/
# NOTA: .dist-info e .egg-info foram mantidos pois importlib.metadata os usa em runtime (ex: Celery/click_repl)


# ── Stage 2: Production ───────────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Apenas curl para o healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuário não-root (UID 1000)
RUN useradd -m -u 1000 logia

# Copiar pacotes limpos do builder para o home do logia
COPY --from=builder /root/.local /home/logia/.local

WORKDIR /app

# Código da aplicação + migrations
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN chown -R logia:logia /app

ENV PATH=/home/logia/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER logia

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
