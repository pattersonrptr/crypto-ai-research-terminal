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
- 🔲 Wire live `NarrativeDetector` pipeline to replace seed data in `GET /narratives`
  → **Moved to Phase 10** (requires real social data + cycle detection first)
- 🔲 Wire live `AlertRuleEngine` to scheduler so alerts fire automatically
  → **Moved to Phase 11** (requires full scoring pipeline first)

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
- 🔲 `Narratives` page — replace seed data with live `NarrativeDetector` output
  → **Moved to Phase 10**
- 🔲 `Alerts` page — real alerts from the rule engine (currently empty state)
  → **Moved to Phase 11**

### Production Infrastructure
- ✅ `infra/docker-compose.prod.yml` — production overrides (no bind mounts, resource limits)
- ✅ Nginx rate limiting + CORS hardening
- 🔲 Log rotation + structured log export (optional: Loki/Grafana) → **Deferred**
- ✅ `.env.example` updated with all new keys

**Status:** Pipeline works end-to-end (249 real tokens from CoinGecko). But only
`fundamental_score` and `opportunity_score` are populated — all other sub-scores
are 0.0. The remaining Phase 8 items (live narratives, alerts) depend on the full
scoring pipeline and are moved to Phases 10–11.

**Deliverable:** `collect-now` collects real data. API serves real scores.
Remaining scoring and prediction features addressed in Phases 9–12.

---

## Phase 9 — Full Scoring Pipeline (target: ~2–3 weeks)

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

### Upgrade FundamentalScorer
- 🔲 Expand `FundamentalScorer` from 4-metric → 5-sub-pillar model per SCOPE.md §6.8:
  - Technology (20%): use LLM analysis of whitepaper (via `WhitepaperAnalyzer`)
  - Tokenomics (20%): supply metrics, inflation rate, distribution, unlocks
  - Adoption (20%): TVL, volume trends, integrations
  - Dev Activity (20%): commits, contributors, releases (via `DevProcessor`)
  - Narrative Fit (20%): alignment with dominant narrative cluster
- 🔲 Persist each sub-pillar score individually in `token_scores` table:
  `technology_score`, `tokenomics_score`, `adoption_score`, `dev_activity_score`

### Wire existing scorers into pipeline
- 🔲 Wire `GrowthScorer.score()` — inputs from `DevProcessor` + `SocialProcessor`
  → persist `growth_score` in `token_scores`
- 🔲 Wire `RiskScorer.score()` — inputs from `RugpullDetector`, `ManipulationDetector`,
  `WhaleTracker`, `TokenomicsRisk` → persist `risk_score` in `token_scores`
- 🔲 Wire `NarrativeScorer.score()` — inputs from `NarrativeDetector` cluster matching
  → persist `narrative_score` in `token_scores`
- 🔲 Wire `ListingScorer.score()` — inputs from `ExchangeMonitor`, `ListingSignals`
  → persist `listing_probability` in `token_scores`
- 🔲 Wire `CycleLeaderModel.predict()` → persist `cycle_leader_prob` in `token_scores`

### Upgrade OpportunityEngine
- 🔲 Implement full 5-pillar composite formula from SCOPE.md §9:
  ```
  opportunity = (
    0.30 × fundamental +
    0.25 × growth +
    0.20 × narrative +
    0.15 × listing +
    0.10 × risk_adjustment
  ) × cycle_leader_boost
  ```
- 🔲 Replace Phase 1 fallback mode with real multi-pillar calculation
- 🔲 Graceful degradation: if a sub-score is unavailable, redistribute its weight

### Fix Token Detail API
- 🔲 Join `market_data` table in `GET /tokens/{symbol}` → return `price_usd`,
  `market_cap`, `volume_24h`, `ath`, `ath_change_pct`, `circulating_supply`
- 🔲 Return all 11 sub-scores in token response (not just fundamental + opportunity)
- 🔲 Radar chart data: `{technology, tokenomics, adoption, dev_activity, narrative_fit}`
  all non-zero

### AI-generated token analysis
- 🔲 Call `SummaryGenerator.generate()` via Ollama/Gemini for each scored token
- 🔲 Cache AI summaries in `ai_analyses` table (avoid re-generating daily)
- 🔲 Return AI summary in `GET /tokens/{symbol}` response
- 🔲 Include AI summary in PDF reports

### Tests (TDD)
- 🔲 Tests for upgraded `FundamentalScorer` (5-sub-pillar model)
- 🔲 Tests for upgraded `OpportunityEngine` (5-pillar formula)
- 🔲 Tests for pipeline integration (all scorers wired correctly)
- 🔲 Tests for Token Detail API with market data + all sub-scores
- 🔲 Frontend tests for populated radar chart + market metrics

**Deliverable:** Rankings show multi-dimensional scores. Radar chart is filled.
Token Detail page is actionable. PDF reports include AI analysis.

---

## Phase 10 — Live Narratives + Cycle Detection (target: ~2 weeks)

> Goal: Narratives page shows real detected clusters from social data.
> App knows the current market cycle. Ecosystems derived from real data.
> The system can identify what's gaining momentum NOW.

### Problem statement
Narratives page shows hardcoded `_SEED_NARRATIVES` (10 fake items). Ecosystems
page uses a hardcoded 15-node graph. The app has no cycle awareness — it doesn't
know we're in a bear market in 2026. Without cycle context, no prediction is
possible.

### Live narrative detection
- 🔲 Run `NarrativeDetector.detect()` on real social data (Twitter + Reddit mentions)
  as part of the scheduler pipeline
