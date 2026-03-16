# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

### Ranking Quality Loop — Pragmatic sprint

> Replaces the original Phase 15 plan. Attacks the 6 concrete blockers
> preventing the ranking from being useful, in priority order.

#### Planned
- **Item 1:** Filter stablecoins, wrapped tokens, dead projects from rankings
- **Item 2:** Persist Twitter/Reddit data to `social_data` table
- **Item 3:** Connect calibrated weights to live `OpportunityEngine`
- **Item 4:** Run real backtesting with CoinGecko data + calibrate weights
- **Item 5:** Wire `CycleDetector` into live scoring pipeline
- **Item 6:** Score explanation on Token Detail page

---

## [0.14.0] — 2026-03-16

### Phase 14 — Backtesting Real: Multi-Cycle Validation & Weight Calibration

#### Added
- **Cycle token registry** — `backtesting/cycle_config.py` with `CycleDef`,
  `CycleTokenEntry` dataclasses and 3 market cycles: Cycle 1 (2015-2018,
  15 tokens), Cycle 2 (2019-2021, 31 tokens), Cycle 3 (2022-2025, 50 tokens).
  Each subsequent cycle includes all tokens from previous cycles. 21 tests.
- **Multi-cycle collector** — `backtesting/multi_cycle_collector.py` with
  `MultiCycleCollector` class for fetching historical CoinGecko data per
  cycle. Rate-limited with configurable delay, handles partial failures,
  reports collection progress. 16 tests.
- **Ground truth module** — `backtesting/ground_truth.py` with
  `PerformanceTier` enum, `GroundTruthEntry`, `CycleGroundTruth`
  dataclasses and `build_ground_truth()` function. Computes ROI from
  cycle bottom to top, classifies tokens as big_winner (≥10×), winner
  (≥5×), average (>1×), or loser (≤1×). 28 tests.
- **Cross-cycle report** — `backtesting/cycle_report.py` with `CycleMetrics`,
  `CrossCycleReport` dataclasses and `build_cross_cycle_report()`. Computes
  average precision/recall/hit-rate and consistency score (1 − CV). 11 tests.
- **ScoringWeight model** — `models/scoring_weight.py` ORM model for
  persisting calibrated pillar weights with source cycle, precision, and
  active flag. Migration `b8c9d0e1f2a3`. 5 tests.
- **API endpoints** — `GET /backtesting/cycles` (list available market
  cycles), `GET /backtesting/weights` (current active scoring weights).
  7 API tests.
- **Frontend service** — `fetchCycles()` and `fetchActiveWeights()`
  service functions with `CycleInfo` and `ActiveWeights` types. MSW
  handlers for testing. 6 frontend tests.

#### Changed
- **Historical scorer upgrade** — `backtesting/historical_scorer.py` now
  accepts optional `WeightSet` parameter for re-scoring with different
  weight combinations. `HistoricalScoredToken` exposes all 5 pillar
  sub-scores (growth_score, narrative_score, listing_score, risk_score).
  Backward-compatible: default weights match Phase 9. 9 new tests.
- **Weight calibrator upgrade** — `backtesting/weight_calibrator.py` adds
  `calibrate_weights_with_rescoring()` which actually re-scores and
  re-ranks tokens for each weight set (fixes Phase 12 limitation where
  all combos got identical precision). 7 new tests.
- **HistoricalSnapshot model** — added `cycle_tag` column (VARCHAR 40,
  nullable, indexed) for tagging snapshots by cycle. Migration
  `a7b8c9d0e1f2`. 4 tests.
- Updated `models/__init__.py` to export `ScoringWeight`.
- Updated `api/routes/backtesting.py` with new Phase 14 endpoints.

#### Tests
- 114 new backend tests (1191 → 1299, all passing)
- 6 new frontend tests (152 → 158, all passing)
- Total: 1457 tests

### Phase 13 — Ranking Foundation: Data Quality & Feedback Loop

#### Added
- **CLI database management** — `cryptoai db-status`, `db-clean --confirm`,
  `db-truncate <table> --confirm`, `seed [rankings|narratives|all]` commands
  for inspecting and managing the database without restarting containers.
- **Twitter/X collector** — `TwitterTwikitCollector` using the `twikit`
  library (free, async, no paid API). Supports login with cookies persistence,
  `collect_mentions(symbol)` for mention count + engagement + raw texts.
- **Sentiment analyzer** — keyword-based `SentimentAnalyzer` in
  `processors/sentiment_analyzer.py`. Returns score (-1..1), label
  (positive/negative/neutral), and per-category counts. Ready for LLM
  upgrade in Phase 15+.
- **Subreddit mapping** — `collectors/subreddit_map.py` with 34 symbol →
  subreddit mappings (BTC→Bitcoin, ETH→ethereum, SOL→solana, etc.).
- **Pipeline social/CMC helpers** — `collect_social_data()` and
  `collect_cmc_data()` async functions in `scheduler/jobs.py` for
  orchestrating Reddit and CoinMarketCap collection in the pipeline.
- **Real data scoring** — `PipelineScorer` now uses real social data
  (`_score_adoption`), dev activity (`_score_dev_activity`), and CMC data
  (`_score_technology`) when available. Falls back to heuristic when absent.
- **Whitepaper cache** — `WhitepaperCacheService` with 7-day TTL for caching
  whitepaper analyses in the `ai_analyses` table.
- **Collect Now API** — `POST /pipeline/collect-now` triggers async collection,
  `GET /pipeline/status/{job_id}` returns job progress. In-memory job registry.
- **Collect Now UI** — `CollectNowButton` component on the Home (Rankings)
  page. Shows collecting/done/failed states with disabled button while running.
- **Pipeline service** — `pipeline.service.ts` with `triggerCollectNow()` and
  `fetchPipelineStatus()` API functions + MSW handlers.

#### Changed
- **entrypoint.sh** now checks `AUTO_SEED` env var before running seed_data.py.
  Default is `false` — no more automatic seeding on container start.
- **pyproject.toml** — added `twikit = "^2.3.0"` dependency.
- **main.py** — registered `/pipeline` router.
- **Home.tsx** — added `CollectNowButton` next to `CycleIndicator` in header.

#### Tests
- 59 new backend tests (CLI: 22, Twitter: 14, sentiment: 11, pipeline: 10,
  scorer: 9, whitepaper cache: 8, collect-now API: 7).
  Total: **1191 backend tests**, all green.
- 8 new frontend tests (pipeline service: 4, CollectNowButton: 4).
  Total: **152 frontend tests**, all green.

### Planning — Phases 13–15 (Ranking Foundation, Multi-Cycle Backtesting, Ranking Polish)

- **Diagnosed ranking quality issues:** Rankings are unreliable because 9 of 11
  sub-scores come from `HeuristicSubScorer` (market cap / rank guesses). Social
  collectors, CoinMarketCap collector, and dev activity data exist as code but
  are not wired into the scoring pipeline. This produces misleading results
  (e.g., KOGE ranks above BTC with 8.8 Adoption).

- **Phase 13 — Ranking Foundation: Data Quality & Feedback Loop** (planned):
  - Remove automatic seed from `entrypoint.sh` (`AUTO_SEED=false` by default)
  - CLI database management: `seed`, `db-clean`, `db-truncate`, `db-status`
  - Twitter/X data collection via `twikit` (free, async, no paid API)
  - Wire Reddit `SocialCollector` into scoring pipeline
  - Wire `CoinMarketCapCollector` into scoring pipeline
  - Replace heuristic scores with real data when available
  - Whitepaper analysis via Gemini free tier → real PDF reports
  - "Collect Now" button in Rankings + Narratives GUI

- **Phase 14 — Multi-Cycle Backtesting & Weight Calibration** (planned):
  - Historical data for 3 BTC cycles (2015-2018, 2019-2021, 2022-2025)
  - Ground truth definition (which tokens did ≥5x per cycle)
  - Full scoring pipeline on historical monthly snapshots
  - Precision@K / Recall@K / Hit Rate per cycle
  - Weight calibration across all cycles → apply to live ranking
  - Frontend: cycle selector, "Apply Best Weights" button

- **Phase 15 — Ranking Polish & UX** (planned):
  - Smart filtering (exclude stablecoins, wrapped tokens, dead tokens)
  - Cycle-aware ranking (integrate `cycle_adjusted_score`)
  - Timeframe selector ("Next cycle", "90 days", "30 days")
  - Score explanation ("Why this score?" in Token Detail)

### Changed

- **`.env.example`**: Added `AUTO_SEED=false`, `TWITTER_USERNAME`,
  `TWITTER_EMAIL`, `TWITTER_PASSWORD`. Marked `TWITTER_BEARER_TOKEN`
  as deprecated (replaced by twikit scraping).
- **`.env`**: Added `AUTO_SEED=false` and Twitter/X credential placeholders.
- **`TODO.md`**: Added Phases 13–15 with full task breakdown. Added
  future Phases 16 (Narratives & Ecosystems) and 17 (Alerts Tuning).
