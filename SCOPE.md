# 🧠 Crypto AI Research Terminal — Full Technical Scope

> **Specification document for use with GitHub Copilot + Claude Sonnet 4.6**
> Version: 1.0 | Status: Draft | Investor profile: Long-term, BTC-cycle-focused

---

## 📌 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Goals and Requirements](#2-goals-and-requirements)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Directory Structure](#5-directory-structure)
6. [Modules — Detailed](#6-modules---detailed)
   - 6.1 Data Collectors
   - 6.2 Data Storage Layer
   - 6.3 Feature Engineering
   - 6.4 Signal Generation Engine
   - 6.5 AI Analysis Engine
   - 6.6 Graph Intelligence Layer
   - 6.7 Machine Learning Layer
   - 6.8 Scoring & Opportunity Engine
   - 6.9 Risk Detection Engine
   - 6.10 Alert Engine
   - 6.11 Backtesting Engine
   - 6.12 Report Generator
   - 6.13 Dashboard (React frontend)
   - 6.14 CLI
7. [Database — Schema](#7-database---schema)
8. [External Integrations & APIs](#8-external-integrations--apis)
9. [Scoring System — Details](#9-scoring-system---details)
10. [Development Roadmap](#10-development-roadmap)
11. [Configuration & Environment Variables](#11-configuration--environment-variables)
12. [Docker & Infrastructure](#12-docker--infrastructure)
13. [Example Outputs](#13-example-outputs)
14. [Design Decisions & Rationale](#14-design-decisions--rationale)

---

## 1. Project Overview

### What it is

The **Crypto AI Research Terminal** is a personal market intelligence platform for cryptocurrencies, AI-powered, that automates:

- Fundamental analysis of altcoins (Top 300 by default, configurable)
- Detection of emerging market narratives
- Radar for potential listings on tier-1 exchanges
- Detection of whale accumulation and institutional activity
- Identification of projects with explosive growth potential ("next Solana")
- Alerts about risks (rugpulls, manipulation, time-bomb tokens)
- Backtesting the model against historical cycles (2017, 2020–2021)


### What it is NOT

- An automated trading bot
- A price forecasting system
- A day-trading or scalping tool


### System philosophy

> The AI does not decide. It researches, organizes, scores and explains. The final decision is always the user’s.

The system behaves as a personal quantitative analyst, lowering the cognitive cost of researching hundreds of projects, filtering noise, and highlighting signals.

---

## 2. Goals and Requirements

### Main Goals

| # | Goal |
|---|------|
| 1 | Automatically analyze crypto fundamentals (technology, tokenomics, team, adoption) |
| 2 | Detect emerging market narratives before mainstream awareness |
| 3 | Estimate probability of listing on tier-1 exchanges |
| 4 | Identify projects with explosive growth potential ("10x candidates") |
| 5 | Detect risks: rugpull, token dumps, market manipulation |
| 6 | Monitor Bitcoin cycle and estimate altseason phases |
| 7 | Allow backtesting of the model on past cycles |
| 8 | Generate clear reports (MD/PDF) and alerts via Telegram |


### Functional Requirements

- Analyze Top 300 cryptocurrencies by default (configurable via `.env`)
- Collect data at multiple frequencies: realtime, daily, weekly, monthly
- Support multiple AI providers: **Ollama** (local/free), **Gemini** (free tier), **OpenAI** (optional, paid)
- Expose a React web dashboard with ranking and detail pages
- Expose a CLI for quick terminal access
- Send important alerts through Telegram
- Export reports in Markdown and PDF
- Run fully in **Docker** on a local PC


### Non-Functional Requirements

- Modular architecture: each module can be developed and tested independently
- Well-documented code in Portuguese and English (docstrings in English, comments in Portuguese where needed)
- Centralized configuration in `.env`
- Structured logging across all services
- Fault tolerance: if an API fails, system continues using cached data

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  CoinGecko │ CoinMarketCap │ DefiLlama │ GitHub │ X │ Reddit   │
│            Binance │ Coinbase │ KuCoin │ OKX │ Bybit │ Kraken  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  DATA COLLECTORS │  (collectors/)
                    │  market_collector│
                    │  social_collector│
                    │  github_collector│
                    │  exchange_monitor│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  DATA STORAGE   │  (PostgreSQL)
                    │  tokens         │
                    │  market_data    │
                    │  social_data    │
                    │  dev_activity   │
                    │  signals        │
                    └────────┬────────┘
                             │
                    ┌────────▼──────────────┐
                    │  FEATURE ENGINEERING  │  (processors/)
                    │  growth metrics       │
                    │  anomaly detection    │
                    │  normalization        │
                    └────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌─────▼──────┐ ┌────▼────────────┐
     │ SIGNAL ENGINE │ │ AI ENGINE  │ │ GRAPH LAYER     │
     │ growth signals│ │ LLM analysis│ │ knowledge graph │
     │ market signals│ │ narratives │ │ community detect│
     │ listing signals│ │ whitepaper │ │ centrality      │
     └────────┬──────┘ └─────┬──────┘ └────┬────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼──────────────┐
                    │    SCORING ENGINE     │  (scoring/)
                    │  OpportunityScore     │
                    │  RiskScore            │
                    │  ListingProbability   │
                    │  CycleLeaderScore     │
                    └────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌─────▼──────┐ ┌────▼────────────┐
     │  ALERT ENGINE │ │  BACKTESTING│ │ REPORT GENERATOR│
     │  Telegram     │ │  Engine     │ │ Markdown / PDF  │
     └───────────────┘ └─────────────┘ └────┬────────────┘
                                            │
                                   ┌────────▼────────┐
                                   │   INTERFACES    │
                                   │  Dashboard React│
                                   │  CLI            │
                                   └─────────────────┘
```

---

## 4. Technology Stack

### Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11+ | Unmatched data/AI ecosystem |
| API Framework | FastAPI | Async, modern, auto-documented |
| Task Scheduler | APScheduler | Lightweight, avoids Celery overhead for personal use |
| ORM | SQLAlchemy 2.x | Mature, async support |
| Migrations | Alembic | Standard with SQLAlchemy |


### Database

| Component | Technology |
|-----------|-----------|
| Primary | PostgreSQL 15 |
| Cache / Queues | Redis |
| Graph (future) | NetworkX (in-memory), migrate to Neo4j when needed |


### AI / ML

| Component | Technology | When to use |
|-----------|-----------|-------------|
| Main LLM | Ollama (llama3, mistral) | No cost, local |
| Secondary LLM | Google Gemini API | Free tier, more powerful |
| Tertiary LLM | OpenAI GPT-4o | Optional, paid |
| Embeddings | sentence-transformers | Narrative detection, similarity |
| Classical ML | scikit-learn, XGBoost | Scoring, classification, backtesting |
| LLM orchestration | LangChain | Chains for complex analysis |
| Graph | NetworkX | Knowledge graph, community detection |


### Frontend

| Component | Technology |
|-----------|-----------|
| Framework | React 18 + TypeScript |
| Build | Vite |
| UI Components | shadcn/ui + TailwindCSS |
| Charts | Recharts |
| Graph visualization | React Flow or D3.js |
| State | Zustand |
| HTTP Client | Axios + React Query |


### Infra

| Component | Technology |
|-----------|-----------|
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx (optional, advanced phase) |
| Logs | structlog (Python) |

---

## 5. Directory Structure

```
crypto-ai-terminal/
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Centralized configuration
│   │   ├── dependencies.py            # FastAPI dependency injection
│   │   │
│   │   ├── api/                       # REST API routes
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── tokens.py          # GET /tokens, /tokens/{symbol}
│   │   │   │   ├── rankings.py        # GET /rankings/opportunities
│   │   │   │   ├── narratives.py      # GET /narratives/trending
│   │   │   │   ├── alerts.py          # GET /alerts
│   │   │   │   ├── reports.py         # POST /reports/generate
│   │   │   │   └── backtesting.py     # POST /backtesting/run
│   │   │
│   │   ├── collectors/                # External data collection
│   │   │   ├── __init__.py
│   │   │   ├── base_collector.py      # Base class with retry, rate limit
│   │   │   ├── coingecko_collector.py
│   │   │   ├── coinmarketcap_collector.py
│   │   │   ├── defillama_collector.py
│   │   │   ├── github_collector.py
│   │   │   ├── social_collector.py    # X (Twitter) + Reddit
│   │   │   └── exchange_monitor.py    # Listing monitoring
│   │   │
│   │   ├── processors/                # Feature engineering
│   │   │   ├── __init__.py
│   │   │   ├── market_processor.py    # Market metrics
│   │   │   ├── social_processor.py    # Social metrics
│   │   │   ├── dev_processor.py       # Dev activity metrics
│   │   │   ├── anomaly_detector.py    # Statistical anomaly detection
│   │   │   └── normalizer.py          # Data normalization
│   │   │
│   │   ├── signals/                   # Signal generation
│   │   │   ├── __init__.py
│   │   │   ├── growth_signals.py      # Growth signals
│   │   │   ├── market_signals.py      # Market signals
│   │   │   ├── listing_signals.py     # Listing signals
│   │   │   ├── whale_signals.py       # Whale activity signals
│   │   │   └── narrative_signals.py   # Narrative signals
│   │   │
│   │   ├── ai/                        # AI engine
│   │   │   ├── __init__.py
│   │   │   ├── llm_provider.py        # Abstraction: Ollama / Gemini / OpenAI
│   │   │   ├── whitepaper_analyzer.py # Whitepaper analysis
│   │   │   ├── narrative_detector.py  # Narrative detection via embeddings
│   │   │   ├── project_classifier.py  # Project category classification
│   │   │   └── summary_generator.py   # Plain-language summary generation
│   │   │
│   │   ├── graph/                     # Knowledge Graph
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py       # Graph construction
│   │   │   ├── community_detector.py  # Cluster/ecosystem detection
│   │   │   ├── centrality_analyzer.py # PageRank, betweenness
│   │   │   └── ecosystem_tracker.py   # Tracking emerging ecosystems
│   │   │
│   │   ├── ml/                        # Machine Learning
│   │   │   ├── __init__.py
│   │   │   ├── feature_builder.py     # Feature vector construction
│   │   │   ├── cycle_leader_model.py  # "next Solana" model
│   │   │   ├── listing_predictor.py   # Listing probability model
│   │   │   └── model_trainer.py       # Training and evaluation
│   │   │
│   │   ├── scoring/                   # Scoring engine
│   │   │   ├── __init__.py
│   │   │   ├── fundamental_scorer.py  # Fundamental scorer (5 VC pillars)
│   │   │   ├── growth_scorer.py       # Growth scorer
│   │   │   ├── narrative_scorer.py    # Narrative scorer
│   │   │   ├── risk_scorer.py         # Risk scorer
│   │   │   ├── listing_scorer.py      # Listing probability scorer
│   │   │   └── opportunity_engine.py  # Final composed score
│   │   │
│   │   ├── risk/                      # Risk detection
│   │   │   ├── __init__.py
│   │   │   ├── rugpull_detector.py
│   │   │   ├── manipulation_detector.py
│   │   │   ├── whale_tracker.py
│   │   │   └── tokenomics_risk.py     # Unlock calendar, inflation
│   │   │
│   │   ├── alerts/                    # Alerts system
│   │   │   ├── __init__.py
│   │   │   ├── telegram_bot.py
│   │   │   ├── alert_rules.py         # Trigger rules
│   │   │   └── alert_formatter.py     # Message formatting
│   │   │
│   │   ├── reports/                   # Report generation
│   │   │   ├── __init__.py
│   │   │   ├── markdown_generator.py
│   │   │   ├── pdf_generator.py
│   │   │   └── templates/
│   │   │       ├── token_report.md.j2
│   │   │       └── market_report.md.j2
│   │   │
│   │   ├── backtesting/               # Backtesting Engine
│   │   │   ├── __init__.py
│   │   │   ├── data_loader.py         # Loads historical data
│   │   │   ├── simulation_engine.py   # Simulates the model on past cycles
│   │   │   └── performance_metrics.py # Precision, recall, hits
│   │   │
│   │   ├── scheduler/                 # Job scheduling
│   │   │   ├── __init__.py
│   │   │   └── jobs.py                # Periodic job definitions
│   │   │
│   │   └── models/                    # SQLAlchemy models
│   │       ├── __init__.py
│   │       ├── token.py
│   │       ├── market_data.py
│   │       ├── social_data.py
│   │       ├── dev_activity.py
│   │       ├── signal.py
│   │       ├── score.py
│   │       └── alert.py
│   │
│   ├── migrations/                    # Alembic migrations
│   ├── tests/                         # Unit & integration tests
│   ├── cli.py                         # CLI entrypoint
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── TokenCard/
│   │   │   ├── TokenDetail/
│   │   │   ├── NarrativeRadar/
│   │   │   ├── EcosystemGraph/
│   │   │   └── AlertFeed/
│   │   ├── pages/
│   │   │   ├── Home.tsx               # Main ranking
│   │   │   ├── TokenDetail.tsx        # Token detail page
│   │   │   ├── Narratives.tsx         # Emerging narratives
│   │   │   ├── Ecosystems.tsx         # Knowledge Graph visual
│   │   │   ├── Backtesting.tsx        # Backtesting UI
│   │   │   └── Alerts.tsx             # Alerts history
│   │   ├── hooks/
│   │   ├── services/                  # API calls
│   │   ├── store/                     # Zustand state
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── nginx/
│       └── nginx.conf
│
├── scripts/
│   ├── seed_historical_data.py        # Populate DB with historical data
│   ├── import_whitepaper.py           # Import and analyze whitepaper
│   └── run_backtest.py                # Quick backtesting script
│
├── data/
│   └── historical/                    # CSVs for backtesting
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 6. Modules — Detailed

### 6.1 Data Collectors

**Responsibility:** Collect data from external sources and persist to the database.

#### `base_collector.py`

Base class that all collectors inherit from. Implements:
- Automatic retries with exponential backoff
- Rate limiting honoring API limits
- Structured logging
- Abstract `collect()` method

```python
# Example of expected interface
class BaseCollector:
    async def collect(self, symbols: list[str]) -> list[dict]: ...
    async def collect_single(self, symbol: str) -> dict: ...
```

#### `coingecko_collector.py`

**Data collected:**
- Price, market cap, 24h volume, 7d/30d change
- Circulating supply, max supply, total supply
- Market cap rank
- ATH and distance from ATH
- Number of exchanges where listed
- Links: website, whitepaper, GitHub

**Frequency:** Daily (respect free tier: 30 req/min)

#### `coinmarketcap_collector.py`

**Data collected (complementary to CoinGecko):**
- CMC rank
- Project tags and categories
- CMC proprietary scores

#### `defillama_collector.py`

**Data collected:**
- Total TVL of the protocol
- TVL evolution (30d, 90d)
- Chains where deployed
- DEX volume (if applicable)
- Revenue (fees generated)

**Frequency:** Daily

#### `github_collector.py`

**Data collected per repository:**
- Commits in the last 30/90/365 days
- Number of unique contributors
- Stars, forks, watchers
- Open vs closed issues
- Pull requests (open, closed, merged)
- Release frequency
- Languages used

**Frequency:** Weekly (GitHub API rate limits apply)

**Logic:** Find the project's main repository from CoinGecko metadata.

#### `social_collector.py`

Twitter/X:
- Mentions of the token in the last 24h
- Change in mentions vs 30d average
- Engagement (likes, retweets) of project posts
- Overall sentiment (positive/negative/neutral via AI)

Reddit:
- Posts in relevant subreddits
- Upvotes, comments
- Subreddit growth (subscribers)
- Trending posts

**Frequency:** Daily (mentions), Weekly (deep sentiment analysis)

#### `exchange_monitor.py`

**What it monitors:**

For each exchange (Binance, Coinbase, Kraken, OKX, Bybit, KuCoin):
- Current list of listed tokens
- Newly detected listings (diff vs previous snapshot)
- DEX volume (Uniswap, PancakeSwap) for tokens not yet listed

**Frequency:** Every 4 hours (possible listings are time-sensitive)

**Early-detection logic:**
1. Monitor tokens with high DEX volume but no CEX listing
2. Cross-check with holder growth
3. Cross-check with surging social mentions
4. Emit `ListingProbabilityScore`

---

### 6.2 Data Storage Layer

**PostgreSQL** as the primary database. **Redis** for API response cache and job queues.

See full schema in [Section 7](#7-database---schema).

---

### 6.3 Feature Engineering

**Responsibility:** Transform raw data into derived metrics ready for scoring.

#### Metrics computed per token

```python
# market_processor.py
volume_to_marketcap_ratio     # Volume/MarketCap — detects relative activity
volume_growth_7d              # % volume growth over 7 days
volume_growth_30d
marketcap_velocity            # Market cap acceleration
price_vs_ath_percentage       # Distance from ATH
liquidity_depth               # Orderbook depth / DEX liquidity

# dev_processor.py
commit_growth_30d             # Commit growth vs previous period
contributor_growth            # New contributors
release_frequency             # Releases/month
dev_activity_score            # Composite dev activity score

# social_processor.py
mention_growth_24h            # 24h mention growth
mention_growth_7d
social_acceleration           # Mention acceleration rate
sentiment_score               # -1.0 to 1.0

# anomaly_detector.py
volume_anomaly_score          # Standard deviations above historical mean
social_anomaly_score
dev_anomaly_score
```

---

### 6.4 Signal Generation Engine

**Responsibility:** Combine metrics into binary or probabilistic signals.

#### Signal types

```python
class Signal:
    token: str
    signal_type: SignalType    # Enum
    strength: float            # 0.0 to 1.0
    confidence: float          # 0.0 to 1.0
    timestamp: datetime
    metadata: dict

class SignalType(Enum):
    # Growth
    DEV_MOMENTUM         # Dev activity accelerating
    SOCIAL_EXPLOSION     # Mentions growing abnormally
    HOLDER_SPIKE         # Holders growing fast
    VOLUME_SURGE         # Abnormal volume
    LIQUIDITY_GROWTH     # Liquidity increasing
    
    # Market
    VOLUME_ANOMALY       # Statistically anomalous volume
    PRICE_BREAKOUT       # Breakout of a level
    
    # Listing
    LISTING_CANDIDATE    # High probability listing
    DEX_VOLUME_PRE_LISTING # DEX volume rising without CEX listing
    
    # Risk
    WHALE_ACCUMULATION   # Whales accumulating
    WHALE_DISTRIBUTION   # Whales selling
    MANIPULATION_RISK    # Signs of manipulation
    RUGPULL_RISK         # Rugpull signals
    TOKEN_UNLOCK_INCOMING # Upcoming token unlocks
    
    # Narrative
    NARRATIVE_ALIGNMENT  # Token aligned with an emerging narrative
    ECOSYSTEM_GROWING    # Token ecosystem expanding
```

---

### 6.5 AI Analysis Engine

**Responsibility:** Use LLMs for qualitative analysis and insight extraction.

#### `llm_provider.py` — LLM abstraction

Supports multiple providers with automatic fallback:

```
Priority:
1. Ollama (local, free) → try first
2. Google Gemini (free tier) → fallback if Ollama unavailable
3. OpenAI GPT-4o (paid) → final fallback if configured
```

#### `whitepaper_analyzer.py`

**Input:** Whitepaper URL (PDF) or extracted text  
**Output:**

```json
{
  "summary": "Plain-language summary (max 300 words)",
  "problem_solved": "Problem the project solves",
  "technology": "How it works technically",
  "token_utility": "What the token is used for",
  "competitors": ["Ethereum", "Solana"],
  "main_risks": ["centralization", "competition"],
  "innovation_score": 7.5,
  "differentiators": ["speed", "low cost"]
}
```

#### `narrative_detector.py`

**Pipeline:**
1. Collect recent posts from X and Reddit (last 48–72h)
2. Create embeddings with `sentence-transformers`
3. Run clustering (HDBSCAN or K-Means)
4. Identify dominant topics per cluster
5. Map tokens mentioned in each cluster
6. Calculate cluster momentum (growth vs prior week)

**Output:**

```json
{
  "narratives": [
    {
      "name": "AI + Blockchain",
      "momentum_score": 8.7,
      "trend": "accelerating",
      "tokens": ["FET", "RNDR", "TAO"],
      "keywords": ["AI agents", "GPU compute", "decentralized AI"]
    }
  ]
}
```

#### `project_classifier.py`

Classifies each token into categories:

```
Layer1 | Layer2 | DeFi | AI | Gaming | Infrastructure | 
DePIN | Oracle | Privacy | Memecoin | RWA | Restaking
```

#### `summary_generator.py`

Generates plain-language explanations of why a token may be interesting or risky. Example output:

> "Celestia is a blockchain that solves a serious technical problem: separating data availability (storage) from transaction execution. This allows other chains to be much cheaper. In 2024, the concept of 'modular blockchain' is gaining traction, and Celestia is a leader in this narrative. The main risk is that Ethereum is developing similar solutions."

---

### 6.6 Graph Intelligence Layer

**Responsibility:** Model the crypto market as a network of relationships and detect emerging ecosystems.

#### Graph structure

**Nodes (entities):**
- `Token` (e.g., Solana, Arbitrum)
- `Ecosystem` (e.g., Ethereum Ecosystem, Solana Ecosystem)
- `Narrative` (e.g., AI, DePIN, RWA)
- `Exchange` (e.g., Binance, Coinbase)
- `VCFund` (e.g., a16z, Multicoin)

**Edges (relations):**
- `Token → BELONGS_TO → Ecosystem`
- `Token → ALIGNED_WITH → Narrative`
- `Token → LISTED_ON → Exchange`
- `Token → FUNDED_BY → VCFund`
- `Token → INTEGRATED_WITH → Token`
- `Token → COMPETES_WITH → Token`

#### Algorithms

```python
# community_detector.py
# Detects clusters (ecosystems) of related tokens
# Algorithm: Louvain community detection

# centrality_analyzer.py
# Computes node importance in the network
# Metrics: PageRank, Betweenness Centrality

# ecosystem_tracker.py
# Tracks growth of each cluster over time
# Detects ecosystems with accelerating growth
```

#### Example output

```
Top Growing Ecosystems (last 30 days):

1. AI Infrastructure
   Tokens: FET, RNDR, TAO, AGIX
   Growth score: 8.7
   Trend: ACCELERATING ↑↑

2. Solana Ecosystem  
   Tokens: SOL, JUP, RAY, DRIFT
   Growth score: 7.9
   Trend: GROWING ↑

3. Modular Blockchain
   Tokens: TIA, AVAIL, EIGEN
   Growth score: 7.2
   Trend: GROWING ↑
```

---

### 6.7 Machine Learning Layer

**Responsibility:** Models trained to detect historical winner patterns.

#### `cycle_leader_model.py` — "Next Solana"

**Concept:**
Train a model using tokens that did 10x+ in past cycles (2017–2018, 2020–2021), using characteristics of projects **before** the pump.

**Input features:**
```
market_cap_rank          # Rank at the time (e.g., top 200)
volume_growth_90d        # Volume growth
dev_commit_growth_90d    # Dev activity growth
social_growth_90d        # Social growth
holder_growth_90d        # Holder growth
tvl_growth_90d           # TVL growth (if applicable)
narrative_score          # Alignment with dominant narrative
token_distribution       # Token concentration
age_days                 # Project age
```

**Target:**
```
cycle_leader: bool       # Achieved 10x+ in the following cycle
```

**Model:** XGBoost or Random Forest (good for tabular data)

**Output:**
```
Token: XYZ
Cycle Leader Probability: 0.73
Similar to early: Solana (0.71), Avalanche (0.64)
```

#### `listing_predictor.py`

**Features:**
```
dex_volume_growth_7d
holder_growth_7d
social_mentions_growth_7d
liquidity_depth
bridge_integrations_count
aggregator_listings_count
```

**Output:**
```
Listing Probability Score: 0.0 – 1.0
```

---

### 6.8 Scoring & Opportunity Engine

**Responsibility:** Compute the final composite score for each token.

#### Fundamental Score (inspired by a VC model)

| Pillar | Weight | Metrics used |
|--------|--------|--------------|
| Technology | 20% | Innovation, differentiation (LLM analysis of whitepaper) |
| Tokenomics | 20% | Supply, inflation, utility, distribution, unlocks |
| Adoption | 20% | TVL, users, transactions, integrations |
| Dev Activity | 20% | Commits, contributors, releases |
| Narrative Fit | 20% | Alignment with dominant narrative |

#### Growth Score

```python
growth_score = (
    0.25 * dev_commit_growth_30d_normalized +
    0.20 * social_growth_30d_normalized +
    0.20 * holder_growth_30d_normalized +
    0.20 * volume_growth_30d_normalized +
    0.15 * liquidity_growth_30d_normalized
)
```

#### Risk Score (inverse — lower = riskier)

```python
risk_score = (
    0.30 * rugpull_risk_inverse +
    0.25 * manipulation_risk_inverse +
    0.25 * tokenomics_risk_inverse +   # unlocks, inflation
    0.20 * whale_concentration_inverse
)
```

#### Opportunity Score (final score)

```python
opportunity_score = (
    0.30 * fundamental_score +
    0.25 * growth_score +
    0.20 * narrative_score +
    0.15 * listing_probability +
    0.10 * risk_score
) * cycle_leader_probability_boost  # ML model multiplier
```

---

### 6.9 Risk Detection Engine

#### `rugpull_detector.py`

Alert signals:
- Completely anonymous team with no verifiable history
- Concentration above 30% of supply in top 10 wallets
- Very low liquidity relative to market cap
- Contract without an audit (check Certik, Hacken)
- No code on GitHub or repositories with very low activity
- Recent launch (< 6 months) with aggressive promises

#### `manipulation_detector.py`

Detected patterns:
- **Pump and dump:** Volume explodes, price rises rapidly, holders do not increase proportionally
- **Wash trading:** High volume without real changes in holders or liquidity
- **Coordinated social pump:** Explosion of mentions from low-credibility accounts

#### `whale_tracker.py`

- Monitor top 50 wallets for each token
- Detect consistent accumulation (gradual buys over time)
- Detect distribution (large wallets selling in tranches)
- Compute `Whale Accumulation Score`

#### `tokenomics_risk.py`

- Unlock calendar for the next 90 days
- Percentage of supply to be unlocked
- Current and future inflation rate
- Alert: unlock > 5% of supply in the next 30 days

---

### 6.10 Alert Engine

#### Alert types

| Type | Urgency | Channel |
|------|---------|---------|
| `LISTING_CANDIDATE` | High | Telegram |
| `MEMECOIN_HYPE_DETECTED` | High | Telegram |
| `WHALE_ACCUMULATION` | Medium | Telegram |
| `NARRATIVE_EMERGING` | Medium | Telegram |
| `RUGPULL_RISK` | High | Telegram |
| `TOKEN_UNLOCK_SOON` | Medium | Telegram |
| `DAILY_REPORT` | Low | Telegram |
| `MANIPULATION_DETECTED` | High | Telegram |

#### Telegram format

```
🚨 LISTING CANDIDATE DETECTED

Token: ABC
Symbol: ABC

Listing score: 82/100

Detected signals:
✅ DEX volume grew 340% in 7 days
✅ Holders grew 28% in 7 days  
✅ Social mentions +180%
✅ Bridge integration detected

Estimated probability: High
Most likely exchanges: Binance, KuCoin

⚠️ Not a guarantee. Do your own research.
```

---

### 6.11 Backtesting Engine

**Responsibility:** Test the model against historical data to validate effectiveness.

#### How it works

1. Load historical data for a period (e.g., Jan 2019 – Jan 2020)
2. Run the full scoring pipeline **as if it were that time**
3. Compare the generated ranking with what actually happened in the following cycle
4. Compute performance metrics

#### Evaluation metrics

```
Precision@10: of the top 10 recommended, how many did 5x+?
Recall@50:    of the 50 that did 5x+, how many were in the top 50?
Hit rate:     % of recommended tokens that outperformed the market
```

#### Interface

```bash
# Run backtesting on 2019–2021 cycle
cryptoai backtest --start 2019-01-01 --end 2021-01-01 --top 20

# Expected output:
# Precision@10: 6/10 (60%)
# Tokens that would have been highlighted: SOL, AVAX, MATIC...
```

---

### 6.12 Report Generator

#### Report types

**Token Report (on-demand):**
- Plain-language executive summary
- Detailed score by pillar
- Metric evolution charts
- Risk analysis
- Possible catalysts

**Daily Report (automatic):**
- Top 10 opportunities of the day
- Active alerts
- Narrative movements

**Monthly Report (automatic):**
- Deep analysis of top 20
- Cycle review
- Model performance (hits/misses)

---

### 6.13 Dashboard (React Frontend)

#### Pages

**Home — Rankings**
- Table with Top Opportunities, sortable by any score
- Filters: category, market cap range, narrative
- Alert chips
- Mini 30-day score sparkline per token

**Token Detail**
- Visual score breakdown (radar chart of 5 pillars)
- Market metrics with time series charts
- Dev activity timeline
- Social trend
- Plain-language analysis (generated by AI)
- Active alerts for the token
- "Generate PDF Report" button

**Narratives**
- Cards for emerging narratives
- Momentum chart per narrative
- Tokens associated with each narrative

**Ecosystem Graph**
- Interactive Knowledge Graph visualization
- Click node → details
- Filter by ecosystem

**Backtesting**
- UI to configure and run backtests
- Results visualization

**Alerts**
- Historical alerts feed
- Alert configuration

---

### 6.14 CLI

```bash
# Main commands

cryptoai scan                          # Runs full analysis
cryptoai top [--n 20]                  # Lists top N opportunities
cryptoai report <SYMBOL>               # Detailed token report
cryptoai narrative                     # Emerging narratives
cryptoai alerts                        # Active alerts
cryptoai backtest [--start] [--end]    # Run backtesting
cryptoai update                        # Force data refresh
cryptoai config                        # Show current configuration
```

---

## 7. Database — Schema

```sql
-- Registered tokens
CREATE TABLE tokens (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    coingecko_id    VARCHAR(100),
    cmc_id          INTEGER,
    category        VARCHAR(50),          -- Layer1, DeFi, AI, etc
    github_repo     VARCHAR(200),
    whitepaper_url  VARCHAR(500),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Market data (daily snapshot)
CREATE TABLE market_data (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    price_usd       DECIMAL(20,8),
    market_cap      BIGINT,
    volume_24h      BIGINT,
    rank            INTEGER,
    circulating_supply BIGINT,
    max_supply      BIGINT,
    ath             DECIMAL(20,8),
    ath_change_pct  DECIMAL(10,4),
    price_change_7d DECIMAL(10,4),
    price_change_30d DECIMAL(10,4),
    tvl             BIGINT,
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_market_data_token_date ON market_data(token_id, snapshot_date);

-- Development activity
CREATE TABLE dev_activity (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    commits_30d     INTEGER,
    commits_90d     INTEGER,
    contributors    INTEGER,
    stars           INTEGER,
    forks           INTEGER,
    open_issues     INTEGER,
    closed_issues   INTEGER,
    releases_count  INTEGER,
    last_release    TIMESTAMP,
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Social data
CREATE TABLE social_data (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    twitter_mentions_24h INTEGER,
    twitter_sentiment    DECIMAL(4,3),    -- -1.0 to 1.0
    reddit_posts_7d      INTEGER,
    reddit_subscribers   INTEGER,
    reddit_growth_pct    DECIMAL(10,4),
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Holders and liquidity
CREATE TABLE holder_data (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    holder_count    INTEGER,
    top10_pct       DECIMAL(5,2),        -- % of supply in top 10 wallets
    top50_pct       DECIMAL(5,2),
    dex_volume_24h  BIGINT,
    dex_liquidity   BIGINT,
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Calculated scores
CREATE TABLE token_scores (
    id                  SERIAL PRIMARY KEY,
    token_id            INTEGER REFERENCES tokens(id),
    fundamental_score   DECIMAL(4,2),
    technology_score    DECIMAL(4,2),
    tokenomics_score    DECIMAL(4,2),
    adoption_score      DECIMAL(4,2),
    dev_activity_score  DECIMAL(4,2),
    narrative_score     DECIMAL(4,2),
    growth_score        DECIMAL(4,2),
    risk_score          DECIMAL(4,2),
    listing_probability DECIMAL(4,3),
    cycle_leader_prob   DECIMAL(4,3),
    opportunity_score   DECIMAL(4,2),
    snapshot_date       DATE NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_scores_date ON token_scores(snapshot_date);

-- Generated signals
CREATE TABLE signals (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    signal_type     VARCHAR(50),
    strength        DECIMAL(4,3),
    confidence      DECIMAL(4,3),
    metadata        JSONB,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    expires_at      TIMESTAMP
);

-- Fired alerts
CREATE TABLE alerts (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    alert_type      VARCHAR(50),
    message         TEXT,
    metadata        JSONB,
    sent_telegram   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Detected narratives
CREATE TABLE narratives (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100),
    momentum_score  DECIMAL(4,2),
    trend           VARCHAR(20),          -- accelerating, growing, stable, declining
    keywords        TEXT[],
    token_symbols   TEXT[],
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- AI analyses (cache)
CREATE TABLE ai_analyses (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    analysis_type   VARCHAR(50),          -- whitepaper, summary, classification
    content         TEXT,
    model_used      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Historical snapshots for backtesting
CREATE TABLE historical_snapshots (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    snapshot_data   JSONB,               -- full serialized snapshot
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 8. External Integrations & APIs

| Service | Purpose | Free Tier | Base endpoint |
|---------|---------|-----------|---------------|
| CoinGecko | Primary market data | 30 req/min | `https://api.coingecko.com/api/v3` |
| CoinMarketCap | Complementary market data | 333 req/day | `https://pro-api.coinmarketcap.com/v1` |
| DefiLlama | TVL, DeFi data | No limit | `https://api.llama.fi` |
| GitHub | Dev activity | 60 req/h (unauth), 5000 (auth) | `https://api.github.com` |
| Twitter/X API | Social data | Limited (Basic plan) | `https://api.twitter.com/2` |
| Reddit API | Social data | Free | `https://www.reddit.com/r/{sub}/new.json` |
| Telegram Bot API | Alerts | Free | `https://api.telegram.org` |
| Gemini API | LLM | Free tier | `https://generativelanguage.googleapis.com` |
| Ollama | LLM local | Free | `http://localhost:11434` |

---

## 9. Scoring System — Details

### Full formula

```python
def calculate_opportunity_score(token: Token) -> float:
    
    # Pillar 1: Fundamentals (30%)
    fundamental = (
        technology_score * 0.20 +
        tokenomics_score * 0.20 +
        adoption_score   * 0.20 +
        dev_score        * 0.20 +
        narrative_fit    * 0.20
    )
    
    # Pillar 2: Growth (25%)
    growth = (
        dev_commit_growth    * 0.25 +
        social_growth        * 0.20 +
        holder_growth        * 0.20 +
        volume_growth        * 0.20 +
        liquidity_growth     * 0.15
    )
    
    # Pillar 3: Narrative (20%)
    narrative = narrative_momentum_score
    
    # Pillar 4: Listing probability (15%)
    listing = listing_probability_score
    
    # Pillar 5: Risk adjustment (10%)
    risk_adjustment = 1.0 - (risk_score * 0.5)  # high risk penalizes
    
    base_score = (
        fundamental  * 0.30 +
        growth       * 0.25 +
        narrative    * 0.20 +
        listing      * 0.15 +
        risk_adjustment * 0.10
    )
    
    # ML boost
    cycle_boost = 1.0 + (cycle_leader_probability * 0.20)
    
    return min(base_score * cycle_boost, 10.0)  # cap at 10.0
```

---

## 10. Development Roadmap

### Phase 1 — Functional MVP (2–3 weeks)

**Goal:** System running with real data, functional CLI, basic ranking.

- [ ] Project setup (Docker, PostgreSQL, FastAPI, folder structure)
- [ ] `CoinGeckoCollector` operational
- [ ] DB schema + Alembic migrations
- [ ] `MarketProcessor` with basic metrics
- [ ] Simplified `FundamentalScorer` (no LLM yet)
- [ ] CLI with `cryptoai top` and `cryptoai report`
- [ ] Scheduler running daily collection

**Deliverable:** `cryptoai top 20` shows ranking with real data.

---

### Phase 2 — Dev Activity + Social (1–2 weeks)

- [ ] `GitHubCollector` operational
- [ ] `SocialCollector` (Reddit first, X later)
- [ ] `DevProcessor` and `SocialProcessor`
- [ ] `GrowthScorer` with real metrics
- [ ] Basic `AnomalyDetector`

**Deliverable:** Scores include dev activity and social growth.

---

### Phase 3 — AI & Narratives (2 weeks)

- [ ] `LLMProvider` with Ollama and Gemini support
- [ ] `WhitepaperAnalyzer`
- [ ] `NarrativeDetector` with embeddings
- [ ] `ProjectClassifier`
- [ ] `SummaryGenerator`

**Deliverable:** `cryptoai report SOL` generates full analysis with plain-language text.

---

### Phase 4 — Listing Radar + Risk (1–2 weeks)

- [ ] `ExchangeMonitor` operational
- [ ] `ListingSignals` and `ListingPredictor`
- [ ] `RugpullDetector`
- [ ] `ManipulationDetector`
- [ ] `WhaleTracker`
- [ ] `TokenomicsRisk` with unlock calendar

**Deliverable:** Listing and risk alerts operational.

---

### Phase 5 — Telegram + Reports (1 week)

- [ ] `TelegramBot` configured
- [ ] Automatic alerts
- [ ] `MarkdownGenerator` for reports
- [ ] `PDFGenerator`

**Deliverable:** Alerts arriving on Telegram. Exportable reports.

---

### Phase 6 — React Dashboard (2–3 weeks)

- [ ] Setup React + Vite + TailwindCSS + shadcn/ui
- [ ] Home page with ranking
- [ ] Token Detail page
- [ ] Narratives page
- [ ] Connect to FastAPI

**Deliverable:** Local visual dashboard.

---

### Phase 7 — ML + Graph + Backtesting (3–4 weeks)

- [ ] `CycleLeaderModel` with historical data
- [ ] `GraphBuilder` and `CommunityDetector`
- [ ] `BacktestingEngine`
- [ ] Graph visualization in frontend (D3.js)
- [ ] Backtesting page in frontend

**Deliverable:** "Next Solana" score. Validated backtesting. Visual Knowledge Graph.

---

## 11. Configuration & Environment Variables

```env
# .env.example

# ===== DATABASE =====
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/cryptoai
REDIS_URL=redis://redis:6379

# ===== API KEYS =====
COINGECKO_API_KEY=           # Optional (improves rate limit)
COINMARKETCAP_API_KEY=       # Required for CMC
GITHUB_TOKEN=                # Required for dev activity
TWITTER_BEARER_TOKEN=        # Optional (paid plan)
GEMINI_API_KEY=              # For Gemini LLM
OPENAI_API_KEY=              # Optional, paid fallback
TELEGRAM_BOT_TOKEN=          # For alerts
TELEGRAM_CHAT_ID=            # Your chat ID

# ===== LLM PROVIDER =====
LLM_PRIMARY=ollama            # ollama | gemini | openai
LLM_FALLBACK=gemini
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2

# ===== ANALYSIS =====
TOKENS_TO_ANALYZE=300        # Number of tokens to analyze
ANALYSIS_CURRENCY=USD
COINGECKO_VS_CURRENCY=usd

# ===== SCHEDULER =====
REALTIME_INTERVAL_MINUTES=30
DAILY_RUN_HOUR=6             # Daily collection hour (UTC)
WEEKLY_RUN_DAY=monday
MONTHLY_RUN_DAY=1

# ===== ALERTS =====
ALERT_LISTING_THRESHOLD=0.70         # Minimum score to alert listing
ALERT_WHALE_ACCUMULATION_THRESHOLD=7.0
ALERT_MEMECOIN_SOCIAL_GROWTH=500     # % growth in 48h

# ===== FRONTEND =====
VITE_API_BASE_URL=http://localhost:8000
```

---

## 12. Docker & Infrastructure

```yaml
# docker-compose.yml

version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cryptoai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    # GPU support (optional):
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - capabilities: [gpu]

  backend:
    build: ./backend
    env_file: .env
    depends_on:
      - postgres
      - redis
      - ollama
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  scheduler:
    build: ./backend
    env_file: .env
    depends_on:
      - postgres
      - redis
    command: python -m app.scheduler.jobs
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
  ollama_data:
```

---

## 13. Example Outputs

### CLI: `cryptoai top 10`

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CRYPTO AI RESEARCH TERMINAL                      │
│                    Top Opportunities — 2025-03-10                   │
└─────────────────────────────────────────────────────────────────────┘

#   Symbol  Name          Score  Fund  Growth  Narr  Risk   Signals
─────────────────────────────────────────────────────────────────────
1   SOL     Solana         8.7   8.5    9.1    8.8   low    🚀 ↑dev ↑social
2   TIA     Celestia       8.4   8.2    8.7    9.0   low    🔥 narrative leader
3   NEAR    Near Protocol  7.9   8.0    7.8    7.5   low    ↑dev ↑holders
4   RNDR    Render         7.8   7.5    8.1    9.2   med    🤖 AI narrative
5   ARB     Arbitrum       7.6   8.1    7.2    7.8   low    ↑TVL ↑users
6   FET     Fetch.ai       7.4   7.0    8.3    9.1   med    🤖 AI narrative
7   INJ     Injective      7.3   7.8    7.5    7.6   low    ↑dev activity
8   TAO     Bittensor      7.1   6.8    8.9    9.3   high   ⚠ high concentration
9   JUP     Jupiter        7.0   7.2    7.8    7.4   low    ↑DEX volume
10  EIGEN   EigenLayer     6.9   7.5    6.8    8.0   med    restaking narr.
```

### CLI: `cryptoai report TIA`

```
══════════════════════════════════════════
CELESTIA (TIA) — Full Report
Generated: 2025-03-10 | Score: 8.4/10
══════════════════════════════════════════

📋 SUMMARY (generated by AI)
─────────────────────────
Celestia solves a fundamental technical problem: traditional blockchains try to do everything at once (execute, validate, store). Celestia focuses on one thing — data availability/storage — and does it well. This allows other chains (e.g., Ethereum rollups) to use Celestia as a base, making them much cheaper and faster.

The "modular blockchain" concept is growing in 2025, and Celestia is a primary bet in this narrative.

📊 DETAILED SCORES
────────────────────
Technology:    ████████░░  8.2/10
Tokenomics:    ███████░░░  7.5/10
Adoption:      ███████░░░  7.8/10
Dev Activity:  █████████░  8.9/10
Narrative:     █████████░  9.0/10

Overall:       ████████░░  8.4/10

📈 GROWTH (30 days)
────────────────────────
Dev commits:   +34%  ↑↑
Social:        +28%  ↑
Holders:       +15%  ↑
Volume:        +22%  ↑
TVL:           +41%  ↑↑

⚠ RISKS
─────────
• Ethereum developing similar solutions (EIP-4844)
• Token unlock of 8% in June/2025
• Dependence on adoption by other projects (B2B)

🎯 POTENTIAL CATALYSTS
──────────────────────────
• Growth of rollups using Celestia as a DA layer
• Partnerships with Ethereum projects
• Possible Coinbase listing (probability: 58%)

🔗 LINKS
─────────
Website:    https://celestia.org
GitHub:     https://github.com/celestiaorg
Whitepaper: https://celestia.org/whitepaper
```

### Telegram Alert — Listing Candidate

```
🚨 LISTING CANDIDATE DETECTED

🪙 Token: PUMP
Network: Solana

📊 Listing score: 84/100

Detected signals:
✅ DEX Volume: +420% in 7 days  
✅ Holders: +35% in 7 days
✅ Twitter mentions: +890% in 48h
✅ Liquidity steadily increasing
⚠️ Classified as: Memecoin

Most likely exchanges: KuCoin, Bybit

Recommended action: MONITOR
⚠️ Automated analysis. Do your own research.

[View details on the dashboard]
```

---

## 14. Design Decisions & Rationale

| Decision | Alternative considered | Reason for choice |
|---------|------------------------|-------------------|
| PostgreSQL | MongoDB | Relational data + JSONB flexibility |
| APScheduler | Celery + Beat | Lower complexity for single-user use |
| XGBoost for ML | Deep Learning | Better for medium-sized tabular data |
| NetworkX for graph | Neo4j | Avoid extra service overhead in Phase 1; migrate later |
| LangChain | Direct API calls | Easier provider swap and complex chains |
| Ollama as primary LLM | Only paid APIs | Zero cost, privacy, no limits |
| sentence-transformers | OpenAI embeddings | Local, free, sufficient quality |
| React | Streamlit | More professional, better UX, reusable |
| FastAPI | Flask | Native async, typing, OpenAPI docs |

---

*Document generated for use with GitHub Copilot + Claude Sonnet 4.6*  
*Last updated: 2025-03-10*  
*Status: Ready for development — Phase 1*
