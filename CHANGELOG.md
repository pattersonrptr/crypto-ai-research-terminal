# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

### Added

#### Alerts System (Phase 5)
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