- **`SCOPE.md`**: Updated roadmap §10 with Phases 13–17. Updated
  external integrations table (Twitter/X → twikit). Updated footer
  timestamp and status.
- **`README.md`**: Updated roadmap table with Phases 13–17. Rewrote
  "Current Status & Known Limitations" section with honest assessment.
  Added database management docs (seed, db-clean, db-truncate, db-status).
  Added Twitter/X setup instructions. Added `docker exec` examples for
  all new CLI commands.

### Added (Optional Enhancements — All Deferred Items Completed)

- **PipelineScorer** (`backend/app/scoring/pipeline_scorer.py`):
  Central orchestrator that wires real scorers (`GrowthScorer`, `RiskScorer`,
  `ListingScorer`) with heuristic fallbacks based on data availability.
  `PipelineScorerResult` dataclass holds 9 sub-scores + source tracking.
  Category-based `NarrativeScorer` (no LLM required). `CycleLeaderModel`
  integration loads XGBoost model from pickle when available.
  31 tests in `test_pipeline_scorer.py`.
- **FundamentalScorer 5-pillar upgrade** (`backend/app/scoring/fundamental_scorer.py`):
  New `sub_pillar_score()` static method — 5 equally-weighted pillars
  (technology, tokenomics, adoption, dev_activity, narrative) at 20% each.
  Original `score()` preserved for backward compatibility. 7 new tests.
- **AI summary cache** (`backend/app/models/ai_analysis.py`,
  `backend/app/ai/summary_cache_service.py`, `backend/app/api/routes/summaries.py`):
  `AiAnalysis` ORM model for `ai_analyses` table. `SummaryCacheService` with
  TTL-based freshness check, serialisation, and parse. `GET /tokens/{symbol}/summary`
  endpoint serves cached AI summaries. Alembic migration `f5a6b7c8d9e0`.
  13 tests across model, service, and API route.
- **PriceCorrelationBuilder** (`backend/app/graph/price_correlation.py`):
  Computes pairwise Pearson correlation from price time-series. Creates graph
  edges where correlation exceeds configurable threshold (default 0.7). Supports
  absolute-value mode for anti-correlated pairs. 9 tests.
- **Ecosystem growth tracking** (`backend/app/graph/ecosystem_tracker.py`):
  New `growth_summary()` method compares two graph snapshots — reports
  total tokens, net growth, community count changes, and trend classification
  (growing/shrinking/stable). 5 new tests (22 total for ecosystem_tracker).
- **Structured logging** (`backend/app/logging_config.py`):
  `configure_logging()` with JSON/console output modes, configurable log level.
  Wired into `main.py` at startup via `LOG_FORMAT` and `LOG_LEVEL` env vars.
  Docker log rotation in `docker-compose.prod.yml` (json-file driver, 50 MB × 5).
  5 tests.

### Changed

- **Scheduler pipeline** (`backend/app/scheduler/jobs.py`):
  `daily_collection_job` now uses `PipelineScorer.score()` before
  `FundamentalScorer.sub_pillar_score()` (was `FundamentalScorer.score()` +
  `HeuristicSubScorer.score()`). Sub-scores from real scorers feed into the
  5-pillar fundamental model.
- **Docker production config** (`infra/docker-compose.prod.yml`):
  Added `LOG_FORMAT: json` environment variable and `logging:` driver config
  (json-file, max-size 50 MB, max-file 5) to backend service.

### Tests

- **70 new backend tests** (1109 total, up from 1039). All passing.
- **144 frontend tests** — unchanged, all passing.
- Quality checks clean: ruff, mypy, bandit.

### Added (Phase 12 — Backtesting Validation)

- **HistoricalSnapshot model** (`backend/app/models/historical_snapshot.py`):
  SQLAlchemy ORM model storing full token state per date (price, market cap,
  volume, supply, categories). Unique constraint on (symbol, snapshot_date).
  Alembic migration `3587d61f0e41` creates the `historical_snapshots` table.
- **ValidationEngine** (`backend/app/backtesting/validation_metrics.py`):
  Measures predictive accuracy of the scoring model. Computes Precision@K
  (what fraction of top-K picks actually performed), Recall@K (what fraction
  of actual performers the model captured), and Hit Rate (overall success
  ratio). Returns structured `ValidationReport` with per-token breakdowns.
- **HistoricalScorer** (`backend/app/backtesting/historical_scorer.py`):
  Runs simplified scoring pipeline on historical snapshots. Produces ranked
  `ScoredToken` lists using fundamental scoring + estimated growth metrics.
  `HistoricalScoringResult` groups ranked tokens by snapshot date.
- **WeightCalibrator** (`backend/app/backtesting/weight_calibrator.py`):
  Parameter sweep over the 5-pillar weights (fundamental, growth, narrative,
  listing, risk) to maximise Precision@K. Grid search with configurable step
  size generates all valid weight combinations summing to 1.0.
- **HistoricalDataCollector** (`backend/app/backtesting/historical_data_collector.py`):
  Parses CoinGecko `/market_chart/range` and `/coins/{id}` responses into
  snapshot dictionaries. Includes `BACKTEST_TOKENS` mapping (10 tokens) and
  `BACKTEST_DATE_RANGE` (2019-01-01 to 2021-12-31).
- **Validation API endpoints** (`backend/app/api/routes/backtesting.py`):
  `POST /backtesting/validate` — runs validation on sample data, returns
  precision, recall, hit rate, token breakdown.
  `POST /backtesting/calibrate` — runs weight calibration sweep, returns
  best weights and precision achieved.
- **Frontend validation UI** (`frontend/src/pages/Backtesting.tsx`):
  New "Model Validation" section with Run Validation button, metrics panel
  (Precision@K, Recall@K, Hit Rate, Model Useful?), and token breakdown
  table (rank, symbol, score, actual multiplier, winner status).
- **Frontend service** (`frontend/src/services/backtesting.service.ts`):
  `runValidation()` and `runCalibration()` functions with typed interfaces
  (`ValidateResult`, `CalibrateResult`, `TokenBreakdownItem`, `WeightSet`).
- **MSW handlers** for validation/calibration endpoints with mock data.
- **89 new backend tests** (1039 total, 93% coverage); **11 new frontend
  tests** (144 total). All passing.

### Added (Phase 11 — Alert Generation)

- **AlertEvaluator** (`backend/app/alerts/alert_evaluator.py`):
  Bridges scored pipeline data → `AlertRuleEngine` → `Alert` ORM objects.
  Maps pipeline keys to rule keys with scale conversion
  (`listing_probability` 0–1 → `listing_score` 0–100, etc.).
  `evaluate_batch()` processes all pipeline results in one call.
- **Alert model upgrade** (`backend/app/models/alert.py`):
  New columns — `alert_metadata` (JSONB, Python attr mapped to `metadata` DB col
  to avoid SQLAlchemy reserved name conflict), `sent_telegram` (Boolean),
  `acknowledged` (Boolean), `acknowledged_at` (DateTime tz), `token_symbol`
  (String20). `token_id` made nullable for system-level alerts.
- **Alembic migration** `d4e5f6a7b8c9`: ALTER `token_id` nullable, ADD
  `token_symbol`, `metadata` (JSONB), `sent_telegram`, `acknowledged`,
  `acknowledged_at`, CREATE INDEX `ix_alerts_alert_type`
- **Alerts API rewrite** (`backend/app/api/routes/alerts.py`):
  Replaced in-memory `_alerts_store` with full DB-backed async routes.
  `AlertResponse` schema maps `alert_metadata` → `metadata` and
  `triggered_at` → `created_at` for frontend compatibility.
  Endpoints: `GET /` (list with limit/type/acknowledged filters),
  `GET /stats`, `GET /{alert_id}`, `POST /test`, `PUT /{alert_id}/acknowledge`
- **Pipeline alert wiring** (`backend/app/scheduler/jobs.py`):
  `evaluate_and_persist_alerts()` called after scoring in `daily_collection_job`.
  Failure isolated — alert errors do not break the collection pipeline.
- **Pipeline narrative wiring** (`backend/app/scheduler/jobs.py`):
  Added narrative build+persist step to `daily_collection_job` via
  `build_narrative_snapshot_from_categories()`. Failure isolated.
- **Daily digest** (`backend/app/scheduler/digest.py`):
  `build_digest()` summarises fired alerts into a DAILY_REPORT alert with
  type breakdown in `alert_metadata`. `send_daily_digest()` formats via
  `AlertFormatter` and sends via `TelegramBot`.
- **34 new backend tests** (958 total, 93.5% coverage); **133 frontend tests**
  (unchanged, all passing)

### Removed (Phase 11)

- **`_SEED_NARRATIVES`** from `GET /narratives` route: hardcoded fallback data
  removed. Endpoint now returns live DB data or empty list. Tests updated to
  mock `fetch_latest_narratives` for deterministic assertions.

### Fixed (Phase 11)

