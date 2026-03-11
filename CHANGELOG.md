# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

---

## [0.1.0] — 2026-03-11

### Added

#### Project scaffold & quality tooling
- `pyproject.toml` — Poetry-based project with full dependency specification:
  - Runtime: FastAPI, SQLAlchemy 2.x (async), Alembic, asyncpg, Redis, APScheduler,
    structlog, httpx, tenacity, LangChain, sentence-transformers, scikit-learn,
    XGBoost, NetworkX, Jinja2, WeasyPrint, Typer
  - Dev group: pytest, pytest-asyncio, pytest-cov, pytest-httpx, respx,
    factory-boy, Ruff, Mypy, Bandit, pre-commit
- `.pre-commit-config.yaml` — pre-push hooks: Ruff lint + format, Mypy, Bandit, Pytest
- `.gitignore` — Python, Poetry, Docker, IDE, frontend artefacts
- `.env.example` — all required environment variables with comments

#### GitHub Copilot custom instructions
- `.github/copilot-instructions.md` — repo-wide instructions: stack, code quality,
  architecture rules, commit convention, testing policy
- `.github/instructions/python-backend.instructions.md` — path-specific (Python files)
- `.github/instructions/react-frontend.instructions.md` — path-specific (TS/TSX files)

#### CI/CD
- `.github/workflows/ci.yml` — two-job pipeline:
  - `quality`: Ruff lint, Ruff format check, Mypy, Bandit
  - `test`: Pytest with coverage (requires PostgreSQL 15 + Redis services)
  - Compatible with `act` for local execution

#### Project skeleton (SCOPE.md §5)
- Full `backend/app/` directory tree with stub modules for all 14 subsystems:
  `api`, `collectors`, `processors`, `signals`, `ai`, `graph`, `ml`,
  `scoring`, `risk`, `alerts`, `reports`, `backtesting`, `scheduler`, `models`
- `backend/tests/` mirroring the `app/` structure
- `frontend/src/` with `components/`, `pages/`, `hooks/`, `services/`, `store/`
- `infra/nginx/`, `scripts/`, `data/historical/`

#### Core backend stubs (real code, not empty)
- `backend/app/main.py` — FastAPI app with router registration and `/health` endpoint
- `backend/app/config.py` — `Settings` class via pydantic-settings; all env vars
- `backend/app/exceptions.py` — domain exception hierarchy
- `backend/app/collectors/base_collector.py` — abstract `BaseCollector` with
  httpx + tenacity retry + exponential backoff + structlog

#### Tests
- `backend/tests/test_main.py` — smoke test for `/health` endpoint
- `backend/tests/collectors/test_base_collector.py` — BaseCollector instantiation test

#### Documentation
- `README.md` — full rewrite: badges, what it does, tech stack, setup guide,
  code quality commands, act instructions, commit convention, roadmap table
- `TODO.md` — phased roadmap with all tasks from SCOPE.md §10 (Phases 1–7)
- `CHANGELOG.md` — this file

#### Translation
- `SCOPE.md` — English translation of the original Portuguese technical scope document

[0.1.0]: https://github.com/pattersonrptr/crypto-ai-research-terminal/releases/tag/v0.1.0