- 🔲 Persist detected narrative clusters to `narratives` table (replace seed fallback)
- 🔲 Compare current narratives vs 30d-ago snapshot → compute trend
  (`accelerating`, `growing`, `stable`, `declining`)
- 🔲 Remove `_SEED_NARRATIVES` fallback from `GET /narratives` once live data flows

### Cycle detection
- 🔲 New module: `app/analysis/cycle_detector.py`
  - BTC dominance trend (rising = risk-off, falling = altseason)
  - Total crypto market cap trend vs 200-day moving average
  - Fear & Greed index integration (Alternative.me API, free)
  - Market phase classification: `accumulation`, `bull`, `distribution`, `bear`
- 🔲 Expose `GET /market/cycle` API endpoint with current phase + confidence
- 🔲 Factor cycle phase into `OpportunityEngine` scoring (bear market = lower scores,
  bull market = boost for momentum tokens)
- 🔲 Display cycle phase indicator in frontend dashboard header

### Real ecosystem graph
- 🔲 Build graph from real token relationships:
  - Shared narrative clusters (tokens in same narrative = edge)
  - Price correlation matrix (corr > 0.7 = edge)
  - Shared blockchain ecosystem (same chain = edge)
- 🔲 Replace hardcoded seed graph in `GET /graph/communities`
- 🔲 Detect growing ecosystems (compare community sizes over time)

### Tests (TDD)
- 🔲 Tests for `CycleDetector` (phase classification, edge cases)
- 🔲 Tests for live narrative persistence
- 🔲 Tests for real ecosystem graph building
- 🔲 Frontend tests for cycle indicator

**Deliverable:** Narratives page shows real emerging trends. Dashboard shows
current market cycle. Ecosystems reflect real token relationships.

---

## Phase 11 — Alert Generation (target: ~1–2 weeks)

> Goal: Alerts page shows real fired alerts. Telegram notifications working.
> The system proactively warns about opportunities and risks.

### Problem statement
`AlertRuleEngine` and 7 concrete alert rules exist in code but are never called.
The scheduler pipeline ends at `_persist_results`. No alerts are ever generated.
The Alerts page is always empty.

### Wire alert generation into pipeline
- 🔲 Call `AlertRuleEngine.evaluate()` after scoring in `daily_collection_job`
- 🔲 Persist fired alerts to `alerts` table with full metadata
- 🔲 Send high-urgency alerts to Telegram via `TelegramBot`

### Alert rules (threshold-based, from scores)
- 🔲 `LISTING_CANDIDATE`: `listing_probability > 0.70`
- 🔲 `WHALE_ACCUMULATION`: whale tracker detects accumulation pattern
- 🔲 `NARRATIVE_EMERGING`: new narrative cluster with `momentum_score > threshold`
- 🔲 `RUGPULL_RISK`: `risk_score < 0.30` (dangerous zone)
- 🔲 `TOKEN_UNLOCK_SOON`: tokenomics risk detects >5% unlock in 30 days
- 🔲 `MANIPULATION_DETECTED`: manipulation detector flags wash trading / pump-dump
- 🔲 `MEMECOIN_HYPE_DETECTED`: social growth > 500% in 48h

### Daily digest
- 🔲 Generate `DAILY_REPORT` alert with top 10 movers, new alerts summary
- 🔲 Send daily digest to Telegram at configured hour

### Tests (TDD)
- 🔲 Tests for alert generation from real scores
- 🔲 Tests for Telegram delivery
- 🔲 Tests for daily digest formatting

**Deliverable:** Alerts fire automatically from real data. Telegram receives
notifications. User sees actionable alerts in the dashboard.

---

## Phase 12 — Backtesting Validation (target: ~2–3 weeks)

> Goal: Validate the scoring model against real historical cycles.
> Prove (or disprove) that the system can predict winners.

### Problem statement
Backtesting runs on synthetic sinusoidal data from `seed_historical_data.py`.
There's no way to know if the scoring model would have predicted the tokens
that actually did 10x+ in past bull runs. Without validation, the model is
just noise.

### Historical data collection
- 🔲 Collect real historical data from CoinGecko `/coins/{id}/market_chart/range`
  for 2019-01 to 2021-12 (pre-bull → peak → post-peak)
- 🔲 Collect historical dev activity snapshots (GitHub API, if available)
- 🔲 Store as `historical_snapshots` in DB (full serialized state per date)

### Historical scoring pipeline
- 🔲 Run the full scoring pipeline on historical snapshots
  ("What would the model have scored in January 2020?")
- 🔲 Generate a ranked list per snapshot date
- 🔲 Identify actual 10x+ performers from the subsequent bull cycle

### Validation metrics
- 🔲 `Precision@10`: of the top 10 recommended, how many did 5x+?
- 🔲 `Recall@50`: of the 50 that did 5x+, how many were in our top 50?
- 🔲 `Hit rate`: % of recommended tokens that outperformed the market
- 🔲 Display metrics in backtesting UI with per-token breakdown

### Weight calibration
- 🔲 If precision < 50%, run parameter sweep on pillar weights
- 🔲 If a specific sub-score has no predictive power, consider removing it
- 🔲 Document calibration results for future cycles

### Tests (TDD)
- 🔲 Tests for historical data loading
- 🔲 Tests for historical scoring pipeline
- 🔲 Tests for validation metrics computation

**Deliverable:** "If we had run this model in January 2020, it would have
recommended SOL, AVAX, MATIC... with 60% precision@10." Model is calibrated
and trustworthy (or known limitations are documented).
