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

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Docker + Docker Compose
- (Optional) [act](https://github.com/nektos/act) — to run the CI pipeline locally

### 1 — Clone and create virtual environment

```bash
git clone https://github.com/pattersonrptr/crypto-ai-research-terminal.git
cd crypto-ai-research-terminal

python -m venv .venv
source .venv/bin/activate
```

### 2 — Install dependencies

```bash
pip install poetry          # if not already installed globally
poetry install --with dev
```

### 3 — Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 4 — Install pre-commit hooks

```bash
pre-commit install --hook-type pre-push
```

### 5 — Start services with Docker Compose

```bash
docker compose -f infra/docker-compose.yml up -d postgres redis ollama
```

### 6 — Run database migrations

```bash
source .venv/bin/activate
cd backend && alembic upgrade head
```

### 7 — Start the backend

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload
# API docs: http://localhost:8000/docs
```

---

## Running locally

```bash
source .venv/bin/activate

# Full analysis scan
cryptoai scan

# Top 20 opportunities
cryptoai top --n 20

# Detailed report for a token
cryptoai report SOL

# Run backtesting
cryptoai backtest --start 2019-01-01 --end 2021-01-01
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

**Always run this before pushing** to catch errors before they reach the remote CI pipeline.

### Option 1 — `ci-local.sh` script (recommended)

```bash
./scripts/ci-local.sh
```

This runs the exact same checks as the GitHub Actions pipeline, in order:

| Step | Tool | What it checks |
|---|---|---|
| 1 | `ruff check` | Lint rules (unused imports, style, security patterns) |
| 2 | `ruff format --check` | Code formatting |
| 3 | `mypy` | Static type checking (strict mode) |
| 4 | `bandit` | Security vulnerabilities |
| 5 | `pytest` | Tests + coverage (≥ 50% required) |

> **Note:** Activate the virtual environment first if not already active:
> `source .venv/bin/activate`

### Option 2 — run checks individually

```bash
source .venv/bin/activate

# Lint (with auto-fix)
ruff check backend/ --fix

# Format (with auto-fix)
ruff format backend/

# Type check
mypy backend/app

# Security scan
bandit -c pyproject.toml -r backend/app -q

# Tests with coverage
pytest backend/tests/ --tb=short -q
```

### Option 3 — `act` (full GitHub Actions simulation)

[act](https://github.com/nektos/act) runs the complete `.github/workflows/ci.yml`
pipeline locally inside Docker — identical to what runs on GitHub.

```bash
# Install act (Arch Linux)
yay -S act

# Ubuntu / Debian
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run the full CI pipeline
act push

# Run only the quality job
act push -j quality
```

> **Note:** act requires Docker. On the first run it downloads the `ubuntu-22.04`
> runner image (~1.5 GB).

### Common Ruff errors and how to fix them

| Code | Description | Fix |
|---|---|---|
| `F401` | Unused import | Remove the import |
| `B008` | `Query()` in function default | Use `Annotated[T, Query()]` as type hint |
| `E501` | Line too long (> 100 chars) | Break the line |
| `UP017` | Use `datetime.UTC` instead of `timezone.utc` | Replace `timezone.utc` → `UTC` |
| `I001` | Unsorted imports | Run `ruff check --fix` |

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
| 6 | React Dashboard | 🔲 Not started |
| 7 | ML + Knowledge Graph + Backtesting | 🔲 Not started |

**Current status:** 499 tests passing, 93% coverage
