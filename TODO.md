# TODO — Crypto AI Research Terminal

> Phased development plan. Each phase maps to the roadmap in `SCOPE.md` section 10.
> Update this file whenever a task is started or completed.
> Legend: 🔲 Not started · 🔄 In progress · ✅ Done

---

## Development methodology — TDD (mandatory)

Every task below must follow the **Red → Green → Refactor** cycle:

1. **Red** — Write a failing test first. Run it. Confirm it fails for the right reason.
2. **Green** — Write the minimum production code to make the test pass. Nothing more.
3. **Refactor** — Clean up without changing behaviour. Re-run to stay green.
4. Commit. Move to the next behaviour.

**No production code is written before a failing test exists for it.**
Test naming: `test_<unit>_<scenario>_<expected_outcome>`
See `.github/copilot-instructions.md` and `.github/instructions/python-backend.instructions.md` for the full rules.

---

## Phase 1 — Functional MVP (target: ~2 weeks)

**Goal:** System running with real data, functional CLI, basic ranking.

### Setup & Infrastructure
- ✅ Poetry `pyproject.toml` with dev/lint groups
- ✅ Virtual environment (`.venv`) with `python -m venv .venv`
- ✅ Ruff, Mypy (strict), Bandit configuration
- ✅ `pre-commit` hooks (pre-push: ruff, mypy, bandit, pytest)
- ✅ GitHub Actions CI workflow (`.github/workflows/ci.yml`)
- ✅ `act` support for running CI locally
- ✅ Project skeleton: all module directories + stub files
- ✅ `.github/copilot-instructions.md` (repo-wide)
- ✅ `.github/instructions/` (path-specific instructions)
- ✅ `README.md`, `TODO.md`, `CHANGELOG.md`
- ✅ `.env.example`
- 🔲 Docker Compose (`infra/docker-compose.yml`) — PostgreSQL + Redis + Ollama
- 🔲 Alembic initialised (`alembic init`) + `env.py` configured for async

### Database models (SQLAlchemy 2.x async)
- 🔲 `models/token.py` — Token
- 🔲 `models/market_data.py` — MarketData
- 🔲 `models/dev_activity.py` — DevActivity
- 🔲 `models/social_data.py` — SocialData
- 🔲 `models/signal.py` — Signal
- 🔲 `models/score.py` — TokenScore
- 🔲 `models/alert.py` — Alert
- 🔲 Alembic migration for initial schema

### Data Collection
- 🔲 `collectors/coingecko_collector.py` — price, market cap, volume, rank, ATH, supply, links
- 🔲 Tests for CoinGecko collector (mock HTTP)

### Feature Engineering
- 🔲 `processors/market_processor.py` — volume/mcap ratio, velocity, ATH distance
- 🔲 `processors/normalizer.py` — min-max normalization helpers

### Scoring
- 🔲 `scoring/fundamental_scorer.py` — simplified version (no LLM; static weights)
- 🔲 `scoring/opportunity_engine.py` — base composite score

### API & CLI
- 🔲 `api/routes/tokens.py` — GET /tokens, GET /tokens/{symbol}
- 🔲 `api/routes/rankings.py` — GET /rankings/opportunities
- 🔲 `cli.py` — `cryptoai top [--n N]` and `cryptoai report <SYMBOL>`

### Scheduler
- 🔲 `scheduler/jobs.py` — daily collection job

**Deliverable:** `cryptoai top 20` shows ranking with real data.

---

## Phase 2 — Dev Activity + Social (target: ~1–2 weeks)

- 🔲 `collectors/github_collector.py` — commits, contributors, stars, forks, issues
- 🔲 `collectors/social_collector.py` — Reddit posts, subscribers, upvotes
- 🔲 `processors/dev_processor.py` — dev_activity_score, commit growth
- 🔲 `processors/social_processor.py` — mention growth, sentiment_score
- 🔲 `processors/anomaly_detector.py` — statistical anomaly scores
- 🔲 `scoring/growth_scorer.py` — composite growth score
- 🔲 Tests for all new collectors and processors

**Deliverable:** Score includes dev activity and social growth.

---

## Phase 3 — AI & Narratives (target: ~2 weeks)

- 🔲 `ai/llm_provider.py` — Ollama / Gemini / OpenAI abstraction with fallback chain
- 🔲 `ai/whitepaper_analyzer.py` — PDF → structured analysis JSON
- 🔲 `ai/narrative_detector.py` — embeddings + HDBSCAN clustering
- 🔲 `ai/project_classifier.py` — Layer1 / DeFi / AI / etc.
- 🔲 `ai/summary_generator.py` — plain-language token summary
- 🔲 `scoring/narrative_scorer.py`
- 🔲 Tests for AI module (mocked LLM responses)

**Deliverable:** `cryptoai report SOL` generates full analysis with plain-language text.

---

## Phase 4 — Listing Radar + Risk (target: ~1–2 weeks)

- 🔲 `collectors/exchange_monitor.py` — listing diff per exchange
- 🔲 `signals/listing_signals.py` + `ml/listing_predictor.py`
- 🔲 `risk/rugpull_detector.py`
- 🔲 `risk/manipulation_detector.py`
- 🔲 `risk/whale_tracker.py`
- 🔲 `risk/tokenomics_risk.py` — unlock calendar
- 🔲 `scoring/risk_scorer.py` + `scoring/listing_scorer.py`

**Deliverable:** Listing and risk alerts operational.

---

## Phase 5 — Telegram + Reports (target: ~1 week)

- 🔲 `alerts/telegram_bot.py`
- 🔲 `alerts/alert_rules.py` + `alerts/alert_formatter.py`
- 🔲 `reports/markdown_generator.py` + Jinja2 templates
- 🔲 `reports/pdf_generator.py` (WeasyPrint)
- 🔲 `api/routes/alerts.py` + `api/routes/reports.py`

**Deliverable:** Alerts arriving on Telegram. Exportable reports.

---

## Phase 6 — React Dashboard (target: ~2–3 weeks)

- 🔲 `frontend/` setup: React 18 + TypeScript + Vite + shadcn/ui + TailwindCSS
- 🔲 Home page — rankings table with filters
- 🔲 Token Detail page — radar chart + metrics + AI summary
- 🔲 Narratives page — narrative cards + momentum charts
- 🔲 Alerts page — feed + configuration
- 🔲 Connect all pages to FastAPI

**Deliverable:** Local visual dashboard.

---

## Phase 7 — ML + Graph + Backtesting (target: ~3–4 weeks)

- 🔲 `ml/feature_builder.py` + `ml/cycle_leader_model.py` (XGBoost)
- 🔲 `ml/model_trainer.py` — training pipeline with historical data
- 🔲 `graph/graph_builder.py` + `graph/community_detector.py` (Louvain)
- 🔲 `graph/centrality_analyzer.py` (PageRank, betweenness)
- 🔲 `graph/ecosystem_tracker.py`
- 🔲 `backtesting/` — full backtesting engine
- 🔲 Ecosystem Graph visual in frontend (D3.js / React Flow)
- 🔲 Backtesting page in frontend
- 🔲 `scripts/seed_historical_data.py`

**Deliverable:** "Next Solana" score. Validated backtesting. Visual Knowledge Graph.
