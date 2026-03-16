# 🧠 Crypto AI Research Terminal

> Personal AI-powered cryptocurrency market intelligence platform.
> **Not** a trading bot. Not a price predictor. A research assistant.

[![CI](https://github.com/pattersonrptr/crypto-ai-research-terminal/actions/workflows/ci.yml/badge.svg)](https://github.com/pattersonrptr/crypto-ai-research-terminal/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

- [What it does](#what-it-does)
- [Tech Stack](#tech-stack)
- [Project Setup](#project-setup)
- [Running locally](#running-locally)
- [Code Quality](#code-quality)
- [Running CI checks locally](#running-ci-checks-locally)
- [Opening a Pull Request](#opening-a-pull-request)
- [Commit Convention](#commit-convention)
- [Project Roadmap](#project-roadmap)

---

## What it does

- Fundamental analysis of Top 300 altcoins (technology, tokenomics, team, adoption)
- Detection of emerging market narratives via embeddings + clustering
- Listing radar: probability scores for tier-1 exchange listings
- Whale and institutional activity detection
- Risk alerts (rugpull, manipulation, token unlocks)
- Bitcoin cycle monitoring + altseason estimation
- Backtesting the model against historical cycles (2017, 2020–2021)
- Reports in Markdown / PDF + Telegram alerts

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, APScheduler, structlog |
| Databases | PostgreSQL 15, Redis |
| AI / ML | Ollama, Gemini API, OpenAI GPT-4o, LangChain, sentence-transformers, scikit-learn, XGBoost |
| Graph | NetworkX |
| Frontend | React 18 + TypeScript, Vite, shadcn/ui, TailwindCSS, Recharts, Zustand, Axios + React Query |
| Infra | Docker + Docker Compose, Nginx (optional), GitHub Actions |
| Quality | Ruff, Mypy (strict), Bandit, Pytest, pytest-asyncio, pytest-cov |
| Package mgmt | Poetry |
| Local CI | [act](https://github.com/nektos/act) |

---

## Project Setup

### Prerequisites

- Docker + Docker Compose (**recommended path — everything runs in containers**)
- Python 3.11+ + [Poetry](https://python-poetry.org/docs/#installation) *(dev-only path)*
- Node.js 22+ + npm *(dev-only path)*
- (Optional) [act](https://github.com/nektos/act) — to run the CI pipeline locally

---

## Running with Docker *(recommended)*

This is the standard way to run the project. All services — PostgreSQL, Redis,
FastAPI backend, and the React frontend (served by nginx) — start with a single
command.

### 1 — Clone and configure environment

```bash
git clone https://github.com/pattersonrptr/crypto-ai-research-terminal.git
cd crypto-ai-research-terminal

cp .env.example .env
# Edit .env — fill in API keys (CoinGecko, GitHub, Telegram, etc.)
```

#### Twitter/X setup (for social data collection — Phase 13+)

The system uses [`twikit`](https://github.com/d60/twikit) to collect Twitter/X
data **for free** (no paid API required). You need a regular X account:

```env
# .env — add your X credentials
TWITTER_USERNAME=your_x_username
TWITTER_EMAIL=your_x_email@example.com
TWITTER_PASSWORD=your_x_password
```

> **Note:** twikit uses session cookies. After the first login, cookies are
> persisted so your credentials aren't sent repeatedly. The account is only
> used for reading — no tweets are posted.

### 2 — Start all services

```bash
# Build images and start in the background (first run takes ~2 min to build)
docker compose -f infra/docker-compose.yml up -d postgres redis backend frontend

# Check that all containers are healthy
docker compose -f infra/docker-compose.yml ps
```

Expected output:

```
NAME                STATUS
cryptoai_postgres   Up (healthy)
cryptoai_redis      Up (healthy)
cryptoai_backend    Up (healthy)
cryptoai_frontend   Up
```

### 3 — Access the application

| Service | URL |
|---|---|
| **Frontend (React dashboard)** | http://localhost:3000 |
| **Backend API docs (Swagger)** | http://localhost:8000/docs |
| **Backend health check** | http://localhost:8000/health |

> The nginx container at port 3000 also proxies all `/api/*` requests to the
> backend, so `http://localhost:3000/api/health` works too.

### 4 — Run database migrations (first run only)

```bash
# Inside the backend container
docker compose -f infra/docker-compose.yml exec backend alembic upgrade head
```

### 5 — (Optional) Start Ollama for local LLM

```bash
# Only needed if you have an NVIDIA GPU — remove the `deploy` block otherwise
docker compose -f infra/docker-compose.yml up -d ollama

# Pull a model (example: llama3.2)
docker compose -f infra/docker-compose.yml exec ollama ollama pull llama3.2
```

### Stop everything

```bash
docker compose -f infra/docker-compose.yml down

# Also remove volumes (wipes the database)
docker compose -f infra/docker-compose.yml down -v
```

### Rebuild after code changes

```bash
docker compose -f infra/docker-compose.yml build backend frontend
docker compose -f infra/docker-compose.yml up -d backend frontend
```

### Populate the database (manual collection)

Trigger the full collection → scoring → persistence pipeline on demand:

```bash
# Inside the backend container
docker compose -f infra/docker-compose.yml exec backend python -m app.cli collect-now
# Output: "Done — N tokens collected, scored and persisted."
```

You can also trigger collection from the **GUI**: click the **"Collect Now"**
button in the top-right corner of the Rankings page. It shows a spinner
while running and a status message when done.

> The scheduler also runs `daily_collection_job` automatically, but `collect-now`
> lets you populate the DB immediately after a fresh deploy.

### Seed data (optional — disabled by default)

By default, the backend starts with an **empty database**. Seed data is
controlled by the `AUTO_SEED` environment variable in `.env`:

```env
# .env
AUTO_SEED=false   # (default) — no seed data on container start
AUTO_SEED=true    # seeds sample tokens on container start (for development/demos)
```

To manually seed the database:

```bash
# Seed all sample data (rankings + narratives)
docker compose -f infra/docker-compose.yml exec backend python -m app.cli seed all

# Seed only rankings data
docker compose -f infra/docker-compose.yml exec backend python -m app.cli seed rankings

# Seed only narratives data
docker compose -f infra/docker-compose.yml exec backend python -m app.cli seed narratives
```

### Database management

```bash
# Show row counts per table
docker compose -f infra/docker-compose.yml exec backend python -m app.cli db-status

# Truncate ALL data tables (requires --confirm flag)
docker compose -f infra/docker-compose.yml exec backend python -m app.cli db-clean --confirm

# Truncate a specific table (requires --confirm flag)
docker compose -f infra/docker-compose.yml exec backend python -m app.cli db-truncate tokens --confirm
docker compose -f infra/docker-compose.yml exec backend python -m app.cli db-truncate market_data --confirm
docker compose -f infra/docker-compose.yml exec backend python -m app.cli db-truncate narratives --confirm

# Allowed tables: tokens, token_scores, market_data, narratives, alerts,
#                 social_data, dev_activity, signals, ai_analyses,
#                 historical_snapshots
```

> **Tip:** Use `db-clean` before switching between seed data and real data
> to avoid mixing them.

### Production deployment

Use the production overlay to apply resource limits, remove host-exposed DB ports,
and enforce `restart: always`:

```bash
docker compose \
  -f infra/docker-compose.yml \
  -f infra/docker-compose.prod.yml \
  up -d
```

---

## Running locally (dev mode, without Docker)

Use this mode when iterating quickly on backend or frontend code.

### Backend

```bash
# 1 — Start infrastructure only
docker compose -f infra/docker-compose.yml up -d postgres redis

# 2 — Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --with dev

# 3 — Configure environment
cp .env.example .env
# Set DATABASE_URL=postgresql+asyncpg://cryptoai:cryptoai@localhost:5433/cryptoai
# Set REDIS_URL=redis://localhost:6379

# 4 — Run migrations
cd backend && alembic upgrade head && cd ..

# 5 — Start the backend (hot-reload)
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install           # first time only
npm run dev           # http://localhost:3000

# The Vite dev server proxies /api → http://localhost:8000 automatically
```

#### Frontend environment variable (optional)

```bash
# frontend/.env.local — only needed if backend runs on a non-default port
VITE_API_BASE_URL=http://localhost:8000
```

#### Running frontend tests

```bash
cd frontend
npm test              # single run (126 tests)
npm run test:watch    # watch mode
npm run test:coverage # with coverage report
```

#### Running backend tests

```bash
source .venv/bin/activate
pytest                        # all 802 tests + coverage
pytest backend/tests/ -q      # quiet mode
```

---

## Code Quality

All checks run automatically on `git push` via pre-commit hooks.

```bash
source .venv/bin/activate

# Lint + format
ruff check backend/ --fix
ruff format backend/

# Type check
mypy backend/app

# Security scan
bandit -c pyproject.toml -r backend/app

# Tests with coverage
pytest
```

---

## Running CI checks locally

**Always run this before opening a PR** to catch errors before they reach GitHub.

### Option 1 — `ci-local.sh` script (recommended)

```bash
./scripts/ci-local.sh          # check only
./scripts/ci-local.sh --fix    # auto-fix ruff issues, then check
```

This mirrors `.github/workflows/ci.yml` exactly, in the same order:

| Job | Step | Tool | What it checks |
|---|---|---|---|
| `quality` | 1/4 | `ruff check` | Lint rules (unused imports, style, security patterns) |
| `quality` | 2/4 | `ruff format --check` | Code formatting |
| `quality` | 3/4 | `mypy backend/app` | Static type checking (strict mode) |
| `quality` | 4/4 | `bandit` | Security vulnerabilities |
| `test` | 1/1 | `pytest` | Tests + coverage threshold |

> **Note:** Activate the virtual environment first:
> `source .venv/bin/activate`

### Option 2 — run checks individually

```bash
source .venv/bin/activate

ruff check backend/ --fix       # lint (with auto-fix)
ruff format backend/            # format (with auto-fix)
mypy backend/app                # type check
bandit -c pyproject.toml -r backend/app -q   # security
pytest backend/tests/ --tb=short -q          # tests + coverage
```

### Option 3 — `act` (full GitHub Actions simulation)

[act](https://github.com/nektos/act) runs `.github/workflows/ci.yml` inside
Docker — byte-for-byte identical to what runs on GitHub.

```bash
# Install act (Arch Linux)
yay -S act

# Run the full CI pipeline
act push

# Run only the quality job
act push -j quality
```

> **Note:** act requires Docker. First run downloads the `ubuntu-22.04` image (~1.5 GB).

### Common Ruff errors and how to fix them

| Code | Description | Fix |
|---|---|---|
| `F401` | Unused import | Remove the import |
| `B008` | `Query()` in function default | Use `Annotated[T, Query()]` as type hint |
| `E501` | Line too long (> 100 chars) | Break the line |
| `UP017` | Use `datetime.UTC` instead of `timezone.utc` | Replace `timezone.utc` → `UTC` |
| `I001` | Unsorted imports | Run `ruff check --fix` |

---

## Opening a Pull Request

**Never use `gh pr create` directly.** Use `create-pr.sh` instead — it runs
`ci-local.sh` automatically and only opens the PR if all checks pass.

```bash
./scripts/create-pr.sh \
  --title "feat(scope): short description" \
  --body "What and why." \
  --base main
```

### Options

| Flag | Description |
|---|---|
| `--title` | **(required)** PR title — follow Conventional Commits |
| `--body` | PR body as a string |
| `--body-file` | PR body from a file (e.g. `pr-body.md`) |
| `--base` | Target branch (default: `main`) |
| `--skip-ci` | Skip local CI — **strongly discouraged** |

### What the script does

1. Verifies `gh` is installed and authenticated
2. Runs `./scripts/ci-local.sh` — aborts if any check fails
3. Pushes the current branch to `origin`
4. Calls `gh pr create` with the provided arguments

### PR checklist (enforced by `create-pr.sh`)

- [x] `ruff check` — no lint errors
- [x] `ruff format --check` — code is formatted
- [x] `mypy backend/app` — no type errors (strict mode)
- [x] `bandit` — no security issues
- [x] `pytest` — all tests pass, coverage threshold met
- [ ] `TODO.md` updated (manual check)
- [ ] `CHANGELOG.md` updated (manual check)
- [ ] PR title follows Conventional Commits (manual check)

---

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

### Types

| Type | When to use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting (no logic change) |
| `refactor` | Code change that is neither a fix nor a feature |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks (dependencies, config) |
| `ci` | Changes to CI/CD pipeline |

### Scopes (examples)

`collectors`, `scoring`, `ai`, `graph`, `ml`, `risk`, `alerts`, `reports`,
`backtesting`, `frontend`, `infra`, `deps`, `config`

### Examples

```
feat(collectors): add CoinGecko collector with retry logic
fix(scoring): correct weight normalization in opportunity_engine
test(collectors): add tests for base_collector retry behaviour
chore(deps): bump ruff to 0.4.4
ci: add bandit security scan to CI pipeline
docs: update README with act local CI instructions
```

---

## Project Roadmap

See [`TODO.md`](TODO.md) for the full phased roadmap.

| Phase | Description | Status |
|---|---|---|
| 1 | Functional MVP — CoinGecko, DB schema, basic scoring, CLI | ✅ Complete |
| 2 | Dev Activity + Social (GitHub, Reddit, X) | ✅ Complete |
| 3 | AI & Narratives (Ollama, Gemini, embeddings) | ✅ Complete |
| 4 | Listing Radar + Risk detection | ✅ Complete |
| 5 | Telegram alerts + Reports (MD/PDF) | ✅ Complete |
| 6 | React Dashboard — fully wired, Docker containers | ✅ Complete |
| 7 | ML + Knowledge Graph + Backtesting | ✅ Complete |
| 8 | Live Data Pipeline + Production Hardening | ✅ Complete |
| 9 | Full Scoring Pipeline — all 11 sub-scores, 5-pillar formula | ✅ Complete |
| 10 | Live Narratives + Cycle Detection | ✅ Complete |
| 11 | Alert Generation — fire alerts from scores, Telegram delivery | ✅ Complete |
| 12 | Backtesting Validation — historical data, precision metrics | ✅ Complete |
| 13 | **Ranking Foundation** — real social data, wire CMC, CLI db mgmt, Gemini whitepapers | 🔲 Planned |
| 14 | **Multi-Cycle Backtesting** — 3 BTC cycles, weight calibration feedback loop | 🔲 Planned |
| 15 | **Ranking Polish** — smart filtering, cycle-aware scoring, score explanations | 🔲 Planned |
| 16 | Narratives & Ecosystems — real social-driven narratives, real graph edges | 🔲 Future |
| 17 | Alerts Tuning — smart thresholds, reduce volume | 🔲 Future |

### Current Status & Known Limitations

Phases 1–12 are complete (1109 backend tests, 144 frontend tests, full Docker
stack, real CoinGecko data). The infrastructure is solid. The main gap is
**ranking quality** — sub-scores rely on heuristic guesses because social and
dev data collectors aren't wired into the scoring pipeline.

**What works:**
- Full Docker stack (`docker compose up` → all services healthy)
- CoinGecko collection: 250 real tokens, scored and persisted
- Cycle detection: BTC dominance, Fear & Greed, market phase classification
- Alert generation: fires alerts from scores, Telegram delivery
- Backtesting infrastructure: validation engine, weight calibrator
- Frontend: 5 pages (Rankings, Token Detail, Narratives, Ecosystems, Backtesting, Alerts)

**Known limitations (addressed by Phases 13–15):**
- **Rankings are unreliable:** Heuristic sub-scores (from `HeuristicSubScorer`)
  produce misleading results. Obscure tokens rank above BTC/ETH because the
  heuristic confuses speculative volume with adoption.
- **Social data not wired:** Twitter and Reddit collectors exist but don't feed
  into the scoring pipeline. `growth_score` and `narrative_score` are guesses.
- **CoinMarketCap not wired:** CMC collector exists but isn't called in the
  pipeline. Tags and categories aren't used for scoring.
- **Backtesting uses limited data:** Only 10 tokens, one cycle (2019-2021).
  Weight calibration results aren't applied to live ranking.
- **Whitepaper PDF is non-functional:** Download button exists but generates
  stub content, not real analysis.
- **Seed data auto-runs:** `entrypoint.sh` seeds fake data on every container
  start, which mixes with real data.

**Current test counts:** 1109 backend + 144 frontend = **1 253 total tests**