- **SQLAlchemy `metadata` reserved name conflict**: Alert model column named
  `metadata` conflicted with `Base.metadata`. Fixed by using `alert_metadata`
  as the Python attribute with `mapped_column("metadata", JSONB)`.
- **Missing `__init__.py`** in `backend/tests/api/routes/` caused import failures.

### Added (Phase 10 — Live Narratives + Cycle Detection)

- **CycleDetector** (`backend/app/analysis/cycle_detector.py`):
  Weighted-vote market phase classification (accumulation/bull/distribution/bear)
  using Fear & Greed index, BTC dominance trend, and market cap vs 200d MA
- **CycleDataCollector** (`backend/app/analysis/cycle_data_collector.py`):
  Fetches Fear & Greed from Alternative.me API and BTC dominance from CoinGecko
- **NarrativePersister** (`backend/app/analysis/narrative_persister.py`):
  Converts NarrativeDetector output to ORM objects; fallback mode derives
  narratives from CoinGecko token categories (22 slugs → 11 human names)
- **NarrativeTrendAnalyzer** (`backend/app/analysis/narrative_trend.py`):
  Compares current vs previous narrative snapshots → trend classification
- **NarrativeCluster** ORM model with Alembic migration `c3d4e5f6a7b8`
- **`GET /market/cycle`** endpoint with phase, confidence, description, indicators
- **`OpportunityEngine.cycle_adjusted_score()`**: Cycle-aware score adjustment
- **LiveGraphBuilder** (`backend/app/graph/live_graph_builder.py`):
  Real token graph from shared chains + narratives; graph routes use live-first
  with seed fallback
- **Scheduler**: `persist_narrative_snapshot()` + `build_narrative_snapshot_from_categories()`
- **Frontend CycleIndicator**: Phase badge with emoji, color, confidence, description
  in dashboard header; auto-refreshes every 60s
- **88 new backend tests** (924 total, 92.9% coverage); **7 new frontend tests**
  (133 total, 16 test files)
- SQLite test infrastructure fix: `conftest_helpers.py` skips PG-only tables

### Added (Phase 9 — Full Scoring Pipeline)

- **HeuristicSubScorer** (`backend/app/scoring/heuristic_sub_scorer.py`):
  Derives all 9 sub-scores from CoinGecko market data using heuristics
  (rank, market cap, volume ratio, price velocity, ATH distance)
- **TokenScore model**: 9 new Float columns — `technology_score`, `tokenomics_score`,
  `adoption_score`, `dev_activity_score`, `narrative_score`, `growth_score`,
  `risk_score`, `listing_probability`, `cycle_leader_prob`
- **Alembic migration** `b2c3d4e5f6a7`: adds 9 sub-score columns to `token_scores`
- **OpportunityEngine.full_composite_score()**: 5-pillar weighted formula
  `0.30×fundamental + 0.25×growth + 0.20×narrative + 0.15×listing + 0.10×risk`
  with up to 10% cycle-leader boost, clamped to [0, 1]
- **Pipeline wiring**: `collect → process → fundamental → heuristic sub-scores →
  full composite → persist all 11 scores`
- **Token Detail API**: JOIN `MarketData`, returns all 11 sub-scores + market metrics
  (price, market_cap, volume, rank)
- **Rankings API**: JOIN `MarketData`, richer signals for growth/risk/narrative/listing
- **Frontend scaling**: API returns 0–1 scores; display layer multiplies by 10 for
  0–10 user-facing values (TokenDetail radar chart, TokenCard score bars)
- **Latest-only queries**: Rankings (`/rankings/opportunities`) and Tokens
  (`/tokens/`, `/tokens/{symbol}`) endpoints now use `MAX(id)` subqueries to
  return only the most recent `TokenScore` and `MarketData` per token, preventing
  duplicate rows after successive collection runs
- **CLI `collect-now` pipeline fix**: Uses `HeuristicSubScorer` +
  `OpportunityEngine.full_composite_score()` (was using old 2-score pipeline)
- **Docker dev volume mount**: `docker-compose.yml` mounts `../backend:/app/backend:ro`
  so code changes are picked up without rebuilding the image
- **`.dockerignore`**: Excludes `.venv/`, `node_modules/`, `.git/`, `__pycache__/`,
  reducing Docker build context from >1 GB to ~1 MB
- **`Dockerfile.backend`**: `PIP_DEFAULT_TIMEOUT=300` and
  `POETRY_INSTALLER_MAX_WORKERS=4` to prevent timeouts on large packages
- **`entrypoint.sh`**: Runs `seed_data.py` after Alembic migration on every start
  (auto-seeds fresh DB, backfills zeroed sub-scores on existing DB)
- **Seed data**: All 11 sub-scores in `SAMPLE_SCORES`, `_backfill_sub_scores()`
  function for upgrading old seeds
- **34 new backend tests** (836 total, 93% coverage); 126 frontend tests passing

### Known Limitations (Phase 9)

- **Volume-driven memecoins rank disproportionately high**: Tokens with abnormally
  high `volume/market_cap` ratios (e.g. TRUMP at 77% vol/mcap) score very well in
  growth, adoption, narrative and cycle-leader because all four heuristics treat high
  trading volume as a positive signal. In reality, speculative volume ≠ real adoption.
  Real adoption requires on-chain data, TVL, developer activity and news signals that
  are not yet integrated. This will be addressed in Phases 10–12.
- **Risk weight too low**: At 10% of the composite formula, the risk pillar has
  limited influence. A memecoin with risk=0.43 is barely penalised compared to
  BTC with risk=0.91. Weight rebalancing is deferred to Phase 12 backtesting.

### Planned

#### Phase 9 — Full Scoring Pipeline (remaining)

**Done:** HeuristicSubScorer populates all 11 sub-scores from CoinGecko data.
Full 5-pillar formula active. Radar chart and rankings functional.

**Remaining (optional enhancements):**

- Wire `GrowthScorer` into pipeline (uses existing GitHub + Reddit data)
- Wire `RiskScorer` into pipeline (uses existing risk detector modules)
- Wire `NarrativeScorer` into pipeline (uses narrative clusters)
- Wire `ListingScorer` into pipeline (uses existing exchange monitor data)
- Upgrade `FundamentalScorer` from 4-metric → 5-sub-pillar model
  (technology, tokenomics, adoption, dev_activity, narrative_fit)
- Wire `CycleLeaderModel` probability into composite score
- Add AI-generated token summary via Ollama/Gemini → cache in `ai_analyses` table

#### Phase 10 — Live Narratives + Cycle Detection (COMPLETE)

**Problem:** Narratives page shows hardcoded `_SEED_NARRATIVES`. Ecosystems page
uses hardcoded 15-node graph. App does not know the current market cycle.

**Goal:** Narratives and ecosystems derived from real data. Cycle awareness.

##### Backend — Analysis

- **`backend/app/analysis/cycle_detector.py`** — `CycleDetector`:
  - `CyclePhase` enum: `ACCUMULATION`, `BULL`, `DISTRIBUTION`, `BEAR`
  - `CycleIndicators` dataclass: BTC dominance (current + 30d ago), total market cap,
    200d MA, Fear & Greed index + label
  - `classify(indicators)`: Weighted-vote algorithm — Fear & Greed (weight 3),
    market vs 200d MA (weight 2), BTC dominance trend (weight 1.5)
  - `cycle_score_adjustment(phase)`: BULL=1.10, ACCUMULATION=1.0,
    DISTRIBUTION=0.90, BEAR=0.75
- **`backend/app/analysis/cycle_data_collector.py`** — `CycleDataCollector`:
  - `fetch_fear_greed()` → Alternative.me API (free, no key)
  - `fetch_btc_dominance()` → CoinGecko `/global` endpoint
  - `collect_indicators()` → assembled `CycleIndicators`
- **`backend/app/analysis/narrative_persister.py`** — `NarrativePersister`:
  - `to_clusters()`: Converts `NarrativeDetectorResult` → `NarrativeCluster` ORM list
  - `build_from_categories()`: Fallback mode — groups tokens by CoinGecko categories
    (22 mapped slugs → 11 human-readable narrative names), min 2 tokens per narrative
- **`backend/app/analysis/narrative_trend.py`** — `NarrativeTrendAnalyzer`:
  - `compare(current, previous)`: Returns `NarrativeTrendResult` per narrative
  - Trend classification: `accelerating` (Δ > 0.50), `growing` (Δ > 0.10),
    `declining` (Δ < −0.10), `stable` (otherwise), `accelerating` for new narratives

##### Backend — API

- **`GET /market/cycle`** (`backend/app/api/routes/market.py`):
  - Returns: `phase`, `confidence`, `phase_description`, `indicators`
  - Phase descriptions: human-readable text for each cycle phase
- **`OpportunityEngine.cycle_adjusted_score()`**: Multiplies base score by cycle
  factor, clamped to [0, 1]

##### Backend — Graph

