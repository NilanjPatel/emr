FROM python:3.12-slim

WORKDIR /app

# Build tools needed to compile cryptography from source (avoids ARM64/PMULL crash)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev cargo pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY pyproject.toml .python-version ./

# Install production deps — compile cryptography from source for arm64 compatibility
RUN uv sync --no-dev --no-editable \
    --config-setting=no-binary=cryptography

COPY app/ ./app/

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
