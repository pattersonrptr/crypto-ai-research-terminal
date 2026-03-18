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

---

## Phase 13 — Ranking Foundation: Data Quality & Feedback Loop (target: ~2–3 weeks)

> Goal: Fix the root cause of bad rankings. Replace heuristic guesses with
> real data signals (social, dev, CMC). Wire existing collectors into the
> pipeline. Make seed data optional. Add database management CLI. Add
> whitepaper analysis via Gemini.

### Problem statement
Rankings are unreliable because 9 of 11 sub-scores come from
`HeuristicSubScorer` — a set of guesses based on market cap and rank.
KOGE scores 8.8 Adoption and ranks above BTC because the heuristic
confuses high volume/mcap ratio with real adoption. Without social data,
dev activity data, and CMC categories, the scorer has no signal to
differentiate quality projects from noise.

Additionally, the database seeds fake data on every container start,
mixing synthetic data with real data. The user has no CLI tools to
manage the database, and no way to trigger collection from the GUI.

### Remove automatic seed + CLI database management
- ✅ Add `AUTO_SEED=false` to `.env` / `.env.example`. `entrypoint.sh`
  checks this flag before running `seed_data.py`.
- ✅ CLI command: `cryptoai seed [rankings|narratives|all]` — runs
  seed scripts selectively inside the container.
- ✅ CLI command: `cryptoai db-clean [--confirm]` — truncates all data
  tables (tokens, token_scores, market_data, narratives, alerts,
  social_data, dev_activity, signals, ai_analyses). Requires `--confirm`.
- ✅ CLI command: `cryptoai db-truncate <table> [--confirm]` — truncates
  a specific table. Validates table name against allowed list.
- ✅ CLI command: `cryptoai db-status` — shows row counts per table.
- ✅ Tests for all new CLI commands (TDD). — 22 tests

### Twitter/X data collection (free — no API key)
- ✅ Add `twikit` dependency to `pyproject.toml`. twikit is a free
  async Twitter scraper (4.1k stars, MIT license) that requires only
  a regular X account (email + password), no paid API.
- ✅ `collectors/twitter_twikit_collector.py` — `TwitterTwikitCollector` using twikit:
  - Login with X credentials from `.env` (`TWITTER_USERNAME`,
    `TWITTER_EMAIL`, `TWITTER_PASSWORD`). Persist cookies to avoid
    repeated logins.
  - `collect_mentions(symbol)` — searches for `$SYMBOL` or token name
    in recent tweets. Returns mention count, engagement (likes,
    retweets), and raw text for sentiment analysis.
  - Rate-limit aware: respects twikit's internal rate limiting +
    configurable delay between searches.
- ✅ `processors/sentiment_analyzer.py` — simple keyword-based sentiment
  scoring (positive/negative/neutral). Phase 15+ can upgrade to LLM.