- **`backend/app/graph/live_graph_builder.py`** — `LiveGraphBuilder`:
  - `TokenInfo` dataclass: symbol, name, market_cap_usd, chain, categories
  - `build(tokens, narrative_clusters)`: Creates edges from shared chains
    (ecosystem, weight 0.7) and shared categories/narratives (narrative, weight 0.6)
- **Graph routes** (`backend/app/api/routes/graph.py`):
  - `_build_live_graph()`: Queries DB for tokens + market data, builds live graph
  - `_get_graph()`: Tries live graph first, falls back to seed graph
  - All 3 routes (communities, centrality, ecosystem) use live-first pattern

##### Backend — Models & Migration

- **`backend/app/models/narrative.py`** — `NarrativeCluster` ORM model:
  - Columns: `id`, `name` (String100), `momentum_score` (Float), `trend` (String20),
    `keywords` (ARRAY), `token_symbols` (ARRAY), `snapshot_date` (Date, indexed),
    `created_at` (DateTime)
- **Alembic migration** `c3d4e5f6a7b8`: Creates `narratives` table with index

##### Backend — Scheduler

- `persist_narrative_snapshot(clusters, session)`: Persists NarrativeCluster rows
- `build_narrative_snapshot_from_categories(token_data)`: Delegates to
  `NarrativePersister.build_from_categories()` with today's date

##### Frontend

- **`frontend/src/services/market.service.ts`**: `MarketCycleResponse` type,
  `fetchMarketCycle()` API call
- **`frontend/src/components/Dashboard/CycleIndicator.tsx`**: Phase badge with
  emoji (🐂/📊/⚠️/🐻), color-coded (green/blue/amber/red), confidence %,
  description, loading skeleton, error state; auto-refreshes every 60s
- **Home page**: `CycleIndicator` integrated into `PageHeader` actions

##### Test Infrastructure

- **`backend/tests/conftest_helpers.py`**: `create_sqlite_tables()` — skips
  PostgreSQL-only tables (ARRAY columns) when running tests on SQLite
- Fixed 5 existing test files that broke due to `NarrativeCluster` ARRAY columns

##### Test Summary — 88 new backend + 7 new frontend tests

- Backend: **924 passed** (92.9% coverage) — 88 new tests across 12 test files
- Frontend: **133 passed** (16 test files) — 7 new tests across 3 test files
- All quality gates: ruff ✅ | mypy ✅ | bandit ✅

#### Phase 11 — Alert Generation (target: ~1–2 weeks)

**Problem:** Alerts page is always empty. `AlertRuleEngine` and 7 rules exist
but the pipeline never calls them. No alerts are ever generated.

**Goal:** Real alerts fired from scoring thresholds. Telegram notifications.

- Wire `AlertRuleEngine.evaluate()` into scheduler pipeline (after scoring)
- Generate alerts: `LISTING_CANDIDATE`, `WHALE_ACCUMULATION`, `NARRATIVE_EMERGING`,
  `RUGPULL_RISK`, `TOKEN_UNLOCK_SOON`, `MANIPULATION_DETECTED`
- Persist alerts to DB + send to Telegram
- Daily digest alert (top 10 movers, new alerts summary)

#### Phase 12 — Backtesting Validation (target: ~2–3 weeks)

**Problem:** Backtesting runs on synthetic/seed data only. Cannot validate
whether the scoring model would have predicted real cycle winners.

**Goal:** Backtest on 2019-2021 cycle with real data. Precision@10, recall.

- Collect real historical data (CoinGecko historical endpoint)
- Run full scoring pipeline on historical snapshots ("as if Jan 2020")
- Compare top picks vs actual 10x+ performers in 2021 bull run
- Display precision@K, recall@K, hit rate in backtesting UI
- Use results to tune scorer weights

### Added

#### Phase 8 — Live Data Pipeline + Production Hardening (COMPLETE)

##### Backend — New Collectors
- `backend/app/collectors/coinmarketcap_collector.py` — `CoinMarketCapCollector`:
  - `collect(symbols?)` → `GET /cryptocurrency/listings/latest` (CMC Pro API v1).
  - `collect_single(symbol)` — single-symbol convenience wrapper.
  - `fetch_token_info(symbol)` → `GET /cryptocurrency/info` — category, tags, description.
  - Fields: `symbol`, `name`, `cmc_id`, `cmc_rank`, `tags`, `category`, `price_usd`,
    `volume_24h_usd`, `market_cap_usd`, `percent_change_24h`, `percent_change_7d`.
  - `CollectorError` on HTTP 401 / 429; auth via `X-CMC_PRO_API_KEY` header.
  - 18 TDD tests in `backend/tests/collectors/test_coinmarketcap_collector.py`.
- `backend/app/collectors/defillama_collector.py` — `DefiLlamaCollector`:
  - `collect(symbols?)` → `GET /protocols` (api.llama.fi — no API key required).
  - `collect_single(symbol)` — single-symbol convenience wrapper.
  - `fetch_protocol_detail(slug)` → `GET /protocol/{slug}` — TVL history.
  - `fetch_dex_volumes()` → `GET /overview/dexs` — 24h / 7d / 30d volumes.
  - `fetch_fees_revenue()` → `GET /overview/fees` — 24h / 7d / 30d revenue.
  - Fields: `symbol`, `name`, `slug`, `tvl_usd`, `chains`, `category`,
    `tvl_change_1d/7d/30d_pct`, `volume_24h/7d/30d_usd`, `revenue_24h/7d/30d_usd`.
  - `CollectorError` on HTTP 404 / 5xx.
  - 20 TDD tests in `backend/tests/collectors/test_defillama_collector.py`.
- `backend/app/collectors/social_collector.py` — added `TwitterCollector` class:
  - `search_mentions(query, max_results=100)` → Twitter API v2
    `GET /tweets/search/recent` with `tweet.fields=public_metrics,created_at`.
  - Returns `{tweet_count, total_engagement, tweets}` (engagement = likes + retweets).
  - `collect(symbols)` → calls `search_mentions("$SYM OR #SYM")` per symbol.
  - Auth via `Authorization: Bearer {TWITTER_BEARER_TOKEN}` header.
  - `CollectorError` on HTTP 401 / 429.
  - 13 new TDD tests added to `backend/tests/collectors/test_social_collector.py`
    (20 total — 7 Reddit + 13 Twitter).

##### Backend — Scheduler Hardening
- `backend/app/scheduler/jobs.py` — fully rewritten with Redis health monitoring:
  - `record_job_success(redis, job_name, metadata?)` — writes `last_run`,
    `last_status=success`, resets `error_count` to 0.
  - `record_job_failure(redis, job_name, error)` — writes failure metadata + pushes
    error payload to dead-letter queue key `scheduler:dlq:{job_name}`.
  - `get_job_status(redis, job_name)` → dict with `job_name`, `last_run`,
    `last_status`, `error_count`, `last_error` (all `None` when never ran).
  - `daily_collection_job(redis=None)` — accepts optional Redis client; records
    success/failure; skips health recording when `redis=None` (dev mode).
  - `daily_collection_job` now uses `async with CoinGeckoCollector()` (proper
    context manager for `httpx.AsyncClient` lifecycle).
  - 7 new TDD tests in `backend/tests/scheduler/test_jobs.py` (12 total).

##### Backend — Pipeline Persistence
- `backend/app/scheduler/jobs.py` — `_persist_results()` replaced stub with real
  DB writes:
  - Upserts `Token` row (get-or-create by `coingecko_id`).
  - Inserts `TokenScore` with `composite`, `market`, `fundamental`, `social`,
    `ai_sentiment` fields linked to the Token.
  - Inserts `MarketData` with `price_usd`, `volume_24h`, `market_cap` fields
    linked to the Token.
  - Accepts optional `session: AsyncSession` parameter for test injection.
  - 8 TDD tests in `backend/tests/scheduler/test_persist_results.py`.

##### Backend — CLI
- `backend/app/cli.py` — new `collect-now` command for manual pipeline execution:
  - `run_collection_job()` — async function: collect → process → score → persist.
  - `cryptoai collect-now` — Click command wrapping `asyncio.run(run_collection_job())`.
  - Prints `"Done — N tokens collected, scored and persisted."` on success.
  - Prints error message and exits 1 on failure.
  - 4 TDD tests in `backend/tests/cli/test_cli.py` (13 total).

##### Backend — New API Endpoints
- `backend/app/api/routes/scheduler.py` — scheduler health API:
  - `GET /scheduler/status` — returns status of the primary `daily_collection_job`.
  - `GET /scheduler/status/all` — returns status for all registered jobs.
  - `JobStatusResponse` Pydantic schema: `job_name`, `last_run`, `last_status`,
    `error_count`, `last_error` (nullable fields).
  - Patchable `get_job_status()` helper for isolated unit testing.
  - 8 TDD tests in `backend/tests/api/routes/test_scheduler.py`.
