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
- ✅ Docker Compose (`infra/docker-compose.yml`) — PostgreSQL + Redis + Ollama
- ✅ Alembic initialised (`alembic init`) + `env.py` configured for async

### Database models (SQLAlchemy 2.x async)
- ✅ `models/token.py` — Token
- ✅ `models/market_data.py` — MarketData
- ✅ `models/dev_activity.py` — DevActivity
- ✅ `models/social_data.py` — SocialData
- ✅ `models/signal.py` — Signal
- ✅ `models/score.py` — TokenScore
- ✅ `models/alert.py` — Alert
- ✅ Alembic migration for initial schema

### Data Collection
- ✅ `collectors/coingecko_collector.py` — price, market cap, volume, rank, ATH, supply, links
- ✅ Tests for CoinGecko collector (mock HTTP)

### Feature Engineering
- ✅ `processors/market_processor.py` — volume/mcap ratio, velocity, ATH distance
- ✅ `processors/normalizer.py` — min-max normalization helpers

### Scoring
- ✅ `scoring/fundamental_scorer.py` — simplified version (no LLM; static weights)
- ✅ `scoring/opportunity_engine.py` — base composite score

### API & CLI
- ✅ `api/routes/tokens.py` — GET /tokens, GET /tokens/{symbol}
- ✅ `api/routes/rankings.py` — GET /rankings/opportunities
- ✅ `cli.py` — `cryptoai top [--n N]` and `cryptoai report <SYMBOL>`

### Scheduler
- ✅ `scheduler/jobs.py` — daily collection job

**Deliverable:** `cryptoai top 20` shows ranking with real data.

---

## Phase 2 — Dev Activity + Social (target: ~1–2 weeks) ✅ COMPLETE

- ✅ `collectors/github_collector.py` — commits, contributors, stars, forks, issues
- ✅ `collectors/social_collector.py` — Reddit posts, subscribers, upvotes
- ✅ `processors/dev_processor.py` — dev_activity_score, commit growth
- ✅ `processors/social_processor.py` — mention growth, sentiment_score
- ✅ `processors/anomaly_detector.py` — statistical anomaly scores
- ✅ `scoring/growth_scorer.py` — composite growth score
- ✅ `scoring/opportunity_engine.py` — updated with growth_score integration
- ✅ Tests for all new collectors and processors (74 new tests, 169 total)

**Deliverable:** Score includes dev activity and social growth.

---

## Phase 3 — AI & Narratives (target: ~2 weeks) ✅ COMPLETE

- ✅ `ai/llm_provider.py` — Ollama / Gemini / OpenAI abstraction with fallback chain
- ✅ `ai/whitepaper_analyzer.py` — PDF → structured analysis JSON
- ✅ `ai/narrative_detector.py` — embeddings + HDBSCAN clustering
- ✅ `ai/project_classifier.py` — Layer1 / DeFi / AI / etc.
- ✅ `ai/summary_generator.py` — plain-language token summary
- ✅ `scoring/narrative_scorer.py`
- ✅ Tests for AI module (mocked LLM responses; 74 new tests, 243 total)

**Deliverable:** `cryptoai report SOL` generates full analysis with plain-language text.

---

## Phase 4 — Listing Radar + Risk (target: ~1–2 weeks) ✅ COMPLETE

### Risk Detection
- ✅ `risk/rugpull_detector.py` — anonymous team, wallet concentration >30%, low liquidity, no audit, no GitHub
- ✅ `risk/manipulation_detector.py` — pump & dump, wash trading, coordinated social
- ✅ `risk/whale_tracker.py` — top 10/50 wallet concentration, accumulation/distribution
- ✅ `risk/tokenomics_risk.py` — unlock calendar, inflation rate, >5% unlock in 30 days = alert

### Scoring
- ✅ `scoring/risk_scorer.py` — composite risk score (0.30×rugpull + 0.25×manipulation + 0.25×tokenomics + 0.20×whale)
- ✅ `scoring/listing_scorer.py` — combines signals, predictions, exchange breadth

### Listing Radar
- ✅ `collectors/exchange_monitor.py` — listing diff per exchange, snapshot, change detection
- ✅ `signals/listing_signals.py` — generates signals from listing changes, exchange tier strength
- ✅ `ml/listing_predictor.py` — ML-based listing probability (heuristic model for Phase 4)

