# -- Stage 1: builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Dependências de sistema para compilar pacotes nativos
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir ".[dev]" --prefix=/install

# -- Stage 2: runtime
FROM python:3.11-slim AS runtime

# Dependências de sistema para Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium dependencies
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxshmfence1 \
    fonts-liberation \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar pacotes instalados do builder
COPY --from=builder /install /usr/local

# Instalar Playwright e Chromium
RUN playwright install chromium && \
    playwright install-deps chromium

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY app/ ./app/

# Logs
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