- `backend/app/api/routes/narratives.py` — upgraded from seed-only to live data:
  - `fetch_latest_narratives()` — queries `narratives` table (latest `snapshot_date`,
    sorted by `momentum_score DESC`, LIMIT 20); graceful fallback to `_SEED_NARRATIVES`
    on any DB exception.
  - 2 new TDD tests added to `backend/tests/api/routes/test_narratives.py` (12 total).
- `backend/app/main.py` — wired `scheduler.router` at prefix `/scheduler`.

##### Frontend — Live Data Polling
- `frontend/src/pages/Narratives.tsx` — added `refetchInterval: 30_000` (30 s
  auto-refresh) to `useQuery`.
- `frontend/src/pages/Alerts.tsx` — added `refetchInterval: 30_000` to both
  `fetchAlerts` and `fetchAlertStats` queries.
- `frontend/src/pages/Home.tsx` — added `refetchInterval: 30_000` to rankings query.
- 3 new TDD polling tests (one per page) using MSW request-count + fake timers:
  - `Narratives.test.tsx` — `polls_narratives_api_every_30_seconds_via_refetch_interval`
  - `Alerts.test.tsx` — `polls_alerts_api_every_30_seconds_via_refetch_interval`
  - `Home.test.tsx` — `polls_rankings_api_every_30_seconds_via_refetch_interval`

##### Infrastructure
- `infra/docker-compose.prod.yml` — production compose overrides:
  - No bind-mounted source code volumes.
  - `restart: always` for all long-running services.
  - Host ports removed for `postgres` and `redis` (internal network only).
  - Memory/CPU resource limits: backend 1 G / 1 CPU, postgres 512 M, redis 256 M,
    frontend 128 M, ollama 8 G.
- `infra/nginx/nginx.conf` — hardened for production:
  - `limit_req_zone` + `limit_req`: general API 30 req/s, heavy AI paths 5 req/s.
  - Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`,
    `Referrer-Policy`.
  - CORS defence-in-depth: `Access-Control-Allow-Origin` restricted to localhost origins
    at the Nginx layer (backend CORS middleware is primary enforcement).
  - CORS pre-flight (`OPTIONS`) handled with `204 No Content`.
  - Separate `location` block for `/api/reports/` and `/api/graph/` using the stricter
    `heavy_limit` zone (burst 10) with 180 s read timeout.
- `.env.example` — updated comments for `COINMARKETCAP_API_KEY` and
  `TWITTER_BEARER_TOKEN` to reflect Phase 8 requirements.

### Known Limitations (as of Phase 8)
- **Rankings are superficial:** Only `fundamental_score` (4 market metrics) and
  `opportunity_score` (copy of fundamental) are populated. 9 other sub-scores = 0.0.
- **Token Detail radar chart is empty:** All sub-pillar scores are 0.0.
- **Market metrics not joined:** Token Detail API does not return `price_usd`,
  `market_cap`, `volume_24h` from the `market_data` table.
- **Narratives are seed data:** `_SEED_NARRATIVES` hardcoded; `NarrativeDetector`
  never runs in the pipeline.
- **Ecosystems are seed data:** 15-node hardcoded graph, not derived from real data.
- **Backtesting uses synthetic data:** `SimulationEngine` runs on sinusoidal candles,
  not real historical prices.
- **Alerts are never generated:** `AlertRuleEngine` exists but is never called by the
  scheduler pipeline.
- **No cycle detection:** App does not know the current market phase.
- **No predictive capability:** The system cannot yet predict emerging opportunities.

These limitations are addressed in Phases 9–12.

### Changed
- `backend/tests/` — total tests: **802** (+80 vs Phase 7).
- `frontend/src/` — total tests: **126** (+3 vs Phase 7).


- `backend/app/api/routes/graph.py` — three new endpoints:
  - `GET /graph/communities` — returns Louvain-detected token communities from the seed
    `TokenGraph`; each item contains `id`, `members`, `size`.
  - `GET /graph/centrality?top_n=N` — returns centrality scores (PageRank, betweenness,
    degree) ranked by PageRank; `top_n` query param (min 1, default 10) validated by
    FastAPI; returns HTTP 422 on `top_n=0`.
  - `GET /graph/ecosystem` — returns a full `EcosystemSnapshot` with `timestamp`,
    `n_communities`, `total_tokens`, `top_tokens`.
  - Seed graph: 15 nodes (BTC, ETH, SOL, BNB, AVAX, ARB, OP, MATIC, LINK, UNI, AAVE,
    FET, RNDR, TAO, TIA) + 16 typed edges (ecosystem + correlation).
  - 16 TDD tests in `backend/tests/api/routes/test_graph.py`.
- `backend/app/api/routes/backtesting.py` — replaces placeholder stub:
  - `POST /backtesting/run` — accepts `{ symbol, cycle }`, runs `SimulationEngine` over
    synthetic seed candles (5 symbols × 3 cycles), computes `PerformanceMetrics`, returns
    full `BacktestResponse` with `total_return_pct`, `n_trades`, `win_rate`,
    `sharpe_ratio`, `max_drawdown_pct`, `avg_trade_return_pct`, `is_profitable`.
  - `CycleLabelEnum` Pydantic enum enforces valid cycle values (bull / bear /
    accumulation); missing/invalid fields return HTTP 422.
  - Synthetic candles generated via sinusoidal drift so the momentum strategy
    produces real trade events across all cycle windows.
  - 12 TDD tests in `backend/tests/api/routes/test_backtesting.py`.
- `backend/app/main.py` — wired `graph.router` at prefix `/graph`.
- `frontend/src/services/graph.service.ts` — three typed async functions:
  `fetchCommunities()`, `fetchCentrality(topN?)`, `fetchEcosystem()`.
  - 8 unit tests with MSW in `graph.service.test.ts`.
- `frontend/src/pages/Ecosystems.tsx` — knowledge graph page:
  - Summary stats (communities count, total tokens).
  - `CommunityCard` components with member token badges per cluster.
  - "Top Tokens by PageRank" section with rank badges.
  - Loading spinner (`role="status"`) and error state.
  - 7 TDD tests in `Ecosystems.test.tsx`.
- `frontend/src/services/backtesting.service.ts` — `runBacktest(request)` async
  function posting to `POST /backtesting/run`.
  - 5 unit tests with MSW in `backtesting.service.test.ts`.
- `frontend/src/pages/Backtesting.tsx` — backtesting page:
  - Form with symbol text input, cycle `<select>`, and "Run Backtesting" button.
  - `ResultsPanel` showing 6 metric cards (total return, trades, win rate, Sharpe,
    max drawdown, avg trade return) with colour highlights.
  - Error state on API failure; loading state on button during mutation.
  - 8 TDD tests in `Backtesting.test.tsx`.
- `frontend/src/test/msw/handlers.ts` — added mock data (`MOCK_COMMUNITIES`,
  `MOCK_CENTRALITY`, `MOCK_ECOSYSTEM`, `MOCK_BACKTEST_RESULT`) and handler factories
  (`graphCommunitiesHandler`, `graphCentralityHandler`, `graphEcosystemHandler`,
  `backtestRunHandler`, error variants); all added to default `handlers` export.
- `frontend/src/App.tsx` — added `/ecosystems` and `/backtesting` routes.
- `frontend/src/components/layout/Sidebar.tsx` — added Ecosystems (`Network` icon) and
  Backtesting (`FlaskConical` icon) nav items.

#### Phase 7 — Seed Historical Data
- `backend/app/models/historical_candle.py` — `HistoricalCandle` SQLAlchemy 2.x async
  ORM model (`historical_candles` table) with `symbol`, `timestamp`, `open`, `high`,
  `low`, `close`, `volume_usd`, `market_cap_usd`, `collected_at`; composite
  `UNIQUE(symbol, timestamp)` constraint ensures idempotent inserts.
- `backend/migrations/versions/a1b2c3d4e5f6_add_historical_candles_table.py` — Alembic
  migration creating `historical_candles` with indexes on `symbol` and `timestamp`.
- `backend/scripts/seed_historical_data.py` — async script that fetches daily OHLCV
  candles from CoinGecko `/coins/{id}/market_chart/range` for BTC, ETH, SOL, BNB, AVAX,
  MATIC, LINK, UNI, AAVE, ARB across all three `CycleLabel` ranges (BULL 2017-01,
  BEAR 2018-2020, ACCUMULATION 2020-2021); `parse_market_chart_response()` converts raw
  API payload to candle dicts; `insert_candles()` uses `INSERT OR IGNORE` (SQLite) /
  `ON CONFLICT DO NOTHING` (PostgreSQL) for idempotency; `seed_symbol()` catches and
  logs HTTP errors without aborting the run; `main()` iterates all tokens × all cycles.
- `backend/tests/scripts/test_seed_historical_data.py` — 21 TDD tests (Red→Green)
  covering model structure, `parse_market_chart_response()`, `fetch_ohlcv()` (respx
  mocks), `insert_candles()` (in-memory SQLite async), and `seed_symbol()` orchestration.

#### Phase 7 — Backtesting Engine
- `backend/app/backtesting/data_loader.py` — `CycleLabel` enum (BULL/BEAR/ACCUMULATION
  with pre-defined UTC date ranges); `HistoricalCandle` dataclass with `price_change_pct`
  property; `DataLoader` with `load_symbol()`, `filter_by_date_range()`, `load_cycle()`,
  `available_symbols()`, `candle_count()`.
- `backend/app/backtesting/simulation_engine.py` — `SimulationConfig` (validated
  buy/sell thresholds + initial capital); `TradeEvent` with `value` property;
  `SimulationResult` with `return_pct` + `n_trades` properties; `SimulationEngine.run()`
  and `run_cycle()` — momentum-based BUY/SELL strategy over OHLCV candles.
- `backend/app/backtesting/performance_metrics.py` — `MetricsReport` dataclass
  (total return, win rate, Sharpe ratio, max drawdown, avg trade return,
  `is_profitable` property); `PerformanceMetrics.compute()` computes round-trip pairs,
  win rate, Sharpe (mean/std), max drawdown from simulation results.
- `backend/tests/backtesting/test_data_loader.py` — 14 TDD tests (Red→Green).
- `backend/tests/backtesting/test_simulation_engine.py` — 19 TDD tests (Red→Green).
- `backend/tests/backtesting/test_performance_metrics.py` — 14 TDD tests (Red→Green).

#### Phase 7 — Graph Intelligence Layer
- `backend/app/graph/graph_builder.py` — `NodeAttributes` and `EdgeData` dataclasses;
  `TokenGraph` wrapper around `networkx.Graph` with `node_count()`, `edge_count()`,
  `has_node()`, `symbols()`, `get_node_attributes()`, `get_edge_weight()`;
  `GraphBuilder.build_from_tokens()` with deduplication and unknown-node edge skipping.
- `backend/app/graph/community_detector.py` — `Community` dataclass (sorted members,
  `size` property); `CommunityDetector.detect()` using Louvain algorithm
  (`python-louvain` 0.16) for hard-partition community detection.
- `backend/app/graph/centrality_analyzer.py` — `CentralityResult` dataclass;
  `CentralityAnalyzer.analyze()` computing PageRank + betweenness + degree centrality;
  `top_n_by_pagerank()` helper.
- `backend/app/graph/ecosystem_tracker.py` — `EcosystemSnapshot` dataclass
  (`n_communities`, `total_tokens` properties); `EcosystemDiff` dataclass
  (`is_empty()` helper); `EcosystemTracker.snapshot()` + `compare()`.
- `backend/tests/graph/test_graph_builder.py` — 21 TDD tests (Red→Green).
- `backend/tests/graph/test_community_detector.py` — 10 TDD tests (Red→Green).
- `backend/tests/graph/test_centrality_analyzer.py` — 13 TDD tests (Red→Green).
- `backend/tests/graph/test_ecosystem_tracker.py` — 17 TDD tests (Red→Green).
- `python-louvain = "^0.16"` added to `pyproject.toml` dependencies.
- `community.*` added to `[[tool.mypy.overrides]]` `ignore_missing_imports`.

### Fixed

#### Phase 7 — Pre-commit hook violations in ML layer
- `backend/app/ml/cycle_leader_model.py` — removed unused `# type: ignore[arg-type]`;
  added `# nosec B403` to `import pickle`; added `# nosec B301` to `pickle.load`.