- ✅ Persist Twitter data to `social_data` table (twitter_mentions_24h,
  twitter_sentiment columns already exist in the schema).
  → Done in Ranking Quality Loop Item 2 (PR #25).
- ✅ Tests for TwitterTwikitCollector (mocked twikit client, TDD). — 14 tests
- ✅ Tests for SentimentAnalyzer (TDD). — 11 tests

### Wire Reddit collector into pipeline
- ✅ `SocialCollector` (Reddit, already implemented) called in
  `daily_collection_job` after CoinGecko collection.
- ✅ Map token symbols to subreddit names (e.g., BTC → r/Bitcoin,
  ETH → r/ethereum). Configurable mapping in `collectors/subreddit_map.py`.
- ✅ Persist Reddit data to `social_data` table (reddit_posts_7d,
  reddit_subscribers, reddit_growth_pct).
  → Done in Ranking Quality Loop Item 2 (PR #25).
- ✅ Tests for Reddit pipeline integration (TDD). — 4 subreddit_map + 3 collect_social_data tests

### Wire CoinMarketCap collector into pipeline
- ✅ `CoinMarketCapCollector` (already implemented, Phase 8) called in
  `daily_collection_job`. Enriches token data with CMC rank, tags,
  and categories.
- ✅ Merge CMC data into the scored pipeline dict so `PipelineScorer`
  has access to categories, tags, and CMC-specific metrics.
- ✅ Tests for CMC pipeline integration (TDD). — 3 collect_cmc_data tests

### Replace heuristics with real data in scorer
- ✅ When `social_data` is present: `PipelineScorer._score_adoption()` uses
  real social metrics (reddit_subscribers, reddit_posts_24h, sentiment_score)
  instead of heuristics.
- ✅ When `dev_activity` is present: `PipelineScorer._score_dev_activity()` uses
  real dev metrics (commits_30d, contributors, stars, forks) instead of
  mcap-based guess.
- ✅ When CMC categories are present: `PipelineScorer._score_technology()` uses
  real CMC data (rank, tags, category) instead of volume-based guess.
- ✅ Fallback: `HeuristicSubScorer` remains for any token missing data.
- ✅ Tests verifying scorer selection logic (TDD). — 9 tests

### Whitepaper analysis via Gemini (free tier)
- ✅ `ai/whitepaper_analyzer.py` already wired to Gemini API via
  `LLMProvider` (supports ollama → gemini → openai fallback chain).
- 🔲 Token Detail "Download PDF" button generates a real PDF with:
  - Plain-language fundamental analysis (generated by Gemini)
  - Score breakdown with explanations
  - Risk assessment
  - Market metrics snapshot
  → Deferred to Future Phase: Gemini-Powered Analysis.
- ✅ Cache analysis in `ai_analyses` table (TTL 7 days) via
  `WhitepaperCacheService`. Only re-analyse if cache is stale.
- 🔲 `fundamental_score` optionally incorporates Gemini's analysis
  (innovation_score, token_utility assessment) when available.
  → Deferred to Future Phase: Gemini-Powered Analysis.
- ✅ Tests for whitepaper cache service (TDD). — 8 tests

### "Collect Now" button in GUI
- ✅ Backend: `POST /pipeline/collect-now` endpoint — triggers
  `daily_collection_job` asynchronously. Returns job ID.
- ✅ Backend: `GET /pipeline/status/{job_id}` — returns job progress
  (pending / running / completed / failed).
- ✅ Frontend: `pipeline.service.ts` with `triggerCollectNow()` and
  `fetchPipelineStatus()` API functions.
- ✅ Frontend: `CollectNowButton` component on Home (Rankings) page.
  Shows spinner while running, status on completion/failure.
- ✅ Tests for pipeline trigger endpoint (TDD). — 7 backend tests
- ✅ Tests for pipeline service + button (TDD). — 8 frontend tests

### Documentation
- ✅ Update `README.md` with all new CLI commands, AUTO_SEED, Twitter setup,
  Collect Now (CLI + GUI). Update `.env.example` placeholders.
- ✅ Update `CHANGELOG.md` with Phase 13 entries.

### Tests summary (actual)
- ✅ **59 new backend tests**: CLI (22), Twitter (14), sentiment (11),
  pipeline social/cmc (10), scorer real data (9), whitepaper cache (8),
  collect-now API (7). — **Total: 1191 backend tests, all green.**
- ✅ **8 new frontend tests**: pipeline service (4), CollectNowButton (4).
  — **Total: 152 frontend tests, all green.**
- ✅ All existing tests continue to pass.

**Deliverable:** Rankings use real social + dev + CMC data where available.
Seed data is optional. User can manage the database via CLI. Twitter/X and
Reddit data flow into scoring. Whitepaper analysis generates useful PDFs.
"Collect Now" button in the GUI.

---

## Phase 14 — Backtesting Real: Multi-Cycle Validation & Weight Calibration (target: ~2–3 weeks)

> Goal: Validate the scoring model against real historical cycles across
> multiple BTC cycles. Calibrate weights using backtesting results. Make
> the feedback loop work: backtest → calibrate → improve ranking.

### Problem statement
The current backtesting infrastructure (Phase 12) collects data for only
10 tokens across one cycle (2019-2021) and uses mostly synthetic data.
The `WeightCalibrator` exists but its results are never applied to the
live scoring pipeline. There is no feedback loop — running validation
does not improve the ranking.

The BTC market moves in ~4-year cycles. To trust the model, we need to
validate across at least 2-3 complete cycles and prove the scoring
formula would have identified winners **before** they pumped.

### Multi-cycle historical data collection
- ✅ Define token lists per cycle era:
  - **Cycle 1 (2015-2018):** BTC, ETH, XRP, LTC, DASH, XMR, NEM, NEO,
    EOS, IOTA, ADA, TRX, XLM, VET, BNB (15 tokens)
  - **Cycle 2 (2019-2021):** All of Cycle 1 + SOL, AVAX, MATIC, DOT,
    LINK, UNI, AAVE, LUNA, FTT, ATOM, ALGO, FIL, NEAR, DOGE, SHIB,
    FTM (31 tokens)
  - **Cycle 3 (2022-2025):** All of Cycle 2 + ARB, OP, TIA, INJ, JUP,
    SUI, SEI, APT, EIGEN, TAO, RNDR, FET, WLD, PEPE, BONK, WIF, FLOKI,
    PYTH, JTO (50 tokens)
  - `backtesting/cycle_config.py` — CycleDef, CycleTokenEntry, helpers.
    21 tests.
- ✅ `backtesting/multi_cycle_collector.py` — collects monthly snapshots
  from CoinGecko (`/market_chart/range`) for all tokens across all cycles.
  Uses rate limiting with configurable delay. Handles partial failures.
  16 tests.
- ✅ Persist to `historical_snapshots` table with cycle tag.
  Added `cycle_tag` column + migration. 4 tests.
- ✅ Tests for multi-cycle collector (TDD). Total: 41 tests.

### Ground truth definition
- ✅ `backtesting/ground_truth.py` — defines actual cycle performers:
  - For each cycle, compute actual ROI from cycle bottom to cycle top.
  - Tokens that did ≥5x from bottom to top = "winner".
  - Tokens that did ≥10x = "big winner".
  - PerformanceTier enum, GroundTruthEntry, CycleGroundTruth, build_ground_truth.
- ✅ Tests for ground truth computation (TDD). 28 tests.

### Historical scoring pipeline upgrade
- ✅ `backtesting/historical_scorer.py` upgrade — accepts configurable
  `WeightSet` for re-scoring with different weight combinations.
  Exposes all 5 pillar sub-scores on `HistoricalScoredToken`.
  Backward-compatible: default weights match Phase 9.
- ✅ Score each token at each snapshot → produce ranked list with
  configurable weights.
- ✅ Tests for upgraded historical scorer (TDD). 9 new + 12 existing = 21 tests.

### Validation engine upgrade
- ✅ `backtesting/validation_metrics.py` — existing module preserved,
  used by new re-scoring calibrator.
- ✅ `backtesting/cycle_report.py` — CycleMetrics, CrossCycleReport,
  build_cross_cycle_report with consistency score (1 − CV of precision).
  11 tests.
- ✅ Tests for validation + cycle report (TDD).

### Weight calibration with feedback loop
- ✅ `backtesting/weight_calibrator.py` upgrade —
  `calibrate_weights_with_rescoring()` re-scores and re-ranks tokens
  with each weight set (fixes the Phase 12 limitation where all combos
  got the same precision). Evaluates against ground truth. 7 new tests
  + 14 existing = 21 tests.
- ✅ `GET /backtesting/cycles` — returns available market cycles. 3 tests.
- ✅ `GET /backtesting/weights` — returns current active weight set
  (Phase 9 defaults for now). 4 tests.
- ✅ `models/scoring_weight.py` — ScoringWeight ORM model for persisting
  calibrated weights. Migration. 5 tests.
- 🔲 `POST /backtesting/apply-weights` — persists the calibrated weights
  to the database. The live `OpportunityEngine` reads weights from DB
  instead of hardcoded constants. (Deferred — needs DB session integration.)
- ✅ Tests for weight persistence and API (TDD). 12 new backend tests.

### Frontend: Backtesting multi-cycle UI
- ✅ `fetchCycles()` + `fetchActiveWeights()` service functions. 6 tests.
- ✅ MSW handlers for new endpoints.
- 🔲 Cycle selector dropdown: "2015-2018", "2019-2021", "2022-2025", "All"
  → Deferred to Phase 16.
- 🔲 Precision/Recall/HitRate per cycle displayed as cards.
  → Deferred to Phase 16.
- 🔲 Token breakdown table per cycle.
  → Deferred to Phase 16.
- 🔲 "Apply Best Weights" button + confirmation dialog.
  → Deferred to Phase 16.

### CI quality gate
- 🔲 Add backtesting validation to CI pipeline (optional, slow job).
  → Deferred to Future Phase.

### Tests summary
- ✅ ~114 new backend tests (21+16+4+28+9+11+7+5+3+4+6 = 114)
- ✅ ~6 new frontend tests
- ✅ All existing tests continue to pass (1299 backend + 158 frontend)

**Deliverable:** Multi-cycle token registry with 3 BTC cycles (2015–2025),
ground truth computation, upgraded scorer with configurable WeightSet,
re-scoring calibrator, cross-cycle report with consistency score, ScoringWeight
persistence model, and API endpoints for cycles & weights.

---

## Ranking Quality Loop — Pragmatic sprint (replaces Phase 15)

> **Goal:** Make the ranking answer one question: "Which altcoins could
> explode during the next crypto ATH?" Everything else is secondary.
>
> This sprint replaces the original Phase 15 plan. Instead of following
> the phased roadmap, we attack the 6 concrete blockers preventing the
> ranking from being useful — in priority order.

### Problem statement (current state)
The ranking shows USDT at #1, USD1 at #2, FDUSD at #3. Stablecoins and
wrapped tokens pollute the results. Scoring weights are hardcoded guesses
(0.30/0.25/0.20/0.15/0.10) that were never validated. Twitter and Reddit
collectors exist but their data is never persisted, so the scorer falls
back to heuristics for almost every token. The `CycleDetector` exists but
is never called in the live pipeline. There is no way to understand why a
token scores high.

### Item 1 — Filter stablecoins, wrapped tokens, and dead projects
- ✅ `scoring/token_filter.py` — `TokenFilter` class with configurable
  exclusion lists: stablecoins (USDT, USDC, DAI, BUSD, TUSD, FRAX, FDUSD,
  USD1 + 17 more), wrapped/bridged (WBTC, WETH, stETH, cbETH, rETH + 14
  more), dead tokens (volume < $10k or missing volume data).
- ✅ Rankings API applies filter before returning results (post-query).
- ✅ Frontend: category filter chips (DeFi, AI, L1, L2, Meme, etc.) with
  toggle exclude/include. Done in Phase 15 (`CategoryFilter` component).
- ✅ Tests for filtering logic — 27 unit tests + 6 API tests (TDD).

### Item 2 — Persist Twitter/Reddit data to social_data table
- ✅ Add `twitter_mentions_24h` + `twitter_engagement` columns to
  `SocialData` model + Alembic migration (`c9d0e1f2a3b4`).
- ✅ `persist_social_data()` helper in `jobs.py` — merges Reddit + Twitter
  data per symbol into a single `SocialData` row.
- ✅ `collect_twitter_data()` helper in `jobs.py` — orchestrates
  `TwitterTwikitCollector` for all symbols.
- ✅ `daily_collection_job` collects social data **before** scoring and
  merges `reddit_subscribers`, `reddit_posts_24h`, `sentiment_score`,
  `twitter_mentions_24h`, `twitter_engagement` into the processed dict.
- ✅ `PipelineScorer._score_adoption()` already uses `reddit_subscribers`
  and `reddit_posts_24h` — now they arrive from real data instead of
  heuristic fallback.
- ✅ Tests: 11 new tests (8 persist + 3 collect_twitter_data) — TDD.

### Item 3 — Connect calibrated weights to live scoring
- ✅ `POST /backtesting/apply-weights` — persists calibrated weights to
  `scoring_weights` table and sets `is_active=True` (deactivates previous).
- ✅ `OpportunityEngine.full_composite_score()` accepts optional `weights`
  dict — callers can pass DB-loaded weights instead of hardcoded constants.
- ✅ `weight_service.py` — `get_active_weights()` reads from DB via Redis
  cache (5 min TTL), falls back to Phase 9 defaults.
- ✅ `GET /backtesting/weights` now reads from weight service (DB → cache → defaults).
- ✅ Tests: 20 new tests (10 weight_service + 8 API apply-weights + 2 OpportunityEngine custom weights) — TDD.

### Item 4 — Run real backtesting + calibrate weights
- ✅ CLI command: `cryptoai backtest-collect <cycle>` — fetches real
  CoinGecko historical data via httpx, persists to `historical_snapshots`
  with cycle_tag. Validates cycle name, reports progress and errors.
- ✅ CLI command: `cryptoai backtest-calibrate [--cycle all] [--step 0.10] [--k 10]`
  — runs `calibrate_weights_with_rescoring()` against real historical data.
  Reports best weights, precision@K, and provides curl command to apply.
- ✅ After calibration, user can apply weights via `POST /backtesting/apply-weights`.
- ✅ Tests: 9 new tests (4 backtest-collect + 5 backtest-calibrate) — TDD.

### Item 5 — Wire CycleDetector into live scoring pipeline
- ✅ `daily_collection_job` calls `detect_cycle_phase()` once per run
  (uses `CycleDataCollector` + `CycleDetector.classify()`).
- ✅ `OpportunityEngine.cycle_adjusted_score()` applied to every token
  (bull=+10%, bear=−25%, accumulation=neutral, distribution=−10%).
- ✅ `cycle_phase` included in scored results dict for downstream use.
- ✅ Graceful fallback: if cycle detection fails, phase is `None` and
  scores remain unchanged (no adjustment).
- ✅ Tests: 8 new tests (5 cycle_adjusted_score + 3 detect_cycle_phase)
  + 1 existing test updated to mock detect_cycle_phase — TDD.
- ✅ Display current cycle phase on Rankings page header (frontend).
  Done in Phase 15 (`CycleIndicator` component wired to Home page header).

### Item 6 — Score explanation on Token Detail
- ✅ `scoring/score_explainer.py` — `ScoreExplainer.explain(token_data)`
  generates human-readable 1-2 sentence explanation per pillar
  (fundamental, growth, narrative, listing, risk) + overall summary.
  Uses `PillarExplanation` frozen dataclass with `to_dict()`.
- ✅ `GET /tokens/{symbol}/explanation` API endpoint — fetches token +
  latest score + market data + social data, passes to `ScoreExplainer`,
  returns `TokenExplanationSchema` (symbol, name, opportunity_score,
  list of pillar explanations). 404 when token or score not found.
- ✅ `_fetch_token_with_details()` helper — joins Token, TokenScore,
  MarketData, SocialData with latest-row subqueries.
- ✅ Tests: 14 ScoreExplainer + 7 API endpoint = 21 new tests — TDD.
- 🔲 Frontend: "Why this score?" section on Token Detail page.
  → Deferred to Phase 16 (Token Detail UX).

### Ranking Credibility Sprint (PR #28)
- ✅ Wire active weights into pipeline (`get_active_weights()` → `full_composite_score()`)
- ✅ Expand TokenFilter (exotic stables, gold-backed, non-crypto tokens)
- ✅ Token category classifier + risk multiplier (memecoin 0.70×, unknown 0.90×)
- ✅ Fix adoption scoring (rank+mcap+categories, social→narrative)
- ✅ Rebalance pillar weights (risk 0.10→0.30)
- ✅ Seed real backtest data (3 cycles, 69 tokens, real prices)
- ✅ Fix Twitter collector (short-circuit on empty credentials, pass Settings)
- ✅ Tests: 84 new tests (1483 total, 92.04% coverage)
- ✅ **Result:** FARTCOIN #1→#201, PEPE #2→#167, BTC→#1, ETH→#2

### Tests summary (actual)
- ✅ 105 new backend tests (Items 1-6 + Credibility Sprint + Twitter fix)
- ✅ 10 new frontend tests (Score Explanation + pipeline service)
- ✅ All existing tests pass. **1483 backend tests, 168 frontend tests.**

**Deliverable:** Rankings show only actionable altcoins (no stablecoins, no
wrapped tokens). Scores use real social data and calibrated weights. Cycle
phase influences ranking. User understands why each token scores high.
The system can answer: "Which cryptos could perform well in the next bull run?"
✅ COMPLETE

---

## Phase 15 — Category-Based Filtering + Professional DataTable (target: ~2–3 weeks) ✅ COMPLETE

> **Goal:** Replace the card grid with a professional data table powered by
> live token categories from CoinGecko. Users can filter by category, sort
> by any column, search by name/symbol, and configure which columns to show.
> No more hardcoded exclusion lists — filtering is entirely category-driven.

### Problem statement
Rankings still show FIGR_HELOC (#3), USDS (#4), USDE (#5) — stablecoins and
RWA tokens that pass the hardcoded `TokenFilter`. The `category` column on
the Token model is always `null`. The Home page uses a card grid with simple
client-side pagination — no sorting, no filtering, no search. With 200+
tokens, this is unusable. Users cannot filter by token type (L1, DeFi, Meme)
or exclude categories they don't care about (stablecoins, wrapped).

### Persist token categories from CoinGecko
- ✅ `category` column on `Token` model (VARCHAR 50, nullable, indexed) —
  already existed from Ranking Quality Loop. Alembic migration already applied.
- ✅ `daily_collection_job` calls `CoinGeckoCollector.collect_categories()`
  for **all** tokens (not just top 20) and merges CoinGecko categories into
  the processed dict **before** scoring, so `TokenCategoryClassifier.classify()`
  receives real category data instead of relying on symbol-based fallback.
- ✅ `_persist_results` always updates `token.category` — except when the
  new value is `"unknown"` and the token already has a real classification
  (prevents downgrading a known category on transient CoinGecko failures).
- ✅ Backfill: categories populated on every pipeline run for all tokens.
- ✅ Tests for category persistence in pipeline (TDD) — 7 new tests in
  `test_pipeline_category_population.py` + 1 updated test in
  `test_persist_category.py`.

### Backend: server-side filtering, sorting, pagination, search (PR #30)
- ✅ Refactored `GET /rankings/opportunities` with full query params:
  - `categories` — comma-separated list of categories to include
    (e.g. `?categories=l1,defi,ai`). Empty = all categories.
  - `exclude_categories` — comma-separated list to exclude
    (e.g. `?exclude_categories=memecoin,rwa`). Applied after include.
  - `sort` — column to sort by (default: `opportunity_score`).
    Allowed: all score columns + `rank`, `market_cap`, `volume_24h`, `name`.
  - `order` — `asc` or `desc` (default: `desc`).
  - `search` — text search on `symbol` and `name` (case-insensitive ILIKE).
  - `page` / `page_size` — server-side pagination (default: page=1, size=50).
  - Response includes `total_count` for pagination UI.
- ✅ Category-based filtering replaces hardcoded `TokenFilter.should_exclude()`.
  `TokenFilter` only filters truly broken data (null volume, dead tokens).
- ✅ `GET /rankings/categories` — returns distinct categories with token
  counts (`[{category: "l1", count: 42}, ...]`) for filter UI.
- ✅ Fixed 422 bug: `exclude_categories` default changed from `""` to `None`
  so omitting the param doesn't create an empty-string filter.
- ✅ Tests for all new query params and edge cases (TDD) — 46 new backend tests.

### Frontend: TanStack Table + category filters (PR #30 + current branch)
- ✅ Installed `@tanstack/react-table` (headless, styled with Tailwind).
- ✅ Replaced card grid with professional `RankingsTable` component:
  - **Column sorting** — click header to sort asc/desc. Server-side via
    `tableStore.sort` + `tableStore.order`.
  - **Global search** — text input searches symbol/name. Debounced,
    server-side via `tableStore.search`.
  - **Column visibility** — `ColumnPicker` toggle (11 tests). Some columns
    hidden by default (listing_probability, cycle_leader_prob).
  - **Server-side pagination** — page controls at bottom with prev/next.
  - **Cycle phase indicator** — `CycleIndicator` component in table header
    area (from deferred Ranking Quality Loop Item 5).
  - **Collect Now button** — in header, triggers pipeline manually.
- ✅ `CategoryFilter` component — chip bar showing available categories from
  `/rankings/categories`. Toggle exclude/include per category. Default
  excluded: `stablecoin`, `wrapped-tokens`. "Reset filters" button.
  Preferences saved to localStorage via Zustand persist. 8 tests.
- ✅ `PageSizeSelector` component — select dropdown (25/50/100 options),
  wired to `tableStore.setPageSize()`. 4 tests.
- ✅ `tokens.service.ts` — `fetchRankingOpportunities()` accepts
  `RankingsParams` (search, categories, exclude_categories, sort, order,
  page, page_size) and returns `{ data, total_count }`.
  `fetchCategories()` returns `CategoryCount[]`.
- ✅ `useTableStore` expanded with `excludeCategories`, `categories`,
  `search`, `sort`, `order`, `page`, `pageSize`, `setExcludeCategories`,
  `setSearch`, `setSort`, `setPage`, `setPageSize`, `resetFilters`.
  Zustand persist with localStorage. 20 store tests.
- ✅ Home page wires CategoryFilter + PageSizeSelector between search bar
  and data table. 2 new Home integration tests. 11/11 Home tests pass.
- ✅ Tests for RankingsTable (sorting, column display, links, empty state,
  category column) — 13 tests. Column reordering deferred.

### Reddit collector short-circuit
- 🔲 Same pattern as Twitter fix: `collect_social_data()` checks if Reddit
  is being rate-limited (403 responses) and short-circuits early instead
  of retrying for every token. Log informative skip message.
  → Deferred to Future Phase.
- 🔲 Tests (TDD). → Deferred to Future Phase.

### Documentation
- ✅ Update `README.md` with new query params, category system.
- ✅ Update `CHANGELOG.md` with Phase 15 entries.

### Tests summary (actual)
- ✅ **53 new backend tests** (46 server-side filtering/sorting/pagination +
  7 category population pipeline). **Total: 1536 backend tests, 92.28% coverage.**
- ✅ **46 new frontend tests** (13 RankingsTable + 20 tableStore + 8 CategoryFilter +
  4 PageSizeSelector + 2 Home integration - 1 removed card test).
  **Total: 214 frontend tests, all passing.**
- ✅ All existing tests continue to pass.

**Deliverable:** Rankings page is a professional data table with server-side
sorting, filtering by category, search, column configuration, and pagination.
Token categories populated from CoinGecko on every pipeline run. User can
toggle category exclusions via chip bar. Page size selector (25/50/100).
Preferences persist in localStorage.

---

## Phase 16 — Backtest Validation + Token Detail UX (target: ~2–3 weeks)

> **Goal:** Make backtesting produce actionable results. Improve the Token
> Detail page with an actions menu and richer data display.

### Problem statement
The backtesting infrastructure has real cycle price data (`real_cycle_prices.py`)
but has never been executed end-to-end. The Weight Calibrator can suggest
better weights but results are never automatically validated. The Token Detail
page has two separate download buttons (MD + PDF) and no room for future
actions. The radar chart shows 5 sub-pillars of Fundamental but users don't
understand this distinction vs the 5 main scoring pillars.

### Run and validate backtesting with real data
- 🔲 Execute `real_cycle_prices.py` ground truth for all 3 cycles.
- 🔲 Run `calibrate_weights_with_rescoring()` with real data.
- 🔲 Validate Precision@K across cycles. Document results.
- 🔲 If calibrated weights improve precision, apply via API and update
  defaults in `weight_service.py`.
- 🔲 Backtesting UI: cycle selector dropdown, per-cycle metrics cards,
  token breakdown table, "Apply Best Weights" button + confirmation
  (deferred from Phase 14).
- 🔲 Tests for end-to-end backtest flow (TDD).

### Token Detail UX improvements
- 🔲 Replace download buttons with **actions dropdown menu** (Radix
  `DropdownMenu`, already in dependencies). Actions: Download PDF,
  Download Markdown, future-proof for more actions.
- 🔲 Frontend: "Why this score?" section on Token Detail page (deferred
  from Ranking Quality Loop Item 6 — backend already done).
- 🔲 Clarify radar chart: rename "Score Breakdown" → "Fundamental
  Sub-Pillars" or add a tooltip explaining the distinction vs the 5
  main scoring pillars shown in Detailed Scores.
- 🔲 Show token category badge on Token Detail header.
- 🔲 Show risk multiplier if applicable (e.g. "Memecoin: 0.70× penalty").
- 🔲 Tests for new Token Detail components (TDD).

### Documentation
- 🔲 Update `README.md` and `CHANGELOG.md` with Phase 16 entries.

### Tests summary (estimated)
- 🔲 ~20-30 new backend tests (backtest validation flow)
- 🔲 ~20-25 new frontend tests (actions menu, score explanation, category badge)
- 🔲 All existing tests must continue to pass

**Deliverable:** Backtesting produces validated precision metrics across 3
real BTC cycles. Token Detail page has an actions menu, score explanations,
category badge, and clear radar chart labelling.

---

## Future Phases (planned — not yet numbered)

### Narratives & Ecosystems (target: TBD)
> Rebuild Narratives page with real social data from Twitter + Reddit.
> Rebuild Ecosystems with real graph edges (shared categories, price
> correlation, blockchain ecosystem). Make both pages useful.

### Alerts Tuning (target: TBD)
> Reduce alert volume from 300+ to ~10-20 per day. Smart thresholds
> based on historical alert accuracy. Only high-confidence alerts
> sent to Telegram.

### Gemini-Powered Analysis (target: TBD)
> Token Detail "Download PDF" generates real analysis via Gemini.
> `fundamental_score` optionally incorporates Gemini's assessment
> (innovation_score, token_utility). CI quality gate for backtesting.

### Remaining deferred items
- 🔲 CI quality gate for backtesting validation (from Phase 14)
- 🔲 `fundamental_score` optionally incorporates Gemini analysis (from Phase 13)
