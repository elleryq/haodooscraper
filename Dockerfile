FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install locked dependencies first so this layer is cached across code changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
    OPENSHIFT_PYTHON_IP=0.0.0.0 \
    OPENSHIFT_PYTHON_PORT=8000

EXPOSE 8000
CMD ["python", "wsgi/application"]
