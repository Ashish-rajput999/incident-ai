# IncidentAI — 3-Agent AI Incident Response System

A production-quality, multi-agent pipeline that ingests server logs, performs root cause analysis, researches real solutions from the web, and generates a step-by-step remediation plan — all visualized in a Streamlit dashboard.

**Built by Ashish Singh Naruka**

---

## Architecture

```
Logs → Agent 1 (Log Analysis) → Agent 2 (Solution Research) → Agent 3 (Planner) → Report
        [Groq LLM]              [Web Scraping + LLM parse]     [Groq LLM]
```

### Agent 1 — Log Analysis Agent (`agents/log_agent.py`)

- Ingests all 3 log files (nginx-access, nginx-error, app-error)
- Uses Groq LLM to detect anomalies, correlate events, identify root cause
- Outputs: root cause, evidence snippets, confidence score, affected endpoints

### Agent 2 — Solution Research Agent (`agents/research_agent.py`)

- **Primary source: real web scraping** (DuckDuckGo + BeautifulSoup)
- Generates targeted queries from Agent 1 output
- Scrapes trusted technical docs (SQLAlchemy, PostgreSQL, Gunicorn, Nginx)
- LLM is **only** used to structure the scraped content — not as a knowledge source
- Fallback: pre-defined solutions when web is unreachable

### Agent 3 — Resolution Planner Agent (`agents/planner_agent.py`)

- Takes Agent 1 + Agent 2 outputs as input
- Uses Groq LLM to produce a safe, production-ready remediation plan
- Outputs: pre-checks, numbered steps with commands, post-checks, rollback plan

---

## Setup

### 1. Clone the project

```bash
git clone https://github.com/Ashish-rajput999/incident-ai.git
cd incident-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API key

```bash
cp .env.example .env
# Edit .env and add your Groq API key
# Get a free key at: https://console.groq.com
```

---

## Running

### CLI (backend only)

```bash
python main.py
```

Optionally save the JSON report:

```bash
python main.py --output report.json
```

Use a custom log directory:

```bash
python main.py --logs-dir /path/to/logs
```

### Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

Then open http://localhost:8501 in your browser.

---

## Project Structure

```
incident-ai/
├── agents/
│   ├── log_agent.py          # Agent 1: LLM-powered log analysis
│   ├── research_agent.py     # Agent 2: Web scraping + LLM parsing
│   └── planner_agent.py      # Agent 3: LLM-powered remediation planner
├── services/
│   ├── llm.py                # Groq wrapper (call_llm, call_llm_json)
│   └── scraper.py            # DuckDuckGo search + BeautifulSoup scraper
├── models/
│   └── schemas.py            # Pydantic models for all agent I/O
├── data/
│   ├── nginx-access.log      # Sample logs
│   ├── nginx-error.log
│   └── app-error.log
├── main.py                   # Pipeline orchestrator
├── streamlit_app.py          # Dashboard UI
├── config.py                 # Settings, env vars, paths
├── requirements.txt
├── .env.example
└── README.md
```

---

## Sample Output

```
📂 Loading logs...
  Loaded nginx_access: 1872 chars
  Loaded nginx_error: 2141 chars
  Loaded app_error: 2984 chars

🔍 Running Agent 1: Log Analysis...
   ✓ Done in 4.2s | confidence=0.92

   Root cause: SQLAlchemy QueuePool exhausted due to DB session leak in
   portfolio/rebalance_service.py introduced in deployment 2026.03.17-2

🌐 Running Agent 2: Solution Research...
   [Research] Generated 4 search queries
   [Research] Found 7 web results
   [Research] Scraped 5 pages
   ✓ Done in 8.1s | found 4 solutions

🛠️  Running Agent 3: Resolution Planner...
   ✓ Done in 3.9s | severity=CRITICAL

✅ Pipeline complete in 16.2s

======================================================================
  INCIDENT RESPONSE REPORT
======================================================================

🔴 ROOT CAUSE
   SQLAlchemy QueuePool exhausted due to DB session leak in rebalance_service.py
   Confidence: 92% | Severity: CRITICAL

📋 EVIDENCE
   • QueuePool limit of size 20 overflow 5 reached, connection timed out, timeout 30.00
   • suspected session leak count=23 release_rate_below_threshold=true
   • Worker timeout (pid: 21408) / Worker timeout (pid: 21944)
   ...
```

---

## Tech Stack

- **Python 3** — Core language
- **Streamlit** — Interactive dashboard UI
- **Groq API** — Ultra-fast LLM inference (Llama 3.3 70B)
- **Pydantic** — Strict data validation between agents
- **BeautifulSoup4** — Web scraping for real solutions
- **Requests** — HTTP client for web search

---

## Limitations

1. **Web scraping may be blocked**: Some sites return CAPTCHAs or block scrapers. The system automatically falls back to pre-defined technical solutions in this case.

2. **DuckDuckGo rate limits**: Aggressive use may trigger rate limiting. The system uses a 500ms delay between requests.

3. **Groq API limits**: Using Groq on free tier has RPM limits. For production use, monitor quota usage.

4. **Log format assumptions**: The agents are tuned for the nginx + Gunicorn + SQLAlchemy stack. Other stacks may need prompt adjustments in `agents/log_agent.py`.

---

## Environment Variables

| Variable       | Required | Description         |
| -------------- | -------- | ------------------- |
| `GROQ_API_KEY` | ✅ Yes   | Groq API key        |
| `GROQ_MODEL`   | ❌ No    | Model name override |

---

## Author

**Ashish Singh Naruka** — [GitHub](https://github.com/Ashish-rajput999)