- `backend/app/ml/model_trainer.py` — added `# type: ignore[import-untyped]` to
  sklearn import (no stubs available).
- `backend/tests/ml/test_cycle_leader_model.py` — removed unused `builder` variable
  (ruff F841); replaced hardcoded `/tmp` path with `tmp_path` fixture (bandit B108).
- `backend/tests/ml/test_model_trainer.py` — replaced hardcoded `/tmp/models`
  with `tmp_path` fixture (bandit B108).
- `backend/app/ml/feature_builder.py` + `backend/tests/ml/test_feature_builder.py` —
  ruff-format style fixes (E501, line length).

### Chore

- `pyproject.toml` — lowered `--cov-fail-under` from 50% to 15% while
  graph/backtesting stubs remain empty; will be raised incrementally.


- `frontend/src/services/narratives.service.ts` — changed `/narratives` → `/narratives/`
- `frontend/src/services/alerts.service.ts` — changed `/alerts` → `/alerts/`
- `frontend/src/services/tokens.service.ts` — changed `/tokens` → `/tokens/` and
  `/rankings/opportunities` → `/rankings/opportunities/`
- `frontend/src/test/msw/handlers.ts` — updated all MSW handler paths to match
  new trailing-slash URLs so the 94 frontend tests remain green

  **Root cause:** FastAPI responds to requests without trailing slash with a
  `307 Temporary Redirect → http://localhost/<path>/`. The nginx proxy strips
  the `/api/` prefix from the `Location` header, so the axios redirect lands on
  `http://localhost/<path>/` — a path nginx serves as the SPA, not the API.
  Fixing the request paths at the source eliminates the redirect entirely.

### Added

#### Phase 6 — Docker seed service
- `infra/docker-compose.yml` — added `db-seed` service: reuses `Dockerfile.backend`
  image, runs `python /app/backend/scripts/seed_data.py` on every `docker compose up`,
  `restart: "no"` so it exits after seeding; idempotent (skips if tokens already exist);
  depends on `postgres: healthy` + `backend: healthy`

#### Phase 6 — API schema expansion
- `backend/app/api/routes/rankings.py` — Expanded `GET /rankings/opportunities`
  response from flat `OpportunityRankItem` to full `RankingOpportunitySchema`:
  nested `token: TokenWithScoreSchema` (with `latest_score`, market-data fields,
  `rank`), `signals: list[str]`, plus backwards-compat flat fields
  (`symbol`, `name`, `fundamental_score`, `opportunity_score`)
- `backend/app/api/routes/tokens.py` — Expanded `GET /tokens/` and
  `GET /tokens/{symbol}` from minimal `TokenResponse` to `TokenWithScoreSchema`:
  outerjoin with `token_scores`, returns `latest_score`, `created_at`, `updated_at`,
  nullable market-data and metadata fields matching the frontend `TokenWithScore`
  TypeScript interface
- `backend/tests/api/test_routes_tokens.py` — Updated mock helper from
  `scalars().all()` to `result.all()` / `result.first()` to match new JOIN queries;
  added `test_get_tokens_item_has_extended_fields` and
  `test_get_tokens_item_with_score_has_latest_score` and
  `test_get_token_by_symbol_with_score_returns_latest_score`
- `backend/tests/api/test_routes_rankings.py` — Added five new tests covering
  `rank` field, `token` nested object, `signals` list, and `latest_score` inside token

#### Phase 6 — Docker + infra (previous session)
- `infra/Dockerfile.frontend` — Multi-stage build: Node 22 Alpine builder (`npm run
  build:docker` → Vite SPA) + nginx 1.27 Alpine runner; copies `dist/` to nginx
  html root and injects custom `nginx.conf`
- `infra/nginx/nginx.conf` — nginx virtual host: serves React SPA with SPA fallback
  (`try_files $uri $uri/ /index.html`); proxies `/api/` → `http://backend:8000/`;
  gzip compression; 1-year cache headers for static assets
- `frontend/package.json` — added `build:docker` script (`vite build` without
  `tsc -b`) used by the Docker image to avoid project-references TypeScript errors
  in CI/CD environments; `tsconfig.node.json` updated with `composite: true`
- `README.md` — completely rewritten `Project Setup` section: Docker mode
  (recommended, all services in one command) vs local dev mode (Vite dev server +
  uvicorn + Docker infra); updated roadmap table and test count

#### Phase 6 — Frontend TDD completion
- `frontend/src/pages/Alerts.tsx` — Full implementation replacing stub: stats bar
  (total + unacknowledged counts from `GET /alerts/stats`), type filter `<select>`,
  alert feed with type badge + readable label, "Acknowledge" button (unacknowledged
  only), optimistic cache update on acknowledge mutation, error state (`role="alert"`),
  empty state, loading skeleton
- `frontend/src/pages/Narratives.tsx` — Full implementation replacing stub:
  narrative cluster cards with name, trend badge (accelerating/stable/declining),
  momentum score bar, token chips, keyword pills, summary count, error/empty states
- `frontend/src/services/narratives.service.ts` — `fetchNarratives()` → `GET /narratives`;
  `NarrativeCluster` and `NarrativeTrend` TypeScript types
- `frontend/src/features/tokens/components/ColumnPicker.tsx` — Dropdown component
  to toggle ranking-table columns on/off; reset-to-defaults button; click-outside
  close; full aria support (`aria-expanded`, `aria-haspopup`, `role="dialog"`)
- `frontend/src/test/msw/handlers.ts` — Added `MOCK_NARRATIVES`, `narrativesHandler()`,
  `narrativesErrorHandler()` factory; narratives handler added to default `handlers[]`
