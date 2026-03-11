# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

---

## [0.2.0] — 2026-06-12

### Added

#### Infrastructure
- `infra/docker-compose.yml` — local dev stack: PostgreSQL 15, Redis 7, Ollama, Backend service
- `infra/Dockerfile.backend` — Python 3.13-slim image with Poetry, WeasyPrint and asyncpg deps
- `backend/migrations/` — Alembic initialised with async `env.py` (asyncpg + NullPool)

#### Database models (SQLAlchemy 2.x, `Mapped[]` + `mapped_column()`)
- `app/db/base.py` + `app/db/__init__.py` — shared `DeclarativeBase`
- `app/db/session.py` — `async_sessionmaker` + `get_db` FastAPI dependency
- `app/models/token.py` — `Token` (`tokens` table)
- `app/models/market_data.py` — `MarketData` (`market_data` table)
- `app/models/dev_activity.py` — `DevActivity` (`dev_activity` table)
- `app/models/social_data.py` — `SocialData` (`social_data` table)
- `app/models/signal.py` — `Signal` (`signals` table)
- `app/models/score.py` — `TokenScore` (`token_scores` table)
- `app/models/alert.py` — `Alert` (`alerts` table)

#### Data collection
- `app/collectors/coingecko_collector.py` — `CoinGeckoCollector`: fetches price,
  market cap, volume, rank, ATH, circulating supply from CoinGecko public API;
  inherits `BaseCollector` retry/backoff logic

#### Feature engineering
- `app/processors/normalizer.py` — `clamp()`, `min_max_normalize()`, `normalize_series()`
- `app/processors/market_processor.py` — `MarketProcessor`: `volume_mcap_ratio()`,
  `price_velocity()`, `ath_distance()`, `process()` (now accepts `previous_price: float | None`)

#### Scoring
- `app/scoring/fundamental_scorer.py` — `FundamentalScorer.score()`: static-weight
  composite (volume/mcap 30%, price velocity 25%, ATH distance 25%, market cap 20%)
- `app/scoring/opportunity_engine.py` — `OpportunityEngine.composite_score()`:
  Phase 1 — equals fundamental score; validates [0, 1] range

#### API routes
- `GET /tokens/` — list all tracked tokens (ordered by symbol)
- `GET /tokens/{symbol}` — single token; 404 with detail message if not found
- `GET /rankings/opportunities?limit=N` — tokens ranked by opportunity score DESC

#### CLI
- `app/cli.py` — Click-based CLI group `cryptoai`:
  - `cryptoai top [--n N]` — tabular view of top-N tokens by opportunity score
  - `cryptoai report <SYMBOL>` — detailed single-token report

#### Scheduler
- `app/scheduler/jobs.py` — `daily_collection_job()`: collect → process → score → persist
  pipeline; `_persist_results()` stub (Phase 1: logs only; DB wiring in Phase 2)

#### Tests (TDD — Red → Green → Refactor)
- `tests/models/test_models.py` — 21 tests: tablename, columns, Base inheritance
- `tests/collectors/test_coingecko_collector.py` — 9 tests (respx HTTP mocks)
- `tests/processors/test_market_processor.py` — 14 tests
- `tests/processors/test_normalizer.py` — 12 tests
- `tests/scoring/test_fundamental_scorer.py` — 4 tests
- `tests/scoring/test_opportunity_engine.py` — 5 tests
- `tests/api/test_routes_tokens.py` — 8 tests (FastAPI TestClient + dep overrides)
- `tests/api/test_routes_rankings.py` — 6 tests
- `tests/cli/test_cli.py` — 9 tests (Click CliRunner + patch)
- `tests/scheduler/test_jobs.py` — 5 tests (AsyncMock pipeline verification)

**Total: 95 tests — all passing.**

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