### Tests (TDD)
- ✅ 121 new tests across risk, scoring, collectors, signals, ml modules
- ✅ **Total: 364 tests — all passing (was 243 in Phase 3)**
- ✅ **Test coverage: 93%**

**Deliverable:** Listing and risk alerts operational.

---

## Phase 5 — Telegram + Reports (target: ~1 week) ✅ COMPLETE

### Alerts System
- ✅ `alerts/alert_formatter.py` — AlertType enum (8 types), FormattedAlert dataclass, AlertFormatter
- ✅ `alerts/alert_rules.py` — AlertRule ABC, 7 concrete rules, AlertRuleEngine
- ✅ `alerts/telegram_bot.py` — async Telegram bot with httpx, rate limiting

### Reports System
- ✅ `reports/markdown_generator.py` — Jinja2-based Markdown generation
- ✅ `reports/pdf_generator.py` — WeasyPrint-based PDF generation
- ✅ `reports/templates/token_report.md.j2` — Token analysis template
- ✅ `reports/templates/market_report.md.j2` — Market report template

### API Endpoints
- ✅ `api/routes/alerts.py` — GET/POST/PUT endpoints for alerts management
- ✅ `api/routes/reports.py` — GET endpoints for report generation (markdown/pdf)

### Tests (TDD)
- ✅ 135 new tests across alerts, reports, API modules
- ✅ **Total: 499 tests — all passing (was 364 in Phase 4)**
- ✅ **Test coverage: 93%**

**Deliverable:** Alerts arriving on Telegram. Exportable reports.

---

## Phase 6 — React Dashboard (target: ~2–3 weeks) ✅ COMPLETE

### Scaffold (PR #7 — merged ✅)
- ✅ `frontend/` setup: React 18 + TypeScript + Vite + TailwindCSS (dark default, light/system toggle)
- ✅ Architecture: Feature-Sliced Design — `features/`, `pages/`, `services/`, `store/`
- ✅ Zustand stores: themeStore (dark/light/system + OS sync), sidebarStore (retractable), tableStore (13 configurable columns)
- ✅ Axios service layer: `tokens.service.ts`, `alerts.service.ts`, `reports.service.ts`
- ✅ Layout: AppShell, retractable Sidebar, TopBar with theme toggle, PageHeader
- ✅ `TokenCard` component — TDD: 10/10 tests passing
- ✅ `Home` page — 10 cards/page, pagination, skeleton loader
- ✅ `TokenDetail` page — Recharts radar chart, score bars, market metrics, MD+PDF download
- ✅ Stub pages: Alerts, Narratives

### TDD + wiring (current session) ✅
- ✅ MSW (Mock Service Worker) setup — `src/test/msw/handlers.ts` + server config
- ✅ `Home` page tests — 10/10 (loading, error, pagination with MSW mocks)
- ✅ `TokenDetail` page tests — 13/13 (radar, scores, download buttons with MSW mocks)
- ✅ `Sidebar` tests — 10/10 (nav links, toggle open/close, persists state via localStorage polyfill)
- ✅ `TopBar` tests — 10/10 (theme buttons change `<html>` class, matchMedia polyfill)
- ✅ `ColumnPicker` component + tests — 11/11 (toggle columns, reset, click-outside close)
- ✅ `Alerts` page — full feed, acknowledge button, stats bar, filter, wired to `GET /alerts` — 10/10 tests
- ✅ `Narratives` page — narrative cards with trend/momentum/tokens/keywords, wired to `GET /narratives` — 10/10 tests
- ✅ `narratives.service.ts` — `fetchNarratives()` — 5/5 tests
- ✅ Backend `GET /narratives` — 10 seed narratives, 10/10 tests
- ✅ `vitest run --coverage` → 96.9% statements, all modules ≥80% (94 tests total)

### Docker + infra ✅
- ✅ `infra/Dockerfile.frontend` — multi-stage: Node 22 builder + nginx 1.27 runner
- ✅ `infra/nginx/nginx.conf` — SPA fallback + `/api` proxy to backend container
- ✅ `infra/docker-compose.yml` — added `frontend` service; fixed backend healthcheck
  (`python urllib` instead of `wget`); fixed backend `CMD` (`app.main:app`); removed
  `profiles: [full]` so backend starts by default