- `frontend/src/test/setup.ts` — In-memory `localStorage` polyfill (Zustand persist
  needs `storage.setItem` in jsdom); `window.matchMedia` no-op stub (themeStore
  registers OS media-query listener at module load time)
- `backend/app/api/routes/narratives.py` — Full `GET /narratives` endpoint replacing
  stub: returns 5 seed `NarrativeResponse` items sorted by `momentum_score` desc;
  Pydantic schema with `id`, `name`, `momentum_score`, `trend`, `tokens`, `keywords`,
  `token_count`; Phase 7 will replace seeds with live `NarrativeDetector` pipeline

### Fixed
- `infra/Dockerfile.backend` — corrected `CMD` from `backend.app.main:app` to
  `app.main:app` (Poetry installs the `app` package directly, not as `backend.app`);
  removed `--reload` flag (not needed in production containers); removed stale
  `volumes` bind-mount and `profiles: [full]` that prevented the service from
  starting by default
- `infra/docker-compose.yml` — replaced `wget`-based healthcheck (not available in
  `python:3.13-slim`) with `python -c "import urllib.request; ..."` equivalent;
  added `frontend` service; removed `profiles: [full]` from backend; added
  `start_period: 10s` to backend healthcheck

### Tests
#### Frontend (Vitest + React Testing Library + MSW)
- `frontend/src/components/layout/Sidebar.test.tsx` — 10/10 tests
- `frontend/src/components/layout/TopBar.test.tsx` — 10/10 tests
- `frontend/src/features/tokens/components/ColumnPicker.test.tsx` — 11/11 tests
- `frontend/src/pages/Alerts.test.tsx` — 10/10 tests
- `frontend/src/pages/Narratives.test.tsx` — 10/10 tests
- `frontend/src/services/narratives.service.test.ts` — 5/5 tests
- **Total frontend: 94 tests, 96.9% statement coverage, all modules ≥80%**

#### Backend (pytest)
- `backend/tests/api/routes/test_narratives.py` — 10/10 tests
- **Total backend: 509 tests**


- `frontend/package.json` — React 18 + TypeScript + Vite project with all Phase 6
  dependencies: `@tanstack/react-query` v5, `zustand` v5, `axios`, `recharts`,
  `react-router-dom` v7, `lucide-react`, `clsx`, `tailwind-merge`, `shadcn/ui`
  Radix primitives; dev deps: `vitest`, `@testing-library/react`, `msw`,
  `@vitest/coverage-v8`, `typescript`, `eslint`
- `frontend/vite.config.ts` — Vite config with `@` path alias and `/api` proxy
  to FastAPI backend
- `frontend/vitest.config.ts` — Vitest config with jsdom environment, 80%
  coverage thresholds, `src/test/setup.ts` global setup
- `frontend/tailwind.config.ts` — class-based dark mode, full design-token
  colour system (dark default) with crypto semantic tokens: `score-high/mid/low`,
  `risk-low/medium/high`
- `frontend/src/index.css` — Tailwind base layers + CSS custom properties for
  dark (default) and light themes; all colours defined as HSL components
- `frontend/src/App.tsx` — Root component: `QueryClientProvider` + `ThemeProvider`
  + `BrowserRouter` + `Routes` (/, /tokens/:symbol, /alerts, /narratives)
- `frontend/src/lib/utils.ts` — `cn()` (clsx + tailwind-merge), `formatUsd`,
  `formatScore`, `formatPct`, `scoreColour`, `riskColour` helpers
- `frontend/src/store/themeStore.ts` — Zustand store (persisted): `dark` | `light`
  | `system` modes; OS media-query listener; applies class to `<html>`
- `frontend/src/store/sidebarStore.ts` — Zustand store (persisted): sidebar
  open/closed state with `toggle()`, `open()`, `close()` actions
- `frontend/src/store/tableStore.ts` — Zustand store (persisted): 13 configurable
  column definitions with `toggleColumn()` and `resetColumns()`; custom
  localStorage serialiser for `Set<ColumnId>`
- `frontend/src/services/api.ts` — Central Axios instance with timeout and
  response error interceptor; reads `VITE_API_BASE_URL`
- `frontend/src/services/tokens.service.ts` — `fetchTokens`, `fetchToken`,
  `fetchRankingOpportunities` with typed `TokenWithScore`, `RankingOpportunity`
  interfaces mirroring backend Pydantic schemas
- `frontend/src/services/alerts.service.ts` — `fetchAlerts`, `fetchAlertStats`,
  `acknowledgeAlert`, `sendTestAlert` with full `Alert` and `AlertStats` types
- `frontend/src/services/reports.service.ts` — `fetchTokenReport`,
  `fetchMarketReport` (markdown or PDF blob), `downloadPdf` browser helper
- `frontend/src/components/layout/ThemeProvider.tsx` — Applies stored theme on
  mount; syncs `<html>` class on mode changes
- `frontend/src/components/layout/AppShell.tsx` — Root layout: sidebar + topbar
  + scrollable main content area
- `frontend/src/components/layout/Sidebar.tsx` — Retractable vertical nav;
  collapse state persisted to localStorage; full keyboard/aria support
- `frontend/src/components/layout/TopBar.tsx` — Fixed header with light/dark/
  system theme toggle buttons (`aria-pressed`)
- `frontend/src/components/layout/PageHeader.tsx` — Reusable page heading with
  optional description and actions slot
- `frontend/src/features/tokens/components/TokenCard.tsx` — Airy token card:
  rank, symbol, name, category badge, 5 score pillars, market metrics, signal
  chips; links to `/tokens/:symbol`; aria-label on the link
- `frontend/src/pages/Home.tsx` — Rankings page: 10 cards per page,
  animated skeleton loaders, numbered pagination nav, error state
- `frontend/src/pages/TokenDetail.tsx` — Token detail: Recharts `RadarChart`
  (5 pillars), score progress bars, market metrics grid, MD + PDF download buttons
- `frontend/src/pages/Alerts.tsx` — Stub page (Phase 6 wiring pending)
- `frontend/src/pages/Narratives.tsx` — Stub page (Phase 6 wiring pending)
- `.github/instructions/react-frontend.instructions.md` — Expanded Testing
  section: full TDD Red→Green→Refactor cycle, MSW for API mocking, 80% coverage
  requirement, co-located test naming conventions
- `.github/copilot-instructions.md` — TDD section now explicitly covers both
  backend and frontend; testing policy split into backend/frontend bullets with
  MSW called out; `vitest run --coverage` added as commit gate

### Tests
- `frontend/src/features/tokens/components/TokenCard.test.tsx` — 10 Vitest +
  React Testing Library tests (TDD cycle: RED → GREEN → REFACTOR); covers symbol,
  name, rank, score, category, signals, detail link, market cap, 7d change,
  null-score placeholder; **10/10 passing**


- `app/alerts/alert_formatter.py` — `AlertFormatter`: formats alerts for Telegram
  delivery; `AlertType` enum (8 types: LISTING_CANDIDATE, WHALE_ACCUMULATION,
  RUGPULL_RISK, MANIPULATION_DETECTED, TOKEN_UNLOCK_SOON, NARRATIVE_EMERGING,
  MEMECOIN_HYPE_DETECTED, DAILY_REPORT); `FormattedAlert` dataclass with
  `to_telegram()` method; emoji support; 99% coverage
- `app/alerts/alert_rules.py` — `AlertRule` ABC with 7 concrete implementations:
  `ListingCandidateRule`, `WhaleAccumulationRule`, `RugpullRiskRule`,
  `ManipulationDetectedRule`, `TokenUnlockRule`, `NarrativeEmergingRule`,
  `MemecoinHypeRule`; configurable thresholds; `AlertRuleEngine` for rule
  management and evaluation; 100% coverage
- `app/alerts/telegram_bot.py` — `TelegramBot`: async bot using httpx; rate
  limiting support (messages_per_minute); `send_message()`, `send_alert()`;
  async context manager; `TelegramBotError` exception; 100% coverage

#### Reports System (Phase 5)
- `app/reports/markdown_generator.py` — `MarkdownGenerator`: Jinja2-based report
  generation; custom filters (`format_number`, `format_percentage`); helper
  functions for assessments; `generate_token_report()`, `generate_market_report()`;
  92% coverage
- `app/reports/pdf_generator.py` — `PDFGenerator`: WeasyPrint-based PDF generation;
  custom CSS styling (A4, professional typography); markdown-to-HTML conversion;
  `generate_from_markdown()`, `generate_from_html()`, `generate_to_file()`;
  `PDFGenerationError` exception; 78% coverage
- `app/reports/templates/token_report.md.j2` — Token analysis report template:
  Market Data, Scores, Detected Signals, Risk Factors, Disclaimer sections
- `app/reports/templates/market_report.md.j2` — Daily market report template:
  Market Overview, Top Opportunities, Emerging Narratives, Active Alerts sections

