# syntax=docker/dockerfile:1.3
FROM python:3.13-slim as base
WORKDIR /app

FROM base as builder
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && mv ~/.local/bin/uv /usr/local/bin/
RUN uv venv /venv
ENV PATH="/venv/bin:$PATH"

COPY pyproject.toml uv.lock LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --python /venv/bin/python

COPY . .
RUN sed -i "s/\(COMMIT_HASH *= *\).*/\1'$(git rev-parse HEAD)'/" tgpy/version.py
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