- ✅ `infra/docker-compose.yml` — added `db-seed` service: runs `seed_data.py` once on
  every `docker compose up`, idempotent (skips if data already exists), `restart: "no"`
- ✅ `frontend/package.json` — added `build:docker` script (Vite only, no `tsc -b`)
- ✅ Fixed trailing-slash redirect bug: all `apiClient` paths now include trailing `/`
  so FastAPI's 307 redirect is never triggered through the nginx proxy
- ✅ Verified: `docker compose up -d` → all services healthy, tokens/rankings/narratives
  render in browser, alerts page shows empty state (no data yet — expected)

**Deliverable:** Full stack running in containers — `docker compose up` is all that is needed.

---

## Phase 7 — ML + Graph + Backtesting (target: ~3–4 weeks)

### Machine Learning
- ✅ `ml/feature_builder.py` — feature matrix from historical prices, dev activity, social, scores
- ✅ `ml/cycle_leader_model.py` — XGBoost model to predict "next Solana" cycle leaders
- ✅ `ml/model_trainer.py` — training pipeline: train, validate, serialise model
- ✅ Tests for all ML modules (TDD)

### Graph Intelligence
- ✅ `graph/graph_builder.py` — builds token relationship graph (narratives, ecosystems, correlations)
- ✅ `graph/community_detector.py` — Louvain algorithm for related-project clusters
- ✅ `graph/centrality_analyzer.py` — PageRank + betweenness to find most influential tokens
- ✅ `graph/ecosystem_tracker.py` — tracks ecosystem evolution over time
- ✅ Tests for all graph modules (TDD)

### Backtesting Engine
- ✅ `backtesting/data_loader.py` — loads historical data (2017, 2020–2021 cycles)
- ✅ `backtesting/simulation_engine.py` — simulates model on past cycles
- ✅ `backtesting/performance_metrics.py` — precision, recall, simulated ROI
- ✅ `scripts/seed_historical_data.py` — populate DB with historical data for backtesting
- ✅ Tests for backtesting engine (TDD)

### Frontend — New Pages
- ✅ `frontend/src/pages/Ecosystems.tsx` — ecosystem knowledge graph (community cards + top tokens by PageRank)
- ✅ `frontend/src/pages/Backtesting.tsx` — backtesting results and model validation metrics
- ✅ Wire new backend endpoints to the frontend + MSW tests

### Backend — API Routes (Phase 7 endpoints)
- ✅ `api/routes/graph.py` — GET /graph/communities, GET /graph/centrality, GET /graph/ecosystem
- ✅ `api/routes/backtesting.py` — POST /backtesting/run (replaces placeholder stub)

**Deliverable:** "Next Solana" score. Validated backtesting. Visual Knowledge Graph. ✅ COMPLETE

---

## Phase 8 — Live Data + Production Hardening (target: ~2–3 weeks)

> Goal: Replace all seed/stub data with live pipeline data. Activate real-time
> social signals. Harden the system for long-running production use.

### Live Data Collectors
- ✅ `collectors/coinmarketcap_collector.py` — CMC rank, tags, categories (key: `COINMARKETCAP_API_KEY`)
- ✅ `collectors/defillama_collector.py` — TVL, TVL evolution 30d/90d, chains, DEX volume, revenue
- ✅ `collectors/social_collector.py` — extend with Twitter/X real-time mentions + sentiment
  (key: `TWITTER_BEARER_TOKEN` — Basic plan required ~$100/month)
- ✅ Wire live `NarrativeDetector` pipeline to replace seed data in `GET /narratives`
  → done in Phase 11 (narrative snapshot wired into daily pipeline)
- ✅ Wire live `AlertRuleEngine` to scheduler so alerts fire automatically
  → done in Phase 11 (AlertEvaluator wired into daily pipeline)

### Scheduler Hardening
- ✅ Wire `scheduler/jobs.py` full pipeline: collect → process → score → persist → alert
- ✅ Add job health monitoring + dead-letter queue for failed jobs (Redis)
- ✅ Add `/scheduler/status` API endpoint (last run, next run, errors)