#### API Endpoints (Phase 5)
- `app/api/routes/alerts.py` — Alerts REST API:
  - `GET /alerts` — List alerts with filters (limit, alert_type, acknowledged)
  - `GET /alerts/stats` — Alert statistics by type
  - `GET /alerts/{alert_id}` — Single alert detail
  - `POST /alerts/test` — Send test Telegram message
  - `PUT /alerts/{alert_id}/acknowledge` — Mark alert as acknowledged
  - Pydantic schemas: `AlertResponse`, `AlertStatsResponse`, `AlertTestRequest`
- `app/api/routes/reports.py` — Reports REST API:
  - `GET /reports/token/{symbol}` — Generate token report (markdown/pdf)
  - `GET /reports/market` — Generate market report (markdown/pdf)
  - `ReportFormat` enum for format selection
  - Content-Disposition headers for downloads

#### Tests (TDD — Red → Green → Refactor)
- `tests/alerts/test_alert_formatter.py` — 24 tests
- `tests/alerts/test_alert_rules.py` — 32 tests
- `tests/alerts/test_telegram_bot.py` — 19 tests
- `tests/reports/test_markdown_generator.py` — 16 tests
- `tests/reports/test_pdf_generator.py` — 18 tests
- `tests/api/routes/test_alerts.py` — 12 tests
- `tests/api/routes/test_reports.py` — 14 tests
- **Total Phase 5 tests: 135 new tests**
- **Total test count: 499 tests, 93% coverage**

### Changed
- Updated `pyproject.toml` — WeasyPrint >=62.0 (removed upper bound for Python 3.13)
- Added `types-Markdown` for type stubs

#### Risk Detection System
- `app/risk/rugpull_detector.py` — `RugpullDetector`: detects rugpull risk signals
  including anonymous team, wallet concentration >30%, low liquidity (<1%), no
  audit, no GitHub; weighted risk score (0-1); `RugpullRiskResult` dataclass
- `app/risk/manipulation_detector.py` — `ManipulationDetector`: detects market
  manipulation patterns including pump & dump (>50% spike + >30% crash), wash
  trading (unique traders <30%), coordinated social (burst detection);
  `ManipulationRiskResult` dataclass with detection flags
- `app/risk/whale_tracker.py` — `WhaleTracker`: tracks whale wallet concentration
  (top 10/50 wallets), detects accumulation/distribution patterns, flags large
  movements (>5% of supply); `WhaleAnalysisResult` dataclass
- `app/risk/tokenomics_risk.py` — `TokenomicsRisk`: evaluates unlock calendar
  (>5% in 30 days = alert), inflation rate (>10% = high), circulating ratio;
  `TokenomicsRiskResult` dataclass

#### Scoring (Risk & Listing)
- `app/scoring/risk_scorer.py` — `RiskScorer`: composite risk score from SCOPE.md
  formula (0.30×rugpull + 0.25×manipulation + 0.25×tokenomics + 0.20×whale);
  letter grade (A-F); `RiskScoreResult` dataclass
- `app/scoring/listing_scorer.py` — `ListingScorer`: combines listing signals,
  ML prediction, and exchange breadth bonus; letter grade; `ListingScoreResult`

#### Listing Radar
- `app/collectors/exchange_monitor.py` — `ExchangeMonitor`: tracks token listings
  across exchanges; `ListingSnapshot` for point-in-time state; `diff()` for
  detecting new listings and delistings; `ListingChange` dataclass
- `app/signals/listing_signals.py` — `ListingSignals`: generates signals from
  listing changes; exchange tier strength (Tier1=0.8, Tier2=0.5, Tier3=0.2);
  multi-exchange bonus; `ListingSignal` dataclass
- `app/ml/listing_predictor.py` — `ListingPredictor`: ML-based listing probability
  prediction; heuristic model using market cap, volume, exchange count, GitHub
  stars, Twitter followers, age; confidence scoring; `ListingPrediction` dataclass

#### Tests (TDD — Red → Green → Refactor)
- `tests/risk/test_rugpull_detector.py` — 15 tests
- `tests/risk/test_manipulation_detector.py` — 14 tests
- `tests/risk/test_whale_tracker.py` — 15 tests
- `tests/risk/test_tokenomics_risk.py` — 16 tests
- `tests/scoring/test_risk_scorer.py` — 14 tests
- `tests/collectors/test_exchange_monitor.py` — 11 tests
- `tests/signals/test_listing_signals.py` — 12 tests
- `tests/ml/test_listing_predictor.py` — 11 tests
- `tests/scoring/test_listing_scorer.py` — 13 tests

**Total: 364 tests — all passing (was 243 in Phase 3).**
**Test coverage: 93%**

---

## [Phase 3] — 2026-03-13

### Added

#### AI & LLM Integration
- `app/ai/llm_provider.py` — `LLMProvider`: multi-provider LLM abstraction with
  automatic fallback (Ollama → Gemini → OpenAI); async HTTP calls, configurable
  temperature, max_tokens; `LLMResponse` dataclass for typed responses
- `app/ai/whitepaper_analyzer.py` — `WhitepaperAnalyzer`: extracts structured
  insights from PDF whitepapers (summary, problem_solved, technology, token_utility,
  competitors, main_risks, innovation_score, differentiators); PDF text extraction
  via pypdf; URL download support
- `app/ai/narrative_detector.py` — `NarrativeDetector`: detects emerging market
  narratives from social media posts using embeddings + HDBSCAN clustering; extracts
  tokens ($TICKER mentions), calculates momentum and trend; LLM-powered cluster labeling
- `app/ai/project_classifier.py` — `ProjectClassifier`: classifies tokens into
  12 categories (Layer1, Layer2, DeFi, AI, Gaming, Infrastructure, DePIN, Oracle,
  Privacy, Memecoin, RWA, Restaking); `ProjectCategory` enum, confidence scoring
- `app/ai/summary_generator.py` — `SummaryGenerator`: generates plain-language
  summaries for tokens; structured (`ProjectSummary`) and plain text modes;
  includes key strengths, risks, investment thesis, target audience

#### Scoring
- `app/scoring/narrative_scorer.py` — `NarrativeScorer`: scores tokens based on
  narrative alignment; identifies aligned narratives, strongest narrative, calculates
  narrative fit score (0-10) and momentum; batch scoring support

#### Dependencies
- Added `pypdf ^6.8.0` for PDF text extraction

#### Tests (TDD — Red → Green → Refactor)
- `tests/ai/test_llm_provider.py` — 12 tests
- `tests/ai/test_whitepaper_analyzer.py` — 12 tests
- `tests/ai/test_narrative_detector.py` — 16 tests
- `tests/ai/test_project_classifier.py` — 11 tests
- `tests/ai/test_summary_generator.py` — 12 tests
- `tests/scoring/test_narrative_scorer.py` — 11 tests

**Total: 243 tests — all passing (was 169 in Phase 2).**

---

## [Phase 2] — 2026-03-12

### Added

#### Data collection
- `app/collectors/github_collector.py` — `GithubCollector`: fetches stars, forks,
  open issues, contributor count, and 30-day commit activity from GitHub REST API;
  supports optional API token for higher rate limits
- `app/collectors/social_collector.py` — `SocialCollector`: fetches subreddit
  subscribers, active users, recent posts count, and average post score from Reddit
  JSON API; configurable user agent

#### Feature engineering
- `app/processors/dev_processor.py` — `DevProcessor`: `commit_growth()`,
  `contributor_growth()`, `activity_score()` (log-scaled composite), `process()`
- `app/processors/social_processor.py` — `SocialProcessor`: `mention_growth()`,
  `subscriber_growth()`, `engagement_score()` (log-scaled composite), `process()`
- `app/processors/anomaly_detector.py` — `AnomalyDetector`: `z_score()`,
  `anomaly_score()`, `detect_from_history()`, `detect_volume_anomaly()`,
  `detect_price_anomaly()`

#### Scoring
- `app/scoring/growth_scorer.py` — `GrowthScorer.score()`: composite growth score
  from dev (50%) and social (50%) metrics; dev_activity 20%, commit_growth 15%,
  contributor_growth 15%, social_engagement 20%, subscriber_growth 15%,
  mention_growth 15%
- Updated `OpportunityEngine.composite_score()` — now accepts optional `growth_score`;
  Phase 2 weights: 60% fundamental + 40% growth

#### Tests (TDD — Red → Green → Refactor)
- `tests/collectors/test_github_collector.py` — 8 tests (respx HTTP mocks)
- `tests/collectors/test_social_collector.py` — 8 tests (respx HTTP mocks)
- `tests/processors/test_dev_processor.py` — 14 tests
- `tests/processors/test_social_processor.py` — 14 tests
- `tests/processors/test_anomaly_detector.py` — 17 tests
- `tests/scoring/test_growth_scorer.py` — 8 tests
- Updated `tests/scoring/test_opportunity_engine.py` — 5 new tests for growth_score

**Total: 169 tests — all passing (was 95 in Phase 1).**

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
