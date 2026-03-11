---
applyTo: "backend/**/*.py"
---

# Python backend instructions

## Style
- Use **type annotations** on every function signature and variable declaration where type is non-obvious.
- Use **async/await** for all I/O-bound operations (DB, HTTP, file).
- Prefer `dataclasses` or `pydantic` models over plain dicts for structured data.
- Keep functions short (< 40 lines). Extract helpers when logic grows.

## Imports
- Always use **absolute imports** within the `app` package (e.g., `from app.collectors.base_collector import BaseCollector`).
- Group imports: stdlib → third-party → internal, separated by blank lines. Ruff will enforce this.

## Error handling
- Never swallow exceptions silently. Log with `structlog` before re-raising or returning a safe default.
- Use custom exception classes defined in `app/exceptions.py` for domain errors.

## Database
- All DB access must be async (`async with session` / `await session.execute(...)`).
- Never instantiate a session directly in business logic — use FastAPI dependency injection.
- Alembic migrations must be created for every schema change. Never use `create_all()` in production code.

## Testing
- Mirror the `app/` structure inside `tests/` (e.g., `tests/collectors/test_coingecko_collector.py`).
- Use `pytest-asyncio` with `asyncio_mode = "auto"` for async tests.
- Mock all external HTTP calls with `pytest-httpx` or `respx`.
- Each test file must import only from `app.*` — no cross-test imports.
