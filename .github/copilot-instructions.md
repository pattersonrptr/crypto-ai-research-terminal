# Crypto AI Research Terminal — Repository-wide Copilot Instructions

## Project purpose
This is a personal cryptocurrency market intelligence platform powered by AI.
It is NOT a trading bot or price predictor. It researches, scores and explains —
the final decision is always the user's.

## Language & documentation
- All code docstrings must be written in **English**.
- Inline comments may be in **Portuguese (pt-BR)** when clarifying business logic.
- Commit messages follow **Conventional Commits** (see CHANGELOG.md / README.md for the convention).
- The `README.md` must be updated before every commit if the change affects setup, usage or architecture.
- `CHANGELOG.md` must receive an entry for every commit.

## Tech stack — never suggest alternatives unless asked
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Alembic, APScheduler, structlog
- **Databases:** PostgreSQL 15 (primary), Redis (cache/queues), NetworkX (in-memory graph)
- **AI/ML:** Ollama (primary LLM, local), Google Gemini API (fallback), OpenAI GPT-4o (optional),
  LangChain, sentence-transformers, scikit-learn, XGBoost
- **Frontend:** React 18 + TypeScript, Vite, shadcn/ui, TailwindCSS, Recharts, Zustand, Axios + React Query
- **Infra:** Docker + Docker Compose, Nginx (optional), GitHub Actions (CI), act (local CI runner)
- **Package management:** Poetry (never requirements.txt)
- **Virtual env:** `.venv` created with `python -m venv .venv`; always activate with `source .venv/bin/activate` before running anything

## Code quality (enforce on every suggestion)
- Linter/formatter: **Ruff** (replaces flake8 + isort + black)
- Type checker: **Mypy** (strict mode)
- Tests: **Pytest** with **pytest-asyncio** for async code, **pytest-cov** for coverage
- Security: **Bandit**
- Pre-commit hooks run on **pre-push**: ruff, mypy, bandit, pytest
- CI pipeline (`.github/workflows/ci.yml`) mirrors pre-push hooks and can be run locally with **act**

## Architecture rules
- Each module in `backend/app/` must be independently testable.
- No business logic in API route handlers — routes call service/engine functions only.
- All external HTTP calls go through a `BaseCollector` with retry + exponential backoff + rate limiting.
- Configuration comes exclusively from `.env` (loaded via `pydantic-settings`).
- Structured JSON logs via `structlog` in every service.

## File structure
Follow the directory layout defined in `SCOPE.md` section 5. Do not invent new
top-level directories without updating `SCOPE.md` and `TODO.md`.

## Development workflow — Test-Driven Development (TDD)
This project follows strict TDD. This is mandatory, not optional.

**The cycle for every new unit of behaviour:**
1. **Red** — Write a failing test that describes the expected behaviour. Run it and confirm it fails.
2. **Green** — Write the minimum production code needed to make the test pass. Nothing more.
3. **Refactor** — Clean up code and tests without changing behaviour. Re-run tests to confirm green.
4. Commit only after the cycle is complete and all tests pass.

**Rules:**
- Never write production code before a failing test exists for it.
- One behaviour per test. Name tests as `test_<unit>_<scenario>_<expected_outcome>`.
- If implementing a feature would require changing an existing test, stop and reconsider the design.
- Baby steps: each TDD cycle should be completable in a few minutes. If a cycle takes too long, break it down further.

## Testing policy
- Every new module must have a corresponding test file under `backend/tests/`.
- Minimum coverage target: **80%** per module (enforced progressively as modules are implemented).
- Tests must pass locally before any commit is made (`pre-push` hook enforces this).

## Commit convention (Conventional Commits)
See `README.md#commit-convention` for the full spec. Short form:
`<type>(<scope>): <subject>` — types: feat, fix, docs, style, refactor, test, chore, ci.
