# syntax=docker/dockerfile:1.3
FROM python:3.14-slim as base
WORKDIR /app

FROM base as builder
ARG COMMIT_HASH=""
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cargo curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv ~/.local/bin/uv /usr/local/bin/ \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN uv venv /venv
ENV PATH="/venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT="/venv"

COPY pyproject.toml uv.lock LICENSE README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --python /venv/bin/python

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --python /venv/bin/python
RUN if [ -n "$COMMIT_HASH" ]; then sed -i "s/\(COMMIT_HASH *= *\).*/\1'$COMMIT_HASH'/" tgpy/version.py; fi
RUN rm -rf .git guide uv.lock pyproject.toml .dockerignore .gitignore README.md

FROM base as runner
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:$PATH"

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --from=builder /app /app
ENV TGPY_DATA=/data
ENV PYTHONPATH=/app
VOLUME /data
ENTRYPOINT ["/app/entrypoint.sh"]