### Pipeline Persistence
- ✅ `_persist_results()` — real DB writes: Token + TokenScore + MarketData
- ✅ Duplicate-symbol handling (CoinGecko returns tokens with same symbol)
- ✅ Collector used as async context manager

### CLI
- ✅ `collect-now` command for manual pipeline trigger
- ✅ Entry point fixed: `cryptoai = "app.cli:cli"`

### Frontend — Live Data Pages
- ✅ Dashboard refresh interval (polling 30s) for real-time score updates
- ✅ `Narratives` page — live data from `NarrativePersister` pipeline (Phase 11)
- ✅ `Alerts` page — real alerts from the rule engine (Phase 11)

### Production Infrastructure
- ✅ `infra/docker-compose.prod.yml` — production overrides (no bind mounts, resource limits)
- ✅ Nginx rate limiting + CORS hardening
- ✅ Log rotation + structured log export — `logging_config.py` (JSON/console modes),
  Docker log rotation (json-file driver, 50 MB × 5 files) in `docker-compose.prod.yml`
- ✅ `.env.example` updated with all new keys

**Status:** Pipeline works end-to-end (249 real tokens from CoinGecko). But only
`fundamental_score` and `opportunity_score` are populated — all other sub-scores
are 0.0. The remaining Phase 8 items (live narratives, alerts) depend on the full
scoring pipeline and are moved to Phases 10–11.

**Deliverable:** `collect-now` collects real data. API serves real scores.
Remaining scoring and prediction features addressed in Phases 9–12.

---

## Phase 9 — Full Scoring Pipeline ✅ COMPLETE

> Goal: All 11 sub-scores populated with real data. Full 5-pillar opportunity
> formula from SCOPE.md Section 9. Rankings are actionable. Radar chart works.
> Token Detail page becomes useful for decision-making.

### Problem statement
The `FundamentalScorer` uses only 4 market metrics (`volume_mcap_ratio`,
`price_velocity`, `ath_distance_pct`, `market_cap_usd`). The `OpportunityEngine`
runs in Phase 1 fallback mode (returns `fundamental_score` directly). All other
scorer classes (`GrowthScorer`, `RiskScorer`, `NarrativeScorer`, `ListingScorer`)
exist but are never called by the pipeline. 9 of 11 sub-scores in `token_scores`
are 0.0. The radar chart, rankings, and token detail page are useless.

### HeuristicSubScorer (replaces individual scorer wiring)
- ✅ `HeuristicSubScorer` derives all 9 sub-scores from CoinGecko market data using
  heuristics (rank, market cap, volume ratio, price velocity, ATH distance)
- ✅ `TokenScore` model: 9 new Float columns — `technology_score`, `tokenomics_score`,
  `adoption_score`, `dev_activity_score`, `narrative_score`, `growth_score`,
  `risk_score`, `listing_probability`, `cycle_leader_prob`
- ✅ Alembic migration `b2c3d4e5f6a7`: adds 9 sub-score columns to `token_scores`

### Upgrade OpportunityEngine
- ✅ `OpportunityEngine.full_composite_score()`: 5-pillar weighted formula
  `0.30×fundamental + 0.25×growth + 0.20×narrative + 0.15×listing + 0.10×risk`
  with up to 10% cycle-leader boost, clamped to [0, 1]
- ✅ Pipeline wiring: `collect → process → fundamental → heuristic sub-scores →
  full composite → persist all 11 scores`

### Fix Token Detail API
- ✅ Token Detail API: JOIN `MarketData`, returns all 11 sub-scores + market metrics
  (price, market_cap, volume, rank)
- ✅ Rankings API: JOIN `MarketData`, richer signals for growth/risk/narrative/listing
- ✅ Latest-only queries: Rankings and Tokens endpoints use `MAX(id)` subqueries to
  return only the most recent `TokenScore` and `MarketData` per token
- ✅ Frontend scaling: API returns 0–1 scores; display layer multiplies by 10 for
  0–10 user-facing values (TokenDetail radar chart, TokenCard score bars)

### Production fixes
- ✅ CLI `collect-now` pipeline fix: Uses `HeuristicSubScorer` +
  `OpportunityEngine.full_composite_score()`
