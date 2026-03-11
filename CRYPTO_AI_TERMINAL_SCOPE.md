# 🧠 Crypto AI Research Terminal — Escopo Técnico Completo

> **Documento de especificação para uso com GitHub Copilot + Claude Sonnet 4.6**  
> Versão: 1.0 | Status: Draft | Perfil do investidor: Longo prazo, foco em ciclo BTC

---

## 📌 Sumário

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Objetivos e Requisitos](#2-objetivos-e-requisitos)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Estrutura de Diretórios](#5-estrutura-de-diretórios)
6. [Módulos Detalhados](#6-módulos-detalhados)
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
   - 6.13 Dashboard (Frontend React)
   - 6.14 CLI
7. [Banco de Dados — Schema](#7-banco-de-dados--schema)
8. [Integrações Externas e APIs](#8-integrações-externas-e-apis)
9. [Sistema de Scoring — Detalhamento](#9-sistema-de-scoring--detalhamento)
10. [Roadmap de Desenvolvimento](#10-roadmap-de-desenvolvimento)
11. [Configurações e Variáveis de Ambiente](#11-configurações-e-variáveis-de-ambiente)
12. [Docker e Infraestrutura](#12-docker-e-infraestrutura)
13. [Exemplos de Output Esperado](#13-exemplos-de-output-esperado)
14. [Decisões de Design e Justificativas](#14-decisões-de-design-e-justificativas)

---

## 1. Visão Geral do Projeto

### O que é

O **Crypto AI Research Terminal** é uma plataforma pessoal de inteligência de mercado para criptomoedas, baseada em IA, que automatiza:

- Análise fundamentalista de altcoins (Top 300, configurável)
- Detecção de narrativas emergentes de mercado
- Radar de possíveis listagens em exchanges tier 1
- Detecção de acumulação por whales e atividade institucional
- Identificação de projetos com perfil de crescimento explosivo ("próxima Solana")
- Alertas sobre riscos (rugpull, manipulação, tokens bomba-relógio)
- Backtesting do modelo contra ciclos históricos (2017, 2020–2021)

### O que NÃO é

- Um bot de trading automático
- Um sistema de previsão de preços
- Uma ferramenta de day trade ou scalping

### Filosofia do sistema

> A IA não decide. Ela pesquisa, organiza, pontua e explica. A decisão final é sempre do usuário.

O sistema funciona como um **analista quantitativo pessoal**, reduzindo o custo cognitivo de pesquisar centenas de projetos, filtrando ruído e destacando sinais.

---

## 2. Objetivos e Requisitos

### Objetivos Principais

| # | Objetivo |
|---|----------|
| 1 | Analisar fundamentos de criptos automaticamente (tecnologia, tokenomics, equipe, adoção) |
| 2 | Detectar narrativas emergentes de mercado antes do mainstream |
| 3 | Estimar probabilidade de listagem em exchange tier 1 |
| 4 | Identificar projetos com potencial explosivo de crescimento ("10x candidates") |
| 5 | Detectar riscos: rugpull, dump de tokens, manipulação de mercado |
| 6 | Monitorar ciclo do Bitcoin e estimar fases de altseason |
| 7 | Permitir backtesting do modelo em ciclos passados |
| 8 | Gerar relatórios claros (MD/PDF) e alertas via Telegram |

### Requisitos Funcionais

- Analisar Top 300 criptomoedas por padrão (número configurável via `.env`)
- Coletar dados em frequências distintas: realtime, diário, semanal, mensal
- Suportar múltiplos provedores de IA: **Ollama** (local/grátis), **Gemini** (gratuito com limite), **OpenAI** (opcional pago)
- Expor dashboard web React com ranking e páginas de detalhe
- Expor CLI para acesso rápido via terminal
- Enviar alertas importantes via Telegram
- Exportar relatórios em Markdown e PDF
- Rodar completamente em **Docker** no PC local

### Requisitos Não Funcionais

- Arquitetura modular: cada módulo pode ser desenvolvido e testado isoladamente
- Código bem documentado em português e inglês (docstrings em inglês, comentários em português quando necessário)
- Configuração centralizada em `.env`
- Logs estruturados em todos os serviços
- Tolerância a falhas: se uma API falhar, o sistema continua com dados cacheados

---

## 3. Arquitetura do Sistema

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

## 4. Stack Tecnológico

### Backend

| Componente | Tecnologia | Justificativa |
|------------|-----------|---------------|
| Linguagem | Python 3.11+ | Ecossistema de dados/IA imbatível |
| Framework API | FastAPI | Async, moderno, auto-documentado |
| Task Scheduler | APScheduler | Leve, sem overhead do Celery para uso pessoal |
| ORM | SQLAlchemy 2.x | Maduro, suporte a async |
| Migrations | Alembic | Padrão com SQLAlchemy |

### Banco de Dados

| Componente | Tecnologia |
|------------|-----------|
| Principal | PostgreSQL 15 |
| Cache / Filas | Redis |
| Grafo (futuro) | NetworkX (em memória), migrar para Neo4j quando necessário |

### IA / ML

| Componente | Tecnologia | Quando usar |
|------------|-----------|-------------|
| LLM primário | Ollama (llama3, mistral) | Sem custo, local |
| LLM secundário | Google Gemini API | Free tier, mais poderoso |
| LLM terciário | OpenAI GPT-4o | Opcional, pago |
| Embeddings | sentence-transformers | Detecção de narrativa, similaridade |
| ML clássico | scikit-learn, XGBoost | Scoring, classificação, backtesting |
| Orquestração LLM | LangChain | Chains de análise complexa |
| Grafo | NetworkX | Knowledge graph, community detection |

### Frontend

| Componente | Tecnologia |
|------------|-----------|
| Framework | React 18 + TypeScript |
| Build | Vite |
| UI Components | shadcn/ui + TailwindCSS |
| Gráficos | Recharts |
| Grafo visual | React Flow ou D3.js |
| Estado | Zustand |
| HTTP Client | Axios + React Query |

### Infra

| Componente | Tecnologia |
|------------|-----------|
| Containerização | Docker + Docker Compose |
| Reverse Proxy | Nginx (opcional, fase avançada) |
| Logs | structlog (Python) |

---

## 5. Estrutura de Diretórios

```
crypto-ai-terminal/
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Configurações centralizadas
│   │   ├── dependencies.py            # Injeção de dependência FastAPI
│   │   │
│   │   ├── api/                       # Rotas da API REST
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── tokens.py          # GET /tokens, /tokens/{symbol}
│   │   │   │   ├── rankings.py        # GET /rankings/opportunities
│   │   │   │   ├── narratives.py      # GET /narratives/trending
│   │   │   │   ├── alerts.py          # GET /alerts
│   │   │   │   ├── reports.py         # POST /reports/generate
│   │   │   │   └── backtesting.py     # POST /backtesting/run
│   │   │
│   │   ├── collectors/                # Coleta de dados externos
│   │   │   ├── __init__.py
│   │   │   ├── base_collector.py      # Classe base com retry, rate limit
│   │   │   ├── coingecko_collector.py
│   │   │   ├── coinmarketcap_collector.py
│   │   │   ├── defillama_collector.py
│   │   │   ├── github_collector.py
│   │   │   ├── social_collector.py    # X (Twitter) + Reddit
│   │   │   └── exchange_monitor.py    # Monitoramento de listagens
│   │   │
│   │   ├── processors/                # Feature engineering
│   │   │   ├── __init__.py
│   │   │   ├── market_processor.py    # Métricas de mercado
│   │   │   ├── social_processor.py    # Métricas sociais
│   │   │   ├── dev_processor.py       # Métricas de dev activity
│   │   │   ├── anomaly_detector.py    # Detecção de anomalias estatísticas
│   │   │   └── normalizer.py          # Normalização de dados
│   │   │
│   │   ├── signals/                   # Geração de sinais
│   │   │   ├── __init__.py
│   │   │   ├── growth_signals.py      # Sinais de crescimento
│   │   │   ├── market_signals.py      # Sinais de mercado
│   │   │   ├── listing_signals.py     # Sinais de listagem
│   │   │   ├── whale_signals.py       # Sinais de whale activity
│   │   │   └── narrative_signals.py   # Sinais de narrativa
│   │   │
│   │   ├── ai/                        # Motor de IA
│   │   │   ├── __init__.py
│   │   │   ├── llm_provider.py        # Abstração: Ollama / Gemini / OpenAI
│   │   │   ├── whitepaper_analyzer.py # Análise de whitepapers
│   │   │   ├── narrative_detector.py  # Detecção de narrativas via embeddings
│   │   │   ├── project_classifier.py  # Classificação de projeto (Layer1, DeFi, etc)
│   │   │   └── summary_generator.py   # Geração de resumos em linguagem simples
│   │   │
│   │   ├── graph/                     # Knowledge Graph
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py       # Construção do grafo
│   │   │   ├── community_detector.py  # Detecção de clusters/ecossistemas
│   │   │   ├── centrality_analyzer.py # PageRank, betweenness
│   │   │   └── ecosystem_tracker.py   # Rastreamento de ecossistemas emergentes
│   │   │
│   │   ├── ml/                        # Machine Learning
│   │   │   ├── __init__.py
│   │   │   ├── feature_builder.py     # Construção de feature vectors
│   │   │   ├── cycle_leader_model.py  # Modelo: "próxima Solana"
│   │   │   ├── listing_predictor.py   # Modelo: probabilidade de listing
│   │   │   └── model_trainer.py       # Treinamento e avaliação
│   │   │
│   │   ├── scoring/                   # Engine de scoring
│   │   │   ├── __init__.py
│   │   │   ├── fundamental_scorer.py  # Score fundamental (5 pilares VC)
│   │   │   ├── growth_scorer.py       # Score de crescimento
│   │   │   ├── narrative_scorer.py    # Score de narrativa
│   │   │   ├── risk_scorer.py         # Score de risco
│   │   │   ├── listing_scorer.py      # Probabilidade de listing
│   │   │   └── opportunity_engine.py  # Score final composto
│   │   │
│   │   ├── risk/                      # Detecção de risco
│   │   │   ├── __init__.py
│   │   │   ├── rugpull_detector.py
│   │   │   ├── manipulation_detector.py
│   │   │   ├── whale_tracker.py
│   │   │   └── tokenomics_risk.py     # Unlock calendar, inflação
│   │   │
│   │   ├── alerts/                    # Sistema de alertas
│   │   │   ├── __init__.py
│   │   │   ├── telegram_bot.py
│   │   │   ├── alert_rules.py         # Regras de disparo
│   │   │   └── alert_formatter.py     # Formatação das mensagens
│   │   │
│   │   ├── reports/                   # Geração de relatórios
│   │   │   ├── __init__.py
│   │   │   ├── markdown_generator.py
│   │   │   ├── pdf_generator.py
│   │   │   └── templates/
│   │   │       ├── token_report.md.j2
│   │   │       └── market_report.md.j2
│   │   │
│   │   ├── backtesting/               # Backtesting Engine
│   │   │   ├── __init__.py
│   │   │   ├── data_loader.py         # Carrega dados históricos
│   │   │   ├── simulation_engine.py   # Simula o modelo em ciclos passados
│   │   │   └── performance_metrics.py # Precision, recall, acertos
│   │   │
│   │   ├── scheduler/                 # Agendamento de jobs
│   │   │   ├── __init__.py
│   │   │   └── jobs.py                # Definição dos jobs periódicos
│   │   │
│   │   └── models/                    # Modelos SQLAlchemy
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
│   ├── tests/                         # Testes unitários e de integração
│   ├── cli.py                         # Entry point da CLI
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
│   │   │   ├── Home.tsx               # Ranking principal
│   │   │   ├── TokenDetail.tsx        # Página de detalhe de um token
│   │   │   ├── Narratives.tsx         # Narrativas emergentes
│   │   │   ├── Ecosystems.tsx         # Knowledge Graph visual
│   │   │   ├── Backtesting.tsx        # Interface de backtesting
│   │   │   └── Alerts.tsx             # Histórico de alertas
│   │   ├── hooks/
│   │   ├── services/                  # Chamadas à API
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
│   ├── seed_historical_data.py        # Popula banco com dados históricos
│   ├── import_whitepaper.py           # Importa e analisa whitepaper
│   └── run_backtest.py                # Script rápido de backtesting
│
├── data/
│   └── historical/                    # CSVs de dados históricos para backtesting
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 6. Módulos Detalhados

### 6.1 Data Collectors

**Responsabilidade:** Coletar dados de fontes externas e persistir no banco.

#### `base_collector.py`

Classe base que todos os collectors herdam. Implementa:
- Retry automático com backoff exponencial
- Rate limiting respeitando limites das APIs
- Logging estruturado
- Método `collect()` abstrato

```python
# Exemplo de interface esperada
class BaseCollector:
    async def collect(self, symbols: list[str]) -> list[dict]: ...
    async def collect_single(self, symbol: str) -> dict: ...
```

#### `coingecko_collector.py`

**Dados coletados:**
- Preço, market cap, volume 24h, variação 7d/30d
- Circulating supply, max supply, total supply
- Market cap rank
- ATH e distância do ATH
- Número de exchanges onde está listado
- Links: website, whitepaper, GitHub

**Frequência:** Diária (respeitar free tier: 30 req/min)

#### `coinmarketcap_collector.py`

**Dados coletados (complementares ao CoinGecko):**
- CMC rank
- Tags e categorias do projeto
- Scores proprietários da CMC

#### `defillama_collector.py`

**Dados coletados:**
- TVL total do protocolo
- Evolução do TVL (30d, 90d)
- Chains onde está deployed
- Volume de DEX (se aplicável)
- Revenue (fees geradas)

**Frequência:** Diária

#### `github_collector.py`

**Dados coletados por repositório:**
- Commits nos últimos 30/90/365 dias
- Número de contribuidores únicos
- Stars, forks, watchers
- Issues abertas vs fechadas
- Pull requests (abertos, fechados, merged)
- Frequência de releases
- Linguagens usadas

**Frequência:** Semanal (GitHub API tem rate limit)

**Lógica:** Buscar o repositório principal do projeto a partir dos metadados do CoinGecko.

#### `social_collector.py`

**Twitter/X:**
- Menções do token nas últimas 24h
- Variação de menções vs média 30d
- Engajamento (likes, retweets) dos posts do projeto
- Sentimento geral (positivo/negativo/neutro via IA)

**Reddit:**
- Posts nos subreddits relevantes
- Upvotes, comentários
- Crescimento do subreddit (subscribers)
- Posts trending

**Frequência:** Diária (menções), Semanal (análise de sentimento profunda)

#### `exchange_monitor.py`

**O que monitora:**

Para cada exchange (Binance, Coinbase, Kraken, OKX, Bybit, KuCoin):
- Lista atual de tokens listados
- Novos listings detectados (diff com snapshot anterior)
- Volume em DEX (Uniswap, PancakeSwap) para tokens ainda não listados

**Frequência:** A cada 4 horas (possível listing é tempo-sensível)

**Lógica de detecção antecipada:**
1. Monitorar tokens com volume alto em DEX mas não listados em CEX
2. Cruzar com crescimento de holders
3. Cruzar com menções sociais crescentes
4. Gerar `ListingProbabilityScore`

---

### 6.2 Data Storage Layer

**PostgreSQL** como banco principal. **Redis** para cache de respostas de API e filas de jobs.

Ver schema completo na [Seção 7](#7-banco-de-dados--schema).

---

### 6.3 Feature Engineering

**Responsabilidade:** Transformar dados brutos em métricas derivadas prontas para scoring.

#### Métricas calculadas por token

```python
# market_processor.py
volume_to_marketcap_ratio     # Volume/MarketCap — detecta atividade relativa
volume_growth_7d              # Crescimento % de volume em 7 dias
volume_growth_30d
marketcap_velocity            # Aceleração do market cap
price_vs_ath_percentage       # Distância do ATH
liquidity_depth               # Profundidade da orderbook / liquidez DEX

# dev_processor.py
commit_growth_30d             # Crescimento de commits vs período anterior
contributor_growth            # Novos contribuidores
release_frequency             # Releases/mês
dev_activity_score            # Score composto de atividade dev

# social_processor.py
mention_growth_24h            # Crescimento de menções em 24h
mention_growth_7d
social_acceleration           # Taxa de aceleração das menções
sentiment_score               # -1.0 a 1.0

# anomaly_detector.py
volume_anomaly_score          # Desvios padrão acima da média histórica
social_anomaly_score
dev_anomaly_score
```

---

### 6.4 Signal Generation Engine

**Responsabilidade:** Combinar métricas em sinais binários ou probabilísticos.

#### Tipos de sinais

```python
class Signal:
    token: str
    signal_type: SignalType    # Enum
    strength: float            # 0.0 a 1.0
    confidence: float          # 0.0 a 1.0
    timestamp: datetime
    metadata: dict

class SignalType(Enum):
    # Growth
    DEV_MOMENTUM         # Dev activity acelerando
    SOCIAL_EXPLOSION     # Menções crescendo anormalmente
    HOLDER_SPIKE         # Holders crescendo rápido
    VOLUME_SURGE         # Volume anormal
    LIQUIDITY_GROWTH     # Liquidez aumentando
    
    # Market
    VOLUME_ANOMALY       # Volume estatisticamente anômalo
    PRICE_BREAKOUT       # Rompimento de nível
    
    # Listing
    LISTING_CANDIDATE    # Alto score de probabilidade de listing
    DEX_VOLUME_PRE_LISTING # Volume DEX crescendo sem CEX listing
    
    # Risk
    WHALE_ACCUMULATION   # Whales acumulando
    WHALE_DISTRIBUTION   # Whales vendendo
    MANIPULATION_RISK    # Sinais de manipulação
    RUGPULL_RISK         # Sinais de rugpull
    TOKEN_UNLOCK_INCOMING # Unlock de tokens em breve
    
    # Narrative
    NARRATIVE_ALIGNMENT  # Token alinhado com narrativa emergente
    ECOSYSTEM_GROWING    # Ecossistema do token crescendo
```

---

### 6.5 AI Analysis Engine

**Responsabilidade:** Usar LLMs para análise qualitativa e extração de insights.

#### `llm_provider.py` — Abstração de LLM

Suporta múltiplos provedores com fallback automático:

```
Prioridade:
1. Ollama (local, grátis) → tenta primeiro
2. Google Gemini (free tier) → fallback se Ollama indisponível
3. OpenAI GPT-4o (pago) → fallback final se configurado
```

#### `whitepaper_analyzer.py`

**Input:** URL do whitepaper (PDF) ou texto extraído  
**Output:**

```json
{
  "summary": "Resumo em linguagem simples (máx 300 palavras)",
  "problem_solved": "Problema que o projeto resolve",
  "technology": "Como funciona tecnicamente",
  "token_utility": "Para que serve o token",
  "competitors": ["Ethereum", "Solana"],
  "main_risks": ["centralização", "concorrência"],
  "innovation_score": 7.5,
  "differentiators": ["velocidade", "custo baixo"]
}
```

#### `narrative_detector.py`

**Pipeline:**
1. Coletar posts recentes do X e Reddit (últimas 48–72h)
2. Gerar embeddings com `sentence-transformers`
3. Rodar clustering (HDBSCAN ou K-Means)
4. Identificar tópicos dominantes por cluster
5. Mapear tokens mencionados em cada cluster
6. Calcular momentum do cluster (crescimento vs semana anterior)

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

Classifica cada token em categoria:

```
Layer1 | Layer2 | DeFi | AI | Gaming | Infrastructure | 
DePIN | Oracle | Privacy | Memecoin | RWA | Restaking
```

#### `summary_generator.py`

Gera explicação em linguagem leiga de por que um token pode ser interessante ou arriscado. Exemplo de output esperado:

> "A Celestia é uma blockchain que resolve um problema técnico sério: separar o armazenamento de dados da execução de transações. Isso permite que outras blockchains sejam muito mais baratas. Em 2024, o conceito de 'modular blockchain' está ganhando força, e a Celestia é a líder dessa narrativa. O risco principal é que Ethereum está desenvolvendo soluções similares."

---

### 6.6 Graph Intelligence Layer

**Responsabilidade:** Modelar o mercado cripto como rede de relações e detectar ecossistemas emergentes.

#### Estrutura do Grafo

**Nós (entidades):**
- `Token` (ex: Solana, Arbitrum)
- `Ecosystem` (ex: Ethereum Ecosystem, Solana Ecosystem)
- `Narrative` (ex: AI, DePIN, RWA)
- `Exchange` (ex: Binance, Coinbase)
- `VCFund` (ex: a16z, Multicoin)

**Arestas (relações):**
- `Token → BELONGS_TO → Ecosystem`
- `Token → ALIGNED_WITH → Narrative`
- `Token → LISTED_ON → Exchange`
- `Token → FUNDED_BY → VCFund`
- `Token → INTEGRATED_WITH → Token`
- `Token → COMPETES_WITH → Token`

#### Algoritmos

```python
# community_detector.py
# Detecta clusters (ecossistemas) de tokens relacionados
# Algoritmo: Louvain community detection

# centrality_analyzer.py
# Calcula importância de cada nó na rede
# Métricas: PageRank, Betweenness Centrality

# ecosystem_tracker.py
# Monitora crescimento de cada cluster ao longo do tempo
# Detecta ecossistemas com aceleração de crescimento
```

#### Output exemplo

```
Top Growing Ecosystems (últimos 30 dias):

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

**Responsabilidade:** Modelos treinados para detectar padrões de vencedores históricos.

#### `cycle_leader_model.py` — "Próxima Solana"

**Conceito:**
Treinar um modelo com dados de tokens que fizeram 10x+ em ciclos passados (2017–2018, 2020–2021), usando características dos projetos **antes** do pump.

**Features de entrada:**
```
market_cap_rank          # Rank no momento (ex: top 200)
volume_growth_90d        # Crescimento de volume
dev_commit_growth_90d    # Crescimento de atividade dev
social_growth_90d        # Crescimento social
holder_growth_90d        # Crescimento de holders
tvl_growth_90d           # Crescimento de TVL (se aplicável)
narrative_score          # Alinhamento com narrativa dominante
token_distribution       # Concentração de tokens
age_days                 # Idade do projeto
```

**Target:**
```
cycle_leader: bool       # Fez 10x+ no ciclo seguinte
```

**Modelo:** XGBoost ou Random Forest (bom para tabular data)

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

**Responsabilidade:** Calcular score final composto para cada token.

#### Fundamental Score (inspirado em modelo VC)

| Pilar | Peso | Métricas usadas |
|-------|------|-----------------|
| Technology | 20% | Inovação, diferenciação (análise LLM do whitepaper) |
| Tokenomics | 20% | Supply, inflação, utilidade, distribuição, unlocks |
| Adoption | 20% | TVL, usuários, transações, integrações |
| Dev Activity | 20% | Commits, contribuidores, releases |
| Narrative Fit | 20% | Alinhamento com narrativa dominante |

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

#### Risk Score (inverso — menor = mais arriscado)

```python
risk_score = (
    0.30 * rugpull_risk_inverse +
    0.25 * manipulation_risk_inverse +
    0.25 * tokenomics_risk_inverse +   # unlocks, inflação
    0.20 * whale_concentration_inverse
)
```

#### Opportunity Score (score final)

```python
opportunity_score = (
    0.30 * fundamental_score +
    0.25 * growth_score +
    0.20 * narrative_score +
    0.15 * listing_probability +
    0.10 * risk_score
) * cycle_leader_probability_boost  # multiplicador do modelo ML
```

---

### 6.9 Risk Detection Engine

#### `rugpull_detector.py`

Sinais de alerta:
- Equipe completamente anônima sem histórico verificável
- Concentração acima de 30% do supply nas top 10 wallets
- Liquidez muito baixa em relação ao market cap
- Contrato sem auditoria (checar Certik, Hacken)
- Sem código no GitHub ou repositório com pouquíssima atividade
- Lançamento recente (< 6 meses) com promessas agressivas

#### `manipulation_detector.py`

Padrões detectados:
- **Pump and dump:** Volume explode, preço sobe rapidamente, holders não aumentam proporcionalmente
- **Wash trading:** Volume alto sem mudança real de holders ou liquidez
- **Coordinated social pump:** Explosão de menções em contas de pouca credibilidade

#### `whale_tracker.py`

- Monitorar top 50 wallets de cada token
- Detectar acumulação consistente (compras graduais ao longo do tempo)
- Detectar distribuição (wallets grandes vendendo em tranche)
- Calcular `Whale Accumulation Score`

#### `tokenomics_risk.py`

- Calendário de unlocks dos próximos 90 dias
- Percentual do supply que será desbloqueado
- Taxa de inflação atual e futura
- Alert: unlock > 5% do supply nos próximos 30 dias

---

### 6.10 Alert Engine

#### Tipos de alertas

| Tipo | Urgência | Canal |
|------|----------|-------|
| `LISTING_CANDIDATE` | Alta | Telegram |
| `MEMECOIN_HYPE_DETECTED` | Alta | Telegram |
| `WHALE_ACCUMULATION` | Média | Telegram |
| `NARRATIVE_EMERGING` | Média | Telegram |
| `RUGPULL_RISK` | Alta | Telegram |
| `TOKEN_UNLOCK_SOON` | Média | Telegram |
| `DAILY_REPORT` | Baixa | Telegram |
| `MANIPULATION_DETECTED` | Alta | Telegram |

#### Formato Telegram

```
🚨 LISTING CANDIDATE DETECTED

Token: ABC
Symbol: ABC

Score de listagem: 82/100

Sinais detectados:
✅ Volume DEX cresceu 340% em 7 dias
✅ Holders cresceram 28% em 7 dias  
✅ Menções sociais +180%
✅ Integração com bridge Ethereum detectada

Probabilidade estimada: Alta
Exchanges mais prováveis: Binance, KuCoin

⚠️ Não é garantia. Faça sua própria análise.
```

---

### 6.11 Backtesting Engine

**Responsabilidade:** Testar o modelo com dados históricos para validar efetividade.

#### Como funciona

1. Carregar dados históricos de um período (ex: Jan 2019 – Jan 2020)
2. Rodar o pipeline completo de scoring **como se fosse aquela época**
3. Comparar o ranking gerado com o que realmente aconteceu no ciclo seguinte
4. Calcular métricas de performance

#### Métricas de avaliação

```
Precision@10: dos 10 mais recomendados, quantos fizeram 5x+?
Recall@50:    dos 50 que fizeram 5x+, quantos estavam no top 50?
Hit rate:     % de tokens recomendados que superaram o mercado
```

#### Interface

```bash
# Rodar backtesting no ciclo 2019–2021
cryptoai backtest --start 2019-01-01 --end 2021-01-01 --top 20

# Output esperado:
# Precision@10: 6/10 (60%)
# Tokens que teriam sido destacados: SOL, AVAX, MATIC...
```

---

### 6.12 Report Generator

#### Tipos de relatórios

**Relatório de Token (on-demand):**
- Resumo executivo em linguagem simples
- Score detalhado por pilar
- Gráfico de evolução das métricas
- Análise de risco
- Catalisadores possíveis

**Relatório Diário (automático):**
- Top 10 oportunidades do dia
- Alertas ativos
- Movimentos de narrativa

**Relatório Mensal (automático):**
- Análise profunda top 20
- Revisão de ciclo
- Performance do modelo (acertos/erros)

---

### 6.13 Dashboard (Frontend React)

#### Páginas

**Home — Rankings**
- Tabela com Top Opportunities, ordenável por qualquer score
- Filtros: categoria, market cap range, narrativa
- Chip de alertas ativos
- Mini gráfico de score nos últimos 30 dias por token

**Token Detail**
- Score breakdown visual (radar chart dos 5 pilares)
- Métricas de mercado com gráficos temporais
- Dev activity timeline
- Social trend
- Análise em linguagem simples (gerada por IA)
- Alertas ativos para esse token
- Botão "Gerar Relatório PDF"

**Narratives**
- Cards de narrativas emergentes
- Momentum de cada narrativa (gráfico)
- Tokens associados a cada narrativa

**Ecosystem Graph**
- Visualização interativa do Knowledge Graph
- Clique em nó → detalhes
- Filtro por ecossistema

**Backtesting**
- Interface para configurar e rodar backtests
- Visualização dos resultados

**Alerts**
- Feed de alertas históricos
- Configuração de alertas

---

### 6.14 CLI

```bash
# Comandos principais

cryptoai scan                          # Roda análise completa
cryptoai top [--n 20]                  # Lista top N oportunidades
cryptoai report <SYMBOL>               # Relatório detalhado de um token
cryptoai narrative                     # Narrativas emergentes
cryptoai alerts                        # Alertas ativos
cryptoai backtest [--start] [--end]    # Rodar backtesting
cryptoai update                        # Força atualização dos dados
cryptoai config                        # Mostrar configuração atual
```

---

## 7. Banco de Dados — Schema

```sql
-- Tokens cadastrados
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

-- Dados de mercado (snapshot diário)
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

-- Atividade de desenvolvimento
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

-- Dados sociais
CREATE TABLE social_data (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    twitter_mentions_24h INTEGER,
    twitter_sentiment    DECIMAL(4,3),    -- -1.0 a 1.0
    reddit_posts_7d      INTEGER,
    reddit_subscribers   INTEGER,
    reddit_growth_pct    DECIMAL(10,4),
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Holders e liquidez
CREATE TABLE holder_data (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    holder_count    INTEGER,
    top10_pct       DECIMAL(5,2),        -- % do supply nas top 10 wallets
    top50_pct       DECIMAL(5,2),
    dex_volume_24h  BIGINT,
    dex_liquidity   BIGINT,
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Scores calculados
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

-- Sinais gerados
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

-- Alertas disparados
CREATE TABLE alerts (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    alert_type      VARCHAR(50),
    message         TEXT,
    metadata        JSONB,
    sent_telegram   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Narrativas detectadas
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

-- Análises IA (cache)
CREATE TABLE ai_analyses (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    analysis_type   VARCHAR(50),          -- whitepaper, summary, classification
    content         TEXT,
    model_used      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Dados históricos para backtesting
CREATE TABLE historical_snapshots (
    id              SERIAL PRIMARY KEY,
    token_id        INTEGER REFERENCES tokens(id),
    snapshot_data   JSONB,               -- snapshot completo serializado
    snapshot_date   DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 8. Integrações Externas e APIs

| Serviço | Uso | Free Tier | Endpoint base |
|---------|-----|-----------|---------------|
| CoinGecko | Market data principal | 30 req/min | `https://api.coingecko.com/api/v3` |
| CoinMarketCap | Market data complementar | 333 req/dia | `https://pro-api.coinmarketcap.com/v1` |
| DefiLlama | TVL, DeFi data | Sem limite | `https://api.llama.fi` |
| GitHub | Dev activity | 60 req/h (unauth), 5000 (auth) | `https://api.github.com` |
| Twitter/X API | Social data | Limitado (plano Basic) | `https://api.twitter.com/2` |
| Reddit API | Social data | Gratuito | `https://www.reddit.com/r/{sub}/new.json` |
| Telegram Bot API | Alertas | Gratuito | `https://api.telegram.org` |
| Gemini API | LLM | Free tier | `https://generativelanguage.googleapis.com` |
| Ollama | LLM local | Gratuito | `http://localhost:11434` |

---

## 9. Sistema de Scoring — Detalhamento

### Fórmula completa

```python
def calculate_opportunity_score(token: Token) -> float:
    
    # Pilar 1: Fundamentos (30%)
    fundamental = (
        technology_score * 0.20 +
        tokenomics_score * 0.20 +
        adoption_score   * 0.20 +
        dev_score        * 0.20 +
        narrative_fit    * 0.20
    )
    
    # Pilar 2: Crescimento (25%)
    growth = (
        dev_commit_growth    * 0.25 +
        social_growth        * 0.20 +
        holder_growth        * 0.20 +
        volume_growth        * 0.20 +
        liquidity_growth     * 0.15
    )
    
    # Pilar 3: Narrativa (20%)
    narrative = narrative_momentum_score
    
    # Pilar 4: Probabilidade de listing (15%)
    listing = listing_probability_score
    
    # Pilar 5: Ajuste de risco (10%)
    risk_adjustment = 1.0 - (risk_score * 0.5)  # risco alto penaliza
    
    base_score = (
        fundamental  * 0.30 +
        growth       * 0.25 +
        narrative    * 0.20 +
        listing      * 0.15 +
        risk_adjustment * 0.10
    )
    
    # Boost pelo modelo ML
    cycle_boost = 1.0 + (cycle_leader_probability * 0.20)
    
    return min(base_score * cycle_boost, 10.0)  # cap em 10.0
```

---

## 10. Roadmap de Desenvolvimento

### Fase 1 — MVP Funcional (2–3 semanas)

**Objetivo:** Sistema rodando com dados reais, CLI funcional, ranking básico.

- [ ] Setup do projeto (Docker, PostgreSQL, FastAPI, estrutura de pastas)
- [ ] `CoinGeckoCollector` funcionando
- [ ] Schema do banco + migrations Alembic
- [ ] `MarketProcessor` com métricas básicas
- [ ] `FundamentalScorer` simplificado (sem LLM ainda)
- [ ] CLI com `cryptoai top` e `cryptoai report`
- [ ] Scheduler rodando coleta diária

**Entregável:** `cryptoai top 20` mostra ranking com dados reais.

---

### Fase 2 — Dev Activity + Social (1–2 semanas)

- [ ] `GitHubCollector` funcionando
- [ ] `SocialCollector` (Reddit primeiro, X depois)
- [ ] `DevProcessor` e `SocialProcessor`
- [ ] `GrowthScorer` com métricas reais
- [ ] `AnomalyDetector` básico

**Entregável:** Score inclui dev activity e crescimento social.

---

### Fase 3 — IA e Narrativas (2 semanas)

- [ ] `LLMProvider` com suporte a Ollama e Gemini
- [ ] `WhitepaperAnalyzer`
- [ ] `NarrativeDetector` com embeddings
- [ ] `ProjectClassifier`
- [ ] `SummaryGenerator`

**Entregável:** `cryptoai report SOL` gera análise completa com texto em linguagem simples.

---

### Fase 4 — Listing Radar + Risk (1–2 semanas)

- [ ] `ExchangeMonitor` funcionando
- [ ] `ListingSignals` e `ListingPredictor`
- [ ] `RugpullDetector`
- [ ] `ManipulationDetector`
- [ ] `WhaleTracker`
- [ ] `TokenomicsRisk` com calendário de unlocks

**Entregável:** Alertas de listing e risco funcionando.

---

### Fase 5 — Telegram + Relatórios (1 semana)

- [ ] `TelegramBot` configurado
- [ ] Alertas automáticos funcionando
- [ ] `MarkdownGenerator` para relatórios
- [ ] `PDFGenerator`

**Entregável:** Alertas chegando no Telegram. Relatórios exportáveis.

---

### Fase 6 — Dashboard React (2–3 semanas)

- [ ] Setup React + Vite + TailwindCSS + shadcn/ui
- [ ] Página Home com ranking
- [ ] Página Token Detail
- [ ] Página Narratives
- [ ] Conexão com API FastAPI

**Entregável:** Dashboard visual funcionando localmente.

---

### Fase 7 — ML + Graph + Backtesting (3–4 semanas)

- [ ] `CycleLeaderModel` com dados históricos
- [ ] `GraphBuilder` e `CommunityDetector`
- [ ] `BacktestingEngine`
- [ ] Integração Graph visual no frontend (D3.js)
- [ ] Página Backtesting no frontend

**Entregável:** Score de "próxima Solana". Backtesting validado. Knowledge Graph visual.

---

## 11. Configurações e Variáveis de Ambiente

```env
# .env.example

# ===== DATABASE =====
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/cryptoai
REDIS_URL=redis://redis:6379

# ===== API KEYS =====
COINGECKO_API_KEY=           # Opcional (melhora rate limit)
COINMARKETCAP_API_KEY=       # Obrigatório para CMC
GITHUB_TOKEN=                # Obrigatório para dev activity
TWITTER_BEARER_TOKEN=        # Opcional (plano pago)
GEMINI_API_KEY=              # Para LLM Gemini
OPENAI_API_KEY=              # Opcional, fallback pago
TELEGRAM_BOT_TOKEN=          # Para alertas
TELEGRAM_CHAT_ID=            # Seu chat ID

# ===== LLM PROVIDER =====
LLM_PRIMARY=ollama            # ollama | gemini | openai
LLM_FALLBACK=gemini
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2

# ===== ANÁLISE =====
TOKENS_TO_ANALYZE=300        # Número de tokens analisados
ANALYSIS_CURRENCY=USD
COINGECKO_VS_CURRENCY=usd

# ===== SCHEDULER =====
REALTIME_INTERVAL_MINUTES=30
DAILY_RUN_HOUR=6             # Hora da coleta diária (UTC)
WEEKLY_RUN_DAY=monday
MONTHLY_RUN_DAY=1

# ===== ALERTAS =====
ALERT_LISTING_THRESHOLD=0.70         # Score mínimo para alertar listing
ALERT_WHALE_ACCUMULATION_THRESHOLD=7.0
ALERT_MEMECOIN_SOCIAL_GROWTH=500     # % crescimento em 48h

# ===== FRONTEND =====
VITE_API_BASE_URL=http://localhost:8000
```

---

## 12. Docker e Infraestrutura

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
    # GPU support (opcional):
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

## 13. Exemplos de Output Esperado

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
8   TAO     Bittensor      7.1   6.8    8.9    9.3   high   ⚠ alta concentração
9   JUP     Jupiter        7.0   7.2    7.8    7.4   low    ↑volume DEX
10  EIGEN   EigenLayer     6.9   7.5    6.8    8.0   med    restaking narr.
```

### CLI: `cryptoai report TIA`

```
══════════════════════════════════════════
CELESTIA (TIA) — Relatório Completo
Gerado em: 2025-03-10 | Score: 8.4/10
══════════════════════════════════════════

📋 RESUMO (gerado por IA)
─────────────────────────
A Celestia resolve um problema técnico fundamental: blockchains 
tradicionais precisam fazer tudo ao mesmo tempo (executar, validar, 
armazenar). A Celestia faz apenas uma coisa — armazenar dados — e 
faz isso muito bem. Isso permite que outras blockchains (como rollups 
do Ethereum) usem a Celestia como base, ficando muito mais baratas 
e rápidas.

O conceito de "blockchain modular" está crescendo em 2025, e a 
Celestia é a principal aposta nessa narrativa.

📊 SCORES DETALHADOS
────────────────────
Technology:    ████████░░  8.2/10
Tokenomics:    ███████░░░  7.5/10
Adoption:      ███████░░░  7.8/10
Dev Activity:  █████████░  8.9/10
Narrative:     █████████░  9.0/10

Overall:       ████████░░  8.4/10

📈 CRESCIMENTO (30 dias)
────────────────────────
Dev commits:   +34%  ↑↑
Social:        +28%  ↑
Holders:       +15%  ↑
Volume:        +22%  ↑
TVL:           +41%  ↑↑

⚠ RISCOS
─────────
• Ethereum desenvolvendo soluções similares (EIP-4844)
• Token com unlock de 8% do supply em Junho/2025
• Dependência de adoção por outros projetos (B2B)

🎯 CATALISADORES POSSÍVEIS
──────────────────────────
• Crescimento de rollups usando Celestia como DA layer
• Parcerias com projetos Ethereum
• Possível listagem na Coinbase (probabilidade: 58%)

🔗 LINKS
─────────
Website:    https://celestia.org
GitHub:     https://github.com/celestiaorg
Whitepaper: https://celestia.org/whitepaper
```

### Alerta Telegram — Listing Candidate

```
🚨 LISTING CANDIDATE DETECTED

🪙 Token: PUMP
Network: Solana

📊 Score de listagem: 84/100

Sinais detectados:
✅ Volume DEX: +420% em 7 dias  
✅ Holders: +35% em 7 dias
✅ Menções Twitter: +890% em 48h
✅ Liquidez crescendo consistentemente
⚠️ Classificado como: Memecoin

Exchanges mais prováveis: KuCoin, Bybit

Ação recomendada: MONITORAR
⚠️ Análise automatizada. Faça sua própria pesquisa.

[Ver detalhes no dashboard]
```

---

## 14. Decisões de Design e Justificativas

| Decisão | Alternativa considerada | Motivo da escolha |
|---------|------------------------|-------------------|
| PostgreSQL | MongoDB | Dados relacionais + suporte a JSONB para flexibilidade |
| APScheduler | Celery + Beat | Menor complexidade para uso single-user |
| XGBoost para ML | Deep Learning | Melhor com tabular data de tamanho médio |
| NetworkX para grafo | Neo4j | Sem overhead de novo serviço na Fase 1; migrar depois |
| LangChain | Chamadas diretas à API | Facilita troca de provider LLM e chains complexas |
| Ollama como LLM primário | Apenas APIs pagas | Custo zero, privacidade total, sem limite |
| sentence-transformers | OpenAI embeddings | Gratuito, roda localmente, qualidade suficiente |
| React | Streamlit | Mais profissional, melhor UX, reutilizável |
| FastAPI | Flask | Async nativo, tipagem, auto-documentação OpenAPI |

---

*Documento gerado para uso com GitHub Copilot + Claude Sonnet 4.6*  
*Última atualização: 2025-03-10*  
*Status: Pronto para desenvolvimento — Fase 1*
