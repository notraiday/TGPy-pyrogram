# AGENTS

## Project layout

- Core runtime code lives in `tgpy/`.
- MkDocs documentation lives in `guide/`.
- Docker and Nix support files live in `docker/` and `nix/`.
- Tests should live in `tests/` and mirror the source layout.

## Development commands

- Install dependencies with `uv sync --group dev`.
- Run the local CLI with `uv run tgpy`.
- Format code with `uv run ruff format .`.
- Lint code with `uv run ruff check .`.
- Run tests with `uv run pytest`.

## Python conventions

- Follow the project's Ruff configuration, including single-quoted strings.
- Use `snake_case` for modules and functions, and `PascalCase` for classes.
- Keep imports sorted; use `uv run ruff check --select I --fix .` when needed.
- Avoid bare `except:` clauses; catch explicit exception types.

## User modules

- Do not use `from __future__ import ...` in user modules.
- The module loader compiles and executes code in a controlled context, so future imports may not survive the eval boundary. Prefer runtime imports and annotations that work without future flags.