- ✅ Docker dev volume mount: `docker-compose.yml` mounts `../backend:/app/backend:ro`
- ✅ `.dockerignore`: Excludes `.venv/`, `node_modules/`, `.git/`, `__pycache__/`
- ✅ `Dockerfile.backend`: `PIP_DEFAULT_TIMEOUT=300`, `POETRY_INSTALLER_MAX_WORKERS=4`
- ✅ `entrypoint.sh`: Runs `seed_data.py` after Alembic migration (auto-seeds, backfills)
- ✅ Seed data: All 11 sub-scores in `SAMPLE_SCORES`, `_backfill_sub_scores()` function

### Remaining (optional enhancements — ✅ all completed)
- ✅ Upgrade `FundamentalScorer` from 4-metric → 5-sub-pillar model
  (`sub_pillar_score()` — technology, tokenomics, adoption, dev_activity, narrative)
- ✅ Wire `GrowthScorer` into pipeline via `PipelineScorer` (data-availability check)
- ✅ Wire `RiskScorer` into pipeline via `PipelineScorer` (data-availability check)
- ✅ Wire `NarrativeScorer` into pipeline via `PipelineScorer` (category-based, no LLM)
- ✅ Wire `ListingScorer` into pipeline via `PipelineScorer` (data-availability check)
- ✅ Wire `CycleLeaderModel.predict()` → `cycle_leader_prob` via `PipelineScorer`
- ✅ AI-generated token summary → `AiAnalysis` model + `SummaryCacheService` +
  `GET /tokens/{symbol}/summary` endpoint with DB cache

### Tests (TDD) — 34 new tests, 836 total
- ✅ Tests for `HeuristicSubScorer` (all 9 sub-scores, edge cases)
- ✅ Tests for `OpportunityEngine.full_composite_score()` (5-pillar formula)
- ✅ Tests for pipeline integration (all scorers wired correctly)
- ✅ Tests for Token Detail API with market data + all sub-scores
- ✅ Frontend tests for populated radar chart + market metrics

**Deliverable:** Rankings show multi-dimensional scores. Radar chart is filled.
Token Detail page is actionable. 836 backend tests (93% coverage), 126 frontend tests.

---

## Phase 10 — Live Narratives + Cycle Detection ✅ COMPLETE

> Goal: Narratives page shows real detected clusters from social data.
> App knows the current market cycle. Ecosystems derived from real data.
> The system can identify what's gaining momentum NOW.

### Problem statement
Narratives page shows hardcoded `_SEED_NARRATIVES` (10 fake items). Ecosystems
page uses a hardcoded 15-node graph. The app has no cycle awareness — it doesn't
know we're in a bear market in 2026. Without cycle context, no prediction is
possible.

### Live narrative detection
- ✅ `NarrativePersister.to_clusters()` — converts `NarrativeDetectorResult` to ORM objects
- ✅ `NarrativePersister.build_from_categories()` — fallback that derives narratives
  from CoinGecko token category metadata when social data is unavailable
- ✅ Persist detected narrative clusters to `narratives` table (Alembic migration)
- ✅ `NarrativeTrendAnalyzer.compare()` — compares current vs previous snapshot → trend
  (`accelerating`, `growing`, `stable`, `declining`)
- ✅ Scheduler jobs: `persist_narrative_snapshot()` + `build_narrative_snapshot_from_categories()`
- ✅ Remove `_SEED_NARRATIVES` fallback from `GET /narratives` — done in Phase 11

### Cycle detection
- ✅ `app/analysis/cycle_detector.py` — `CycleDetector.classify()` with weighted-vote:
  - BTC dominance trend (rising = risk-off, falling = altseason) — weight 1.5
  - Total crypto market cap trend vs 200-day moving average — weight 2
  - Fear & Greed index integration (Alternative.me API, free) — weight 3
  - Market phase classification: `accumulation`, `bull`, `distribution`, `bear`
- ✅ `app/analysis/cycle_data_collector.py` — fetches F&G + BTC dominance from APIs
- ✅ `GET /market/cycle` API endpoint with current phase + confidence + description
- ✅ `OpportunityEngine.cycle_adjusted_score()` — factors cycle phase into scoring
  (bull=1.10, accumulation=1.0, distribution=0.90, bear=0.75)
