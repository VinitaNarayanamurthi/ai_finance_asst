# AI Finance Assistant

A production-quality, multi-agent AI system for financial analysis built with LangGraph, LangChain, and OpenAI. The assistant combines Retrieval-Augmented Generation (RAG), real-time market data, portfolio analytics, and financial news into a unified Streamlit web application.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Module Breakdown](#module-breakdown)
  - [Agent Module](#agent-module)
  - [App Module](#app-module)
  - [RAG Module](#rag-module)
  - [Tools Module](#tools-module)
  - [Database Module](#database-module)
- [LangGraph Orchestration](#langgraph-orchestration)
- [Guardrails & Compliance Filtering](#guardrails--compliance-filtering)
- [Error Handling & Fallback Mechanisms](#error-handling--fallback-mechanisms)
- [Conversational Memory](#conversational-memory)
- [Vector Indexing & RAG with Chroma DB](#vector-indexing--rag-with-chroma-db)
- [Tech Stack & Dependencies](#tech-stack--dependencies)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Docker Deployment](#docker-deployment)
- [Usage Guide](#usage-guide)
- [Data Flow](#data-flow)
- [API Integrations](#api-integrations)
- [Excel Portfolio Format](#excel-portfolio-format)

---

## Overview

The AI Finance Assistant is a capstone project demonstrating advanced agentic AI patterns in the financial domain. It orchestrates four specialized agents using LangGraph — each independently capable of handling a different class of financial query — plus a compliance guardrail layer and an intelligent planner that routes user queries to the right agent(s) automatically.

**Two operating modes are available:**

| Mode | Description |
|------|-------------|
| **Mode 1 — Direct Agents** | Four separate tabs; user selects which agent to invoke |
| **Mode 2 — Orchestrator** | Single chat interface; LLM planner routes automatically |

---

## Architecture

```
User Query
     │
     ▼
┌─────────────────────────────────────────┐
│           Guardrail Layer               │
│  (Compliance check: SAFE / UNSAFE /     │
│   NEEDS_DISCLAIMER via LLM + patterns)  │
└──────────┬──────────────────────────────┘
           │ SAFE
           ▼
┌─────────────────────────────────────────┐
│         Planner / Router Node           │
│  Outputs JSON array of agents to run:   │
│  ["qa", "portfolio", "market", "news"]  │
└──┬──────┬──────────┬──────────┬─────────┘
   │      │          │          │
   ▼      ▼          ▼          ▼
 [QA]  [Portfolio] [Market]  [News]
  RAG   Excel+Charts  Alpha    Alpha
        Analysis    Vantage  Vantage
                    Stocks    News
   │      │          │          │
   └──────┴──────────┴──────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  Aggregator Node  │
        │ Single → direct  │
        │ Multi  → LLM     │
        │         synthesis│
        └──────────────────┘
                  │
                  ▼
           Final Response
```

All agents are wrapped with retry logic (3 retries, exponential backoff) and isolated error handling so a failure in one agent does not block others.

---

## Features

- **Finance Q&A with RAG** — Answers grounded in your own uploaded PDF documents with source citations (filename + page number)
- **Portfolio Analysis** — Reads multi-sheet Excel files; computes allocation, gain/loss, diversification (HHI), drawdown, volatility, and generates 7 charts
- **Real-Time Market Data** — Live quotes, intraday/daily price series, and full company fundamentals via Alpha Vantage
- **News & Sentiment** — Latest financial headlines with per-article sentiment scores and relevance rankings
- **Compliance Guardrails** — Blocks queries involving guaranteed returns, tax evasion, insider trading, and other financial misconduct
- **Multi-Agent Orchestration** — LangGraph graph transparently routes queries and synthesizes multi-agent responses
- **User Profiles** — Sidebar stores name, risk tolerance, and investment goals that are prepended to every agent query
- **Persistent Vector Store** — Chroma DB is saved to disk and survives application restarts
- **Docker Support** — Single `docker compose up` brings up the full application

---

## Project Structure

```
ai_finance_asst/
│
├── agent/                          # All AI agents
│   ├── orchestrator.py             # LangGraph multi-agent graph
│   ├── finance_qa_agent.py         # RAG-based Q&A agent
│   ├── portfolio_agent.py          # Excel portfolio analysis agent
│   ├── market_analysis_agent.py    # Real-time market data agent
│   ├── news_synthesizer_agent.py   # News & sentiment agent
│   └── __init__.py
│
├── app/
│   ├── streamlit_app.py            # Streamlit web UI (Mode 1 & 2)
│   └── __init__.py
│
├── rag/
│   ├── vector_store_embedding.py   # Chroma vector DB management
│   └── loader_preprocessor.py      # PDF loading, cleaning & chunking
│
├── tools/
│   ├── portfolio_analyzer.py       # Excel analysis + matplotlib charts
│   ├── sample_portfolio.xlsx       # Sample portfolio for demo
│   └── __init__.py
│
├── database/                       # Optional PostgreSQL integration
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── database.py                 # Engine & session factory
│   ├── config.py                   # DB config & .env loading
│   ├── crud.py                     # CRUD operations
│   └── main.py                     # Example DB usage
│
├── docs/                           # Drop financial PDF files here for RAG
├── chroma_langchain_db/            # Auto-created; persisted vector store
├── analysis_output/                # Auto-created; generated chart PNGs
│
├── .env                            # API keys — never commit this file
├── .gitignore
├── requirements.txt                # Full dependency list
├── requirements_new.txt            # Minimal install subset
├── Dockerfile
├── docker-compose.yml
└── DOCKER_README.md
```

---

## Module Breakdown

### Agent Module

#### `agent/orchestrator.py`

The central LangGraph workflow. Defines a `FinancialState` TypedDict shared across all nodes:

| Field | Purpose |
|-------|---------|
| `user_input` | Raw query from user |
| `chat_history` | Prior conversation turns |
| `agents_to_run` | List of agent names chosen by planner |
| `blocked` | Set to `True` if guardrail fires |
| `guardrail_reason` | Human-readable block reason |
| `qa_response` | Output from Finance Q&A agent |
| `portfolio_analysis` | Output from Portfolio agent |
| `market_analysis` | Output from Market agent |
| `news_summary` | Output from News agent |
| `final_response` | Synthesized answer |
| `errors` | Accumulated error messages |

**Graph nodes:**

- **`guardrail_node`** — Runs pattern matching (e.g., "guarantee profit", "insider trading") then falls back to LLM classification (`SAFE` / `UNSAFE` / `NEEDS_DISCLAIMER`).
- **`planner_node`** — Parses user intent and returns a JSON array such as `["market", "news"]` following routing rules:
  - `"qa"` → general finance concepts (no tickers)
  - `"portfolio"` → user's own holdings
  - `"market"` → specific company / ticker data
  - `"news"` → financial news & sentiment
- **Agent nodes** (`qa_node`, `portfolio_node`, `market_node`, `news_node`) — Thin wrappers around each agent executor with retry logic.
- **`aggregator_node`** — Returns single-agent output directly; uses GPT-4o-mini to merge multiple outputs coherently.

**Graph topology:**
```
guardrail ──(blocked)──► END
          ──(allowed)──► planner ──► [agents in parallel] ──► aggregator ──► END
```

Model: `gpt-4o-mini`, `temperature=0`

---

#### `agent/finance_qa_agent.py`

Answers general finance questions using documents stored in the vector database.

- Dynamically imports `rag/vector_store_embedding.py` at runtime.
- The `finance_qa_tool` LangChain tool retrieves the top-2 most relevant document chunks from Chroma and returns them with source metadata.
- The agent is instructed to always cite `(source file, page number)` in its response.
- Gracefully degrades if the RAG module or vector store is unavailable.

---

#### `agent/portfolio_agent.py`

Analyses a user's portfolio from an Excel file.

- Dynamically imports `tools/portfolio_analyzer.py`.
- Searches for a portfolio file in `tools/` if no path is supplied by the user.
- The `portfolio_analysis_tool` calls `analyze_portfolio()` and returns the analysis dict plus file paths to generated charts.
- The agent system prompt enforces tool use; chart paths are included verbatim in responses so Streamlit can display them.

---

#### `agent/market_analysis_agent.py`

Fetches real-time and historical market data via Alpha Vantage.

| Tool | Alpha Vantage Function | What it returns |
|------|----------------------|-----------------|
| `get_stock_quote` | `GLOBAL_QUOTE` | Price, change, volume, trading day |
| `get_stock_intraday` | `TIME_SERIES_INTRADAY` | OHLCV at 1/5/15/30/60-min intervals |
| `get_stock_daily` | `TIME_SERIES_DAILY` | Last 100 days of daily OHLCV |
| `search_symbol` | `SYMBOL_SEARCH` | Ticker lookup by company name |
| `get_company_overview` | `OVERVIEW` | P/E, EPS, market cap, sector, beta, 52-week range, dividends, ROE, ROA |

Uses `ALPHA_VANTAGE_API_KEY` from `.env`; falls back to `"demo"` key for limited testing.

---

#### `agent/news_synthesizer_agent.py`

Aggregates financial news and sentiment scores from Alpha Vantage.

| Tool | Purpose |
|------|---------|
| `get_news_sentiment` | Latest news with overall sentiment for given tickers/topics |
| `get_market_news_feed` | General market news by topic category |
| `get_stock_news` | Stock-specific news with per-ticker sentiment breakdown |
| `get_sector_news` | Sector news (technology, finance, energy, real_estate, …) |

Each returned article includes title, source, publish time, 250-character summary, overall sentiment label & score, and a URL.

---

### App Module

#### `app/streamlit_app.py`

Single-file Streamlit application supporting both operating modes.

**Sidebar controls:**
- User name, risk tolerance (Conservative / Moderate / Aggressive), investment goals
- `.xlsx` portfolio file uploader
- History clear button

**Mode 1 — Four tabs:**

| Tab | Agent | Extra UI |
|-----|-------|----------|
| Finance Q&A | `finance_qa_agent` | Suggested question buttons |
| Portfolio Analysis | `portfolio_agent` | Chart images rendered below response |
| Market Analysis | `market_analysis_agent` | Sample tickers as quick-start buttons |
| News Synthesizer | `news_synthesizer_agent` | Sample topics as quick-start buttons |

**Mode 2 — Orchestrator chat:**
- Single text input feeds `orchestrator.py`
- Each response shows which agents were invoked
- Portfolio charts rendered inline when the portfolio agent runs
- Full conversation history maintained across turns

**Key helpers:**
- `_build_input()` — Prepends user profile + portfolio file path to every query
- `_run_agent()` — Invokes an executor with accumulated history
- `_render_chat_history()` — Replays prior turns
- `_render_portfolio_charts()` — Displays generated PNG files

---

### RAG Module

#### `rag/loader_preprocessor.py`

**`DocumentProcessor`** class:

| Parameter | Default |
|-----------|---------|
| `docs_path` | `{project_root}/docs/` |
| Chunk size | 1 000 characters |
| Chunk overlap | 200 characters |
| Splitter | `RecursiveCharacterTextSplitter` |

- `load_and_process_pdfs()` — Discovers all PDFs in `docs/`, loads with `PyPDFLoader`, cleans text (removes spurious newlines, fixes hyphenations), splits into chunks, and attaches metadata (source filename, page number, chunk index, total chunks).
- `create_contextual_embedding(chunk)` — Formats each chunk as `"Source: {file} Page: {page} Chunk: {i}/{total} Content: {text}"` for richer retrieval.

#### `rag/vector_store_embedding.py`

**`EmbeddingProcessor`** class:

| Parameter | Value |
|-----------|-------|
| Persist directory | `{project_root}/chroma_langchain_db/` |
| Collection name | `financial_documents` |
| Embedding model | `text-embedding-3-large` (OpenAI) |
| Retrieval k | 2 |

- `create_embeddings()` — Builds the vector store from scratch; assigns sequential chunk IDs.
- `retrieve_context(query)` — Runs cosine similarity search and returns formatted context string plus raw `Document` objects with source metadata.
- The persist directory survives application restarts; call `create_embeddings()` only when new PDFs are added.

---

### Tools Module

#### `tools/portfolio_analyzer.py`

The core analytics engine. Entry point: `analyze_portfolio(file_path, output_dir)`.

**Metrics computed:**

*Holdings level*
- Current value, portfolio weight, gain/loss ($ and %)
- Top 5 and bottom 5 performers

*Diversification*
- Herfindahl-Hirschman Index (HHI) — 0 = perfectly diversified, 1 = fully concentrated
- Effective number of holdings
- Top-5 concentration %
- Largest holding weight & name

*Portfolio level*
- Total value, total invested, total return %
- Max drawdown, daily volatility, annualised volatility (from snapshot sheet)

*Transactions* (if sheet present)
- Buy / sell counts, date range, most-traded tickers, unique ticker count

**Charts generated (7 PNG files):**

| # | Chart | Type |
|---|-------|------|
| 1 | Holdings allocation | Pie (small holdings → "Others") |
| 2 | Sector allocation | Pie |
| 3 | Asset type allocation | Pie |
| 4 | Gain / loss per holding | Bar |
| 5 | Top performers | Horizontal bar |
| 6 | Portfolio value over time | Line |
| 7 | Diversification summary | HHI gauge + top-5 bar |

---

### Database Module

Optional PostgreSQL backend — not required for core functionality.

**Schema:** `finance_asst`

| Table | Key columns |
|-------|-------------|
| `users` | user_id, email, name, risk_profile, preferences (JSONB) |
| `portfolios` | id, user_id (FK), name |
| `holdings` | id, portfolio_id (FK), symbol, quantity, average_cost |
| `transactions` | id, portfolio_id (FK), symbol, type, quantity, price, date |
| `market_data` | symbol (PK), current_price, day_change_percent, beta |
| `portfolio_snapshots` | id, portfolio_id (FK), snapshot_date, total_value |

CRUD helpers in `database/crud.py` cover users, portfolios, holdings, transactions, market data, and computed portfolio value.

---

## LangGraph Orchestration

LangGraph provides the graph-based execution engine that replaces a simple linear chain with a **stateful, conditional workflow**. Every agent interaction flows through a typed state object (`FinancialState`) that is mutated by each node and inspected to decide the next step.

### Why LangGraph?

| Requirement | How LangGraph addresses it |
|-------------|---------------------------|
| Route to different agents depending on intent | Conditional edges from the planner node |
| Run multiple agents in parallel | Fan-out from planner to agent nodes |
| Aggregate multiple agent outputs | Dedicated aggregator node at the end |
| Enforce compliance before any agent runs | `guardrail_node` runs first; `blocked` flag short-circuits the graph |
| Retry failed agent calls transparently | Each node wraps its executor with `tenacity` retry logic |

### Graph Definition

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(FinancialState)

# Nodes
workflow.add_node("guardrail",   guardrail_node)
workflow.add_node("planner",     planner_node)
workflow.add_node("qa",          qa_node)
workflow.add_node("portfolio",   portfolio_node)
workflow.add_node("market",      market_node)
workflow.add_node("news",        news_node)
workflow.add_node("aggregator",  aggregator_node)

# Entry point
workflow.set_entry_point("guardrail")

# Conditional routing from guardrail
workflow.add_conditional_edges(
    "guardrail",
    lambda s: "blocked" if s["blocked"] else "allowed",
    {"blocked": END, "allowed": "planner"},
)

# Dynamic routing from planner to agents
workflow.add_conditional_edges("planner", route_to_agents)

# All agents feed into aggregator
for agent in ["qa", "portfolio", "market", "news"]:
    workflow.add_edge(agent, "aggregator")

workflow.add_edge("aggregator", END)

orchestrator_app = workflow.compile()
```

### State Flow

```
FinancialState (shared across all nodes)
├── user_input          ← set by caller
├── chat_history        ← set by caller; used by planner & aggregator
├── blocked             ← set by guardrail_node
├── guardrail_reason    ← set by guardrail_node
├── agents_to_run       ← set by planner_node  ["qa", "market"]
├── qa_response         ← set by qa_node
├── market_analysis     ← set by market_node
├── portfolio_analysis  ← set by portfolio_node
├── news_summary        ← set by news_node
├── final_response      ← set by aggregator_node
└── errors              ← appended by any node that catches an exception
```

---

## Guardrails & Compliance Filtering

Every query passes through a two-stage compliance check **before** reaching any agent. This ensures the system never assists with unethical or illegal financial activity.

### Stage 1 — Pattern Matching (fast path)

A set of forbidden keyword/phrase patterns is checked first. If any match, the query is immediately blocked without calling the LLM:

```
"guarantee profit"     "guaranteed return"    "insider trading"
"tax evasion"          "money laundering"      "pump and dump"
"manipulate stock"     "front running"
```

### Stage 2 — LLM Classification (nuanced path)

Queries that pass pattern matching are sent to GPT-4o-mini with a structured prompt that evaluates the full conversation history and returns one of three verdicts:

| Verdict | Meaning | Action |
|---------|---------|--------|
| `SAFE` | Legitimate financial question | Proceeds to planner |
| `UNSAFE` | Harmful / illegal request | Blocked; reason returned to user |
| `NEEDS_DISCLAIMER` | Risky but legal (e.g., leveraged ETFs) | Allowed with a prepended disclaimer |

The LLM evaluator receives the **full chat history**, not just the latest message, so it can catch unsafe intent spread across multiple turns (e.g., a follow-up that escalates a borderline earlier question).

### Example

```
User: "How do I guarantee 30% monthly returns?"

→ Pattern match: "guarantee" detected
→ State: blocked = True
         guardrail_reason = "Query involves guaranteed returns, which
                             violates financial compliance standards."
→ Graph: routes directly to END without calling any agent
→ Response: compliance message returned to user
```

---

## Error Handling & Fallback Mechanisms

The system is built for resilience. Failures at any layer are caught, logged, and gracefully degraded rather than surfaced as raw exceptions.

### Agent-Level Retry (tenacity)

Every agent executor node is wrapped with `tenacity`:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=False,
)
def run_with_retry(executor, inputs):
    return executor.invoke(inputs)
```

- **3 attempts** total before giving up
- **Exponential backoff**: waits 2 s → 4 s → 8 s between retries
- Transient API errors (network timeout, rate limit 429) are handled transparently

### Per-Agent Isolation

Each agent node catches its own exceptions and writes a human-readable error string into `FinancialState["errors"]` rather than crashing the graph. The other agents continue executing normally. The aggregator includes error messages in its final synthesis so the user knows which sub-result is missing.

```python
def portfolio_node(state):
    try:
        result = run_with_retry(portfolio_executor, {...})
        return {"portfolio_analysis": result["output"]}
    except Exception as e:
        return {"errors": [f"Portfolio agent failed: {str(e)}"]}
```

### RAG Fallback

If the Chroma vector store has not been initialised (no PDFs ingested yet), `finance_qa_agent.py` catches the `ImportError` / missing-collection error at runtime and returns a descriptive fallback message instead of crashing:

```
"Vector store not available. Please add PDF documents to the docs/
 directory and run create_embeddings() to initialise the RAG index."
```

### Dynamic Module Loading

Both `portfolio_agent.py` and `finance_qa_agent.py` load their heavy dependencies (`portfolio_analyzer`, `EmbeddingProcessor`) at call time using `importlib.util`. If a module file is missing, the agent returns an informative error message rather than failing at import time — allowing the rest of the app to start normally.

### Alpha Vantage API Fallback

If the configured API key is invalid or the free-tier rate limit is hit, the market and news agents catch the `requests` error and return a structured message indicating the data is temporarily unavailable, along with the raw HTTP status code for debugging.

---

## Conversational Memory

The assistant maintains conversation history across turns so agents can understand follow-up questions in context.

### How History Is Stored

Session state is managed by Streamlit's `st.session_state`. Separate history lists are maintained for each interface:

| Key | Scope | Contents |
|-----|-------|---------|
| `qa_history` | Finance Q&A tab | List of `(role, content)` tuples |
| `portfolio_history` | Portfolio tab | List of `(role, content)` tuples |
| `market_history` | Market tab | List of `(role, content)` tuples |
| `news_history` | News tab | List of `(role, content)` tuples |
| `orchestrator_history` | Orchestrator mode | List of `(role, content, agents_used)` tuples |

### How History Is Used

Before every agent call, the relevant history list is serialised into a formatted string and prepended to the query:

```python
def _build_input(query, history, user_profile, portfolio_path=None):
    context = f"User Profile: {user_profile}\n"
    if portfolio_path:
        context += f"Portfolio File: {portfolio_path}\n"
    if history:
        context += "Conversation History:\n"
        for role, content in history:
            context += f"  {role}: {content}\n"
    return context + f"\nCurrent Question: {query}"
```

This means agents can correctly answer questions such as:

```
Turn 1: "What is AAPL's P/E ratio?"
Turn 2: "How does that compare to its sector average?"
         ↑ agent knows "that" refers to AAPL's P/E from Turn 1
```

### History in the Orchestrator

The orchestrator's `FinancialState["chat_history"]` is passed to the **planner** and **guardrail** nodes. The planner uses history to avoid re-routing the same sub-question twice in a multi-turn conversation. The guardrail evaluates history to detect gradually escalating unsafe intent.

### Clearing History

The sidebar **Clear History** button resets only the active mode's history — it does not clear history for the other mode — so users can start fresh on one interface without losing the other.

---

## Vector Indexing & RAG with Chroma DB

The Finance Q&A agent grounds its answers in your own document library using a full RAG pipeline backed by Chroma DB.

### Indexing Pipeline

```
PDF files in docs/
       │
       ▼
  PyPDFLoader
  (one Document per page)
       │
       ▼
  clean_text()
  • Strip inter-paragraph newlines
  • Fix hyphenated line-breaks
  • Collapse whitespace
       │
       ▼
  RecursiveCharacterTextSplitter
  chunk_size=1000, chunk_overlap=200
       │
       ▼
  create_contextual_embedding()
  "Source: {file} Page: {page} Chunk: {i}/{total} Content: {text}"
       │
       ▼
  OpenAI text-embedding-3-large
  (1536-dimensional vectors)
       │
       ▼
  Chroma.add_documents()
  collection: "financial_documents"
  persist_dir: chroma_langchain_db/
```

### Retrieval Pipeline

```
User question
       │
       ▼
  OpenAI text-embedding-3-large
  (embed the question)
       │
       ▼
  Chroma.similarity_search(query, k=2)
  (cosine similarity over stored vectors)
       │
       ▼
  Top-2 chunks returned with metadata:
  • source (filename)
  • page (page number)
  • chunk_index / total_chunks
       │
       ▼
  finance_qa_tool formats context string
       │
       ▼
  GPT-4o-mini synthesises answer
  with inline source citations
```

### Chroma DB Details

| Setting | Value |
|---------|-------|
| Persist directory | `{project_root}/chroma_langchain_db/` |
| Collection | `financial_documents` |
| Embedding model | `text-embedding-3-large` (OpenAI) |
| Similarity metric | Cosine |
| k (top results) | 2 |
| Chunk size | 1 000 chars |
| Chunk overlap | 200 chars |

### Initialising the Index

Run once after adding PDFs to `docs/`:

```python
from rag.vector_store_embedding import EmbeddingProcessor

ep = EmbeddingProcessor()
ep.create_embeddings()   # writes to chroma_langchain_db/
```

On subsequent app starts the persisted collection is loaded automatically — no re-indexing required.

### Adding New Documents

1. Copy new PDF files into `docs/`.
2. Call `ep.create_embeddings()` again (safe to re-run; replaces the collection).
3. Restart the Streamlit app (or the app picks up the new index on next Q&A query).

### Source Citations

Every answer from the Finance Q&A agent includes citations in the form:

```
According to the document, [answer content] ...

Sources:
  • annual_report_2024.pdf — Page 12
  • investment_guide.pdf — Page 7
```

The source file name and page number are extracted from Chroma document metadata and injected into the agent prompt, so the LLM always has the grounding information it needs.

---

## Tech Stack & Dependencies

### Core AI / ML

| Package | Version | Role |
|---------|---------|------|
| `langchain` | 0.3.27 | LLM framework & tools |
| `langgraph` | 1.0.1 | Multi-agent graph orchestration |
| `langchain-openai` | 0.3.35 | OpenAI LLM & embedding integration |
| `langchain-chroma` | 0.2.6 | Chroma vector store integration |
| `langchain-community` | 0.3.31 | PDF loaders, document utilities |
| `openai` | 2.21.0 | API client |
| `chromadb` | 1.4.1 | Vector database |
| `tenacity` | 9.1.2 | Retry / backoff logic |
| `tiktoken` | 0.12.0 | Token counting |

### Data & Visualisation

| Package | Version | Role |
|---------|---------|------|
| `pandas` | 2.3.3 | Data manipulation, Excel reading |
| `numpy` | 2.4.1 | Numerical computing |
| `openpyxl` | 3.1.5 | Excel file I/O |
| `matplotlib` | 3.10.8 | Chart generation |
| `pypdf` | 6.6.2 | PDF text extraction |

### Web & HTTP

| Package | Version | Role |
|---------|---------|------|
| `streamlit` | 1.54.0 | Web UI |
| `requests` | 2.32.5 | HTTP client (Alpha Vantage) |
| `httpx` | 0.28.1 | Async HTTP |
| `aiohttp` | 3.13.3 | Async HTTP |

### Database (Optional)

| Package | Version | Role |
|---------|---------|------|
| `sqlalchemy` | 2.0.46 | ORM |
| `psycopg2-binary` | 2.9.11 | PostgreSQL driver |

### Utilities

| Package | Version | Role |
|---------|---------|------|
| `python-dotenv` | 1.2.1 | `.env` file loading |
| `pydantic` | 2.12.5 | Data validation |
| `pyarrow` | 23.0.1 | Data serialisation |

---

## Setup & Installation

### Prerequisites

- Python 3.10 or later
- An [OpenAI API key](https://platform.openai.com/api-keys)
- An [Alpha Vantage API key](https://www.alphavantage.co/support/#api-key) (free tier available)
- (Optional) PostgreSQL 14+ if you want the database module

### 1. Clone / navigate to the project

```bash
cd C:\Users\vinit\Documents\agentic_ai\capstone_project\ai_finance_asst
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

For a lighter install (no database drivers):

```bash
pip install -r requirements_new.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-proj-...
ALPHA_VANTAGE_API_KEY=YOUR_KEY_HERE

# Optional — only needed if using the database module
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
```

### 5. (Optional) Populate the RAG knowledge base

Place any financial PDF documents (annual reports, whitepapers, textbooks) into the `docs/` directory, then run:

```python
from rag.vector_store_embedding import EmbeddingProcessor
ep = EmbeddingProcessor()
ep.create_embeddings()
```

This only needs to be run once; the vector store persists to disk.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Used for GPT-4o-mini (all agents) and `text-embedding-3-large` (RAG) |
| `ALPHA_VANTAGE_API_KEY` | Yes* | Real-time stock data & news. Falls back to `"demo"` key (1 req/min limit) |
| `DATABASE_URL` | No | PostgreSQL connection string for optional DB module |

\* The `"demo"` key works for a single symbol (`IBM`) and is heavily rate-limited. A free Alpha Vantage key supports ~5 requests/minute.

---

## Running the App

### Streamlit (recommended)

```bash
streamlit run app/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Run individual agents (for testing)

```bash
# Finance Q&A (requires populated vector store)
python agent/finance_qa_agent.py

# Portfolio analysis (uses sample_portfolio.xlsx)
python agent/portfolio_agent.py

# Market data
python agent/market_analysis_agent.py

# News & sentiment
python agent/news_synthesizer_agent.py

# Full orchestrator
python agent/orchestrator.py
```

---

## Docker Deployment

```bash
# Build and start all services
docker compose build
docker compose up

# Access at http://localhost:8501
# Shut down
docker compose down
```

See `DOCKER_README.md` for advanced configuration (volume mounts, environment injection, multi-service setup).

---

## Usage Guide

### Mode 1 — Direct Agents (four tabs)

**Finance Q&A tab**
- Type any general finance question (e.g., *"What is asset allocation and why does it matter?"*)
- The agent retrieves relevant passages from your PDF documents and answers with source citations.

**Portfolio Analysis tab**
- Upload your `.xlsx` portfolio file via the sidebar.
- Ask things like *"Analyse my portfolio and highlight concentration risk."*
- Seven charts are rendered below the response.

**Market Analysis tab**
- Ask about specific tickers or companies: *"What are Apple's fundamentals?"* or *"Show me Tesla's intraday prices."*

**News Synthesizer tab**
- Request news by ticker or topic: *"Latest sentiment for NVDA"* or *"Sector news on renewable energy."*

### Mode 2 — Orchestrator (single chat)

Switch to **Orchestrator** from the sidebar radio button. Type naturally; the planner decides which agents to call:

| Query | Agents invoked |
|-------|---------------|
| "What is the Sharpe ratio?" | `qa` |
| "How is my portfolio diversified?" | `portfolio` |
| "Current price and news for Microsoft" | `market`, `news` |
| "Compare AAPL fundamentals with my holdings" | `market`, `portfolio` |

Blocked queries (e.g., *"How do I guarantee 30% returns?"*) return a compliance message without invoking any agent.

---

## Data Flow

### Finance Q&A (RAG)

```
Question
  → OpenAI embedding
  → Chroma similarity search (k=2)
  → Retrieved chunks + metadata
  → LLM synthesises answer with citations
```

### Portfolio Analysis

```
Excel upload
  → load_all_sheets()
  → calc_holdings_metrics()  ──┐
  → calc_transaction_metrics() ├─ results dict
  → calc_snapshot_metrics()  ──┘
  → generate_charts() → 7 PNGs
  → LLM narrates insights
```

### Market & News

```
User query (ticker/company)
  → Alpha Vantage REST API
  → JSON response parsed
  → LLM formats structured answer
```

---

## API Integrations

### OpenAI

| Usage | Model / Endpoint |
|-------|-----------------|
| All agents & orchestrator | `gpt-4o-mini` |
| Guardrail classification | `gpt-4o-mini` |
| Document embeddings (RAG) | `text-embedding-3-large` |

### Alpha Vantage

| Endpoint | Used by |
|----------|---------|
| `GLOBAL_QUOTE` | Market agent — live quote |
| `TIME_SERIES_INTRADAY` | Market agent — intraday OHLCV |
| `TIME_SERIES_DAILY` | Market agent — daily OHLCV |
| `OVERVIEW` | Market agent — company fundamentals |
| `SYMBOL_SEARCH` | Market agent — ticker lookup |
| `NEWS_SENTIMENT` | News agent — news + sentiment |

Free-tier rate limit: **5 API calls / minute**. Use your own key to avoid throttling.

---

## Excel Portfolio Format

The portfolio agent expects an `.xlsx` file with the following structure. Column names are matched case-insensitively and support common aliases.

### Required sheet: `Holdings`

| Column | Aliases accepted | Example |
|--------|-----------------|---------|
| Ticker | `symbol`, `stock` | `AAPL` |
| Quantity | `shares`, `units` | `50` |
| Buy Price | `purchase_price`, `cost` | `145.00` |
| Current Price | `market_price`, `price` | `178.50` |
| Sector | — | `Technology` |
| Asset Type | `asset_class`, `type` | `Equity` |

### Optional sheets

| Sheet | Purpose |
|-------|---------|
| `Transactions` | Buy/sell history; enables trade-frequency analytics |
| `Portfolio_Snapshots` | Historical total values; enables drawdown & volatility |
| `Market_Data` | Supplementary price data |

A sample file is provided at `tools/sample_portfolio.xlsx`.

---

## Key Design Decisions

### Lazy module loading
`portfolio_agent.py` and `finance_qa_agent.py` import their heavy dependencies (`portfolio_analyzer`, `EmbeddingProcessor`) at runtime using `importlib`. This allows the app to start even if the vector store has not been initialised yet, and enables graceful error messages rather than import failures.

### Guardrail-first architecture
The compliance check runs before the planner. A blocked query never reaches any data-fetching agent, ensuring policy enforcement regardless of agent behaviour.

### Separate chat histories per mode
Mode 1 maintains four independent conversation histories (one per tab). Mode 2 maintains one orchestrator history. Switching modes does not cross-contaminate context.

### Persistent Chroma vector store
The vector store is written to `chroma_langchain_db/` and reloaded on startup, so embeddings only need to be computed once per document set.

### Flexible Excel column matching
`portfolio_analyzer._safe_col()` performs case-insensitive substring matching against a list of known aliases, so uploaded files do not need to follow an exact naming convention.
