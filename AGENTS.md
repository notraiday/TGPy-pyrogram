# Repository Guidelines

## Project Structure & Module Organization
- `tgpy/` – core library and runtime code.
- `guide/` – MkDocs documentation sources.
- `docker/` – Docker build files.
- `nix/` – Nix flakes and development shells.
- Tests live in `tests/` (create if missing) and mirror the source layout.

## Build, Test, and Development Commands
- `uv sync --group dev` – install runtime and development dependencies.
- `uv run tgpy` – run the CLI locally.
- `uv run ruff format .` – apply code formatting.
- `uv run ruff check .` – lint the codebase.
- `uv run pytest` – run unit tests.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indentation and 88-character lines.
- Use single quotes for strings (`tool.ruff.format`).
- Modules and functions use `snake_case`; classes use `PascalCase`.
- Keep imports sorted and grouped; run `ruff --select I --fix` to tidy.
- Avoid bare `except:` clauses; always specify the exception type.

## Testing Guidelines
- Use `pytest`; name files `test_*.py` and functions `test_*`.
- Place shared fixtures in `tests/conftest.py`.
- New features should include tests for both success and failure paths.
- Aim for coverage on critical modules; use `pytest -q` for quick runs.

## Commit & Pull Request Guidelines
- Commit messages favor conventional prefixes (`feat:`, `fix:`, `docs:`, `chore:`) followed by an imperative description.
- Group related changes into single commits and keep history clean.
- Before opening a PR, ensure lint and tests pass and documentation is updated.
- PRs should include a concise description, linked issues, and screenshots or logs when relevant.

## Security & Configuration Tips
- Never commit secrets or tokens; use `.env` files ignored by Git.
- Validate user input and handle exceptions explicitly to prevent crashes.

## User Modules Guidance
- Do not use `from __future__ import ...` in user modules. The module loader compiles and executes code in a controlled context and future imports may not be preserved across the eval boundary, causing missing symbols. Prefer standard runtime imports and annotations that work without future flags.