- ✅ Frontend `CycleIndicator` component in dashboard header with phase badge, emoji,
  confidence %, description

### Real ecosystem graph
- ✅ `LiveGraphBuilder.build()` — builds graph from real token relationships:
  - Shared narrative clusters (tokens in same narrative = edge, weight 0.6)
  - Shared blockchain ecosystem (same chain = edge, weight 0.7)
- ✅ Graph routes prefer live data, fall back to seed graph when DB is empty
- ✅ Price correlation matrix (corr > 0.7 = edge) — `PriceCorrelationBuilder`
  with Pearson correlation, configurable threshold, absolute value mode
- ✅ Detect growing ecosystems — `EcosystemTracker.growth_summary()` compares
  community sizes over time, reports trend (growing/shrinking/stable)

### Tests (TDD) — 88 new tests, 924 backend + 133 frontend total
- ✅ `CycleDetector` (24 tests — phase classification, all edge cases)
- ✅ `CycleDataCollector` (7 tests — API calls, error handling, defaults)
- ✅ `NarrativeCluster` ORM model (4 tests)
- ✅ `NarrativePersister` (8 tests — both modes, edge cases)
- ✅ `NarrativeTrendAnalyzer` (10 tests — all trend types, new/stable/accelerating)
- ✅ `OpportunityEngine.cycle_adjusted_score` (7 tests — all phases, clamping)
- ✅ Market cycle API endpoint (5 tests)
- ✅ `LiveGraphBuilder` (13 tests — token nodes, edges, ecosystem/narrative links)
- ✅ Graph route live data path (4 tests — live, fallback, communities/centrality/ecosystem)
- ✅ Scheduler integration (6 tests — persist + build from categories)
- ✅ Frontend `market.service.ts` (4 tests — happy path, error handling)
- ✅ Frontend `CycleIndicator` (3 tests — renders phase, confidence, description)

**Deliverable:** Dashboard shows current market cycle phase. LiveGraphBuilder
provides real token relationships. NarrativePersister + TrendAnalyzer ready for
pipeline integration. 924 backend tests (92.9% coverage), 133 frontend tests.

---

## Phase 11 — Alert Generation ✅ COMPLETE

> Goal: Alerts page shows real fired alerts. Telegram notifications working.
> The system proactively warns about opportunities and risks.

### Problem statement
`AlertRuleEngine` and 7 concrete alert rules exist in code but are never called.
The scheduler pipeline ends at `_persist_results`. No alerts are ever generated.
The Alerts page is always empty. Narratives route still uses `_SEED_NARRATIVES`
hardcoded fallback.

### Wire alert generation into pipeline
- ✅ `AlertEvaluator` service bridges scored pipeline data → `AlertRuleEngine` →
  `Alert` ORM objects with key/scale mapping (`listing_probability` 0–1 → 0–100, etc.)
- ✅ `evaluate_and_persist_alerts()` in `scheduler/jobs.py` — called after scoring
- ✅ Persist fired alerts to `alerts` table with full JSONB metadata
- ✅ Send high-urgency alerts to Telegram via `TelegramBot` (optional, env-based)

### Alert model upgrade
- ✅ Alert model: new columns — `alert_metadata` (JSONB, mapped from `metadata` DB col),
  `sent_telegram`, `acknowledged`, `acknowledged_at`, `token_symbol`; `token_id` nullable
- ✅ Alembic migration `d4e5f6a7b8c9`: ALTER + ADD columns + index on `alert_type`

### Alerts API rewrite
- ✅ Replaced in-memory `_alerts_store` with DB-backed async routes
- ✅ Response schema: `AlertResponse` (maps `alert_metadata` → `metadata`,
  `triggered_at` → `created_at` for frontend compatibility)
- ✅ Endpoints: `GET /` (list with limit/type/acknowledged filters),
  `GET /stats`, `GET /{alert_id}`, `POST /test`, `PUT /{alert_id}/acknowledge`

### Wire narratives into pipeline
- ✅ Added narrative build+persist step to `daily_collection_job`
- ✅ Removed `_SEED_NARRATIVES` hardcoded fallback from `GET /narratives`
  (endpoint returns empty list when DB has no data)

### Daily digest
- ✅ `scheduler/digest.py` — `build_digest()` summarises alerts into DAILY_REPORT
- ✅ `send_daily_digest()` — formats via `AlertFormatter` + sends via `TelegramBot`

### Tests (TDD) — 34 new tests, 958 backend total
- ✅ Alert model tests (5 tests — columns, defaults, nullable token_id)
- ✅ AlertEvaluator tests (8 tests — thresholds, metadata, batch, token_id)
- ✅ Alerts API tests (12 tests — list/filter/shape, get by id, test alert, acknowledge, stats)
- ✅ Pipeline alert integration tests (2 tests — evaluator called, failure isolation)
- ✅ Pipeline narrative integration tests (2 tests — snapshot called, failure isolation)
- ✅ Daily digest tests (5 tests — build, empty, metadata, telegram, skip)
- ✅ Narrative route tests updated (12 tests — live data mock, empty list on no DB data)

**Deliverable:** Alerts fire automatically from real data. Telegram receives
notifications. User sees actionable alerts in the dashboard. Narratives served
from live DB data. 958 backend tests (93.5% coverage), 133 frontend tests.

---

## Phase 12 — Backtesting Validation (target: ~2–3 weeks) ✅ COMPLETE

> Goal: Validate the scoring model against real historical cycles.
> Prove (or disprove) that the system can predict winners.

### Problem statement
Backtesting runs on synthetic sinusoidal data from `seed_historical_data.py`.
There's no way to know if the scoring model would have predicted the tokens
that actually did 10x+ in past bull runs. Without validation, the model is
just noise.

### Historical data collection
- ✅ Collect real historical data from CoinGecko `/coins/{id}/market_chart/range`
  for 2019-01 to 2021-12 (pre-bull → peak → post-peak)
- ✅ `backtesting/historical_data_collector.py` — parses CoinGecko responses to snapshots
- ✅ `models/historical_snapshot.py` — SQLAlchemy ORM model for full token state per date
- ✅ Alembic migration `3587d61f0e41` — creates `historical_snapshots` table

### Historical scoring pipeline
- ✅ `backtesting/historical_scorer.py` — scores snapshots, produces ranked `ScoredToken` lists
- ✅ Runs simplified scoring pipeline on historical snapshots
  ("What would the model have scored in January 2020?")
- ✅ Generates ranked list per snapshot date

### Validation metrics
- ✅ `backtesting/validation_metrics.py` — `ValidationEngine` with Precision@K, Recall@K, HitRate
- ✅ `Precision@10`: of the top K recommended, how many did 5x+?
- ✅ `Recall@K`: of the actual performers, how many were in our top K?
- ✅ `Hit rate`: % of recommended tokens that outperformed the threshold
- ✅ Display metrics in backtesting UI with per-token breakdown

### Weight calibration
- ✅ `backtesting/weight_calibrator.py` — parameter sweep over pillar weights to maximise Precision@K
- ✅ Grid search with configurable step size (default 0.1)
- ✅ Documents best weight set and precision achieved

### API endpoints
- ✅ `POST /backtesting/validation/run` — run validation on sample data
- ✅ `POST /backtesting/validation/calibrate` — run weight calibration sweep

### Frontend
- ✅ `backtesting.service.ts` — `runValidation()`, `runCalibration()` with typed interfaces
- ✅ `Backtesting.tsx` — Model Validation section with Run Validation button, metrics panel, token breakdown table
- ✅ MSW handlers for validation/calibration endpoints
- ✅ 12 page tests, 12 service tests — all passing

### Tests (TDD)
- ✅ `test_historical_data_collector.py` — 11 tests
- ✅ `test_historical_scorer.py` — 12 tests
- ✅ `test_validation_metrics.py` — 31 tests
- ✅ `test_weight_calibrator.py` — 14 tests
- ✅ `test_historical_snapshot.py` — 7 tests (model)
- ✅ `test_backtesting_validation.py` — 14 tests (API routes)
- ✅ **89 new backend tests** (1039 total, 93% coverage); **144 frontend tests** (11 new)

**Deliverable:** "If we had run this model in January 2020, it would have
recommended SOL, AVAX, MATIC... with 60% precision@10." Model is calibrated
and trustworthy (or known limitations are documented). ✅ COMPLETE
