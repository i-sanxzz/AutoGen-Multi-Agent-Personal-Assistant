# AutoGen Multi-Agent AI Personal Assistant — Project Documentation

**Version:** 1.0 | **Framework:** Microsoft AutoGen (`autogen-agentchat` v0.7.5) | **Status:** ✅ Fully Operational

---

## Table of Contents
1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Setup & Installation](#4-setup--installation)
5. [Configuration (.env)](#5-configuration-env)
6. [Agents](#6-agents)
7. [Tools](#7-tools)
8. [Team Orchestration](#8-team-orchestration)
9. [Running the Project](#9-running-the-project)
10. [Testing](#10-testing)
11. [Transcripts & Observability](#11-transcripts--observability)
12. [Troubleshooting](#12-troubleshooting)
13. [Roadmap](#13-roadmap)

---

## 1. Overview

A modular, multi-agent personal assistant built on Microsoft's **AutoGen AgentChat** framework. A **Manager Agent** decomposes user requests and delegates subtasks to two specialized agents:

- **Research Agent** — grounded live web search with source citations
- **Coding Agent** — Python code generation with verified local execution

Every session produces a timestamped JSON transcript for full auditability, and a Streamlit web console provides developer-grade inspection of all inter-agent activity.

**Key capabilities:**
- Task decomposition & delegation (Manager orchestration)
- Grounded research via DuckDuckGo (`ddgs`) — no fabricated facts
- Sandboxed local Python execution with 30s timeout
- LLM-driven agent selection (`SelectorGroupChat`)
- `TERMINATE` keyword-based clean session termination
- Full transcript logging (latency, turns, agent participation)

---

## 2. Architecture

```
                        ┌─────────────────────┐
     User Request ────► │   Manager Agent     │  (Orchestrator)
                        │  - Decomposes task  │
                        │  - Delegates        │
                        │  - Synthesizes      │
                        │  - Appends TERMINATE│
                        └──────┬───────┬──────┘
                               │       │
              ┌────────────────┘       └───────────────┐
              ▼                                        ▼
   ┌─────────────────────┐                  ┌─────────────────────┐
   │   Research Agent    │                  │    Coding Agent     │
   │  Tool: search_web   │                  │ Tool: execute_python│
   │  (DuckDuckGo/ddgs)  │                  │ (Local sandbox 30s) │
   └─────────────────────┘                  └─────────────────────┘

   Coordination: SelectorGroupChat (LLM-based selector picks next speaker)
   Termination:  TextMentionTermination("TERMINATE") | MaxMessageTermination(15)
```

**Data flow per request:**
1. User prompt enters the `SelectorGroupChat`.
2. The selector LLM picks `manager_agent` first → it decomposes the task.
3. Manager delegates to `research_agent` (web facts) and/or `coding_agent` (code).
4. Specialized agents call their tools and report results back.
5. Manager synthesizes a unified final answer and appends `TERMINATE`.
6. Team halts; metrics + JSON transcript are saved to `transcripts/`.

---

## 3. Project Structure

```
autogen-main/
├── .env                    # API keys & model config (NOT committed)
├── .env.example            # Config template
├── .gitignore
├── app.py                  # Streamlit web console (3-tab inspection UI)
├── main.py                 # Milestone 1 smoke test (single agent)
├── run_assistant.py        # CLI runner (interactive / --demo / direct query)
├── pytest.ini              # Pytest config (asyncio auto mode)
├── README.md               # Quick-start guide
├── SD.md                   # Software design document
├── requirements.txt        # Dependencies
├── PROJECT_DOCUMENTATION.md  # ← This document
├── src/
│   ├── client.py           # get_model_client() — OpenAI-compatible client factory
│   ├── agents/
│   │   ├── __init__.py     # Exports all agent/team factories
│   │   ├── manager.py      # Manager Agent (orchestrator)
│   │   ├── research.py     # Research Agent (web search)
│   │   ├── coding.py       # Coding Agent (local execution)
│   │   └── team.py         # SelectorGroupChat assembly
│   └── tools/
│       ├── __init__.py     # Exports search_web, execute_python_code
│       ├── search.py       # DuckDuckGo web search tool
│       └── executor.py     # LocalCommandLineCodeExecutor wrapper
├── tests/
│   ├── test_tools.py       # Tool unit tests (5 tests)
│   ├── test_team_structure.py  # Agent/team assembly tests (4 tests)
│   └── run_evaluation.py   # Empirical benchmark (T-01…T-05)
├── transcripts/            # Auto-created JSON session logs
└── workspace/              # Auto-created code-execution sandbox
```

---

## 4. Setup & Installation

**Prerequisites:** Python 3.10–3.12 (3.11+ recommended), pip.

```powershell
cd c:\Users\Admin\Downloads\autogen-main\autogen-main

# 1. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio   # for the test suite

# 3. Configure environment
#    Edit .env (see Section 5)
```

**Installed package versions (verified):**
| Package | Version |
|---------|---------|
| autogen-agentchat | 0.7.5 |
| autogen-core | 0.7.5 |
| autogen-ext[openai] | 0.7.5 |
| ddgs | 9.16.0 |
| streamlit | 1.63.0 |
| python-dotenv | 1.2.3 |
| openai | 3.11.0 |

---

## 5. Configuration (.env)

Current **active configuration — Google Gemini free tier** (OpenAI-compatible endpoint):

```env
OPENAI_API_KEY=AQ.Ab8RN6I...            # Gemini API key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-3.6-flash           # free-tier model
OPENAI_MAX_TOKENS=1000
```

**Supported providers (all OpenAI-compatible):**
| Provider | Base URL | Example Model |
|----------|----------|---------------|
| Google Gemini (free tier) ✅ current | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-3.6-flash` |
| OpenRouter | `https://openrouter.ai/api/v1` | `openai/gpt-4o-mini`, `meta-llama/llama-3.3-70b-instruct:free` |
| OpenAI direct | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Groq / Together / Ollama | respective endpoints | any supported model |

> **Note:** `gemini-2.5-flash` is no longer available to new users — the API recommends `gemini-3.6-flash`. If free-tier rate limits are hit, switch to `gemini-3.6-flash-lite`.

`src/client.py` injects a custom `model_info` block (vision, function-calling, JSON output = true) so non-OpenAI model names work with `OpenAIChatCompletionClient`.

---

## 6. Agents

### 6.1 Manager Agent (`src/agents/manager.py`)
- **Name:** `manager_agent`
- **Role:** Primary coordinator — decomposes user requests, delegates subtasks, synthesizes final answers.
- **Workflow:** Decomposition & delegation → synthesis (with verification highlights) → append `TERMINATE`.
- **Rules:** Never fabricates search findings or code outputs; relies on specialists; transparent about failures.

### 6.2 Research Agent (`src/agents/research.py`)
- **Name:** `research_agent`
- **Tool:** `search_web`
- **Behavior:** ALWAYS calls `search_web` for factual/current questions; cites URLs + titles; reports "No results found" honestly; never writes code.

### 6.3 Coding Agent (`src/agents/coding.py`)
- **Name:** `coding_agent`
- **Tool:** `execute_python_code`
- **Behavior:** ALWAYS executes code before presenting results; includes explicit `print(...)` calls; reports actual stdout/stderr; never fakes output; never searches the web.

---

## 7. Tools

### 7.1 `search_web(query, max_results=5)` — `src/tools/search.py`
- Live DuckDuckGo search via `ddgs`.
- Returns formatted results: `[i] Title / URL: … / Summary: …`
- Handles empty queries and errors gracefully (never raises to the agent).

### 7.2 `execute_python_code(code)` — `src/tools/executor.py`
- Wraps AutoGen's `LocalCommandLineCodeExecutor`.
- Workspace: `workspace/` directory; timeout: **30 seconds**.
- Returns `Execution Status: SUCCESS/FAILED` + stdout/stderr.
- Suppresses the local-execution security warning for clean demo output.

---

## 8. Team Orchestration (`src/agents/team.py`)

- **Type:** `SelectorGroupChat` with 3 participants.
- **Selector:** LLM-driven using `TEAM_SELECTOR_PROMPT` (rules: manager first → delegate → specialists report → manager synthesizes → stop after TERMINATE).
- **Termination:** `TextMentionTermination("TERMINATE")` OR `MaxMessageTermination(max_messages=15)`.
- **Factory:** `create_assistant_team(model_client, max_turns=15)`.

---

## 9. Running the Project

### 9.1 Smoke Test (connectivity check)
```powershell
.venv\Scripts\python.exe main.py
```
✅ Verified output: `[✓] Milestone 1 Smoke Test Successful!`

### 9.2 CLI Assistant
```powershell
.venv\Scripts\python.exe run_assistant.py              # interactive menu
.venv\Scripts\python.exe run_assistant.py --demo 1     # Grounded Research
.venv\Scripts\python.exe run_assistant.py --demo 2     # Project Breakdown (Research + Coding)
.venv\Scripts\python.exe run_assistant.py --demo 3     # Coding & Local Execution
.venv\Scripts\python.exe run_assistant.py "your query" # direct query
```
Features: color-coded agent badges, live tool-call/result streaming, execution metrics (wall-clock time, stop reason, turn breakdown), auto-saved transcripts.

### 9.3 Streamlit Web Console
```powershell
.venv\Scripts\streamlit.exe run app.py
# → http://localhost:8501
```
- **Tab 1 — Final Output & Summary:** user request, synthesized answer, metrics bar.
- **Tab 2 — Multi-Agent Trace Timeline:** step-by-step handoffs + tool call/output boxes.
- **Tab 3 — Audit Log (JSON):** full session payload + download button.
- Sidebar: provider/model config display, preset scenario buttons, clear-session control.
- Design: no default Streamlit animations; clean, high-density developer UI.

### 9.4 Service Management (Windows PowerShell)
```powershell
# Start (background)
Start-Process -FilePath ".venv\Scripts\streamlit.exe" -ArgumentList "run","app.py","--server.headless","true" -WindowStyle Hidden

# Check alive
Invoke-WebRequest http://localhost:8501 -UseBasicParsing   # → 200

# Stop
Get-Process streamlit | Stop-Process -Force
```

---

## 10. Testing

```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

**Current results: 9/9 PASSED** (Python 3.11.9, pytest 9.1.1)

| Test | Status |
|------|--------|
| `test_search_web_empty_query` | ✅ PASSED |
| `test_search_web_live` | ✅ PASSED |
| `test_execute_python_code_success` | ✅ PASSED |
| `test_execute_python_code_syntax_error` | ✅ PASSED |
| `test_execute_python_code_empty` | ✅ PASSED |
| `test_research_agent_init` | ✅ PASSED |
| `test_coding_agent_init` | ✅ PASSED |
| `test_manager_agent_init` | ✅ PASSED |
| `test_team_assembly` | ✅ PASSED |

**Empirical benchmark (requires API key):**
```powershell
.venv\Scripts\python.exe tests/run_evaluation.py   # T-01 … T-05 pass/fail table
```

---

## 11. Transcripts & Observability

Every task run (CLI or web) writes `transcripts/transcript_YYYYMMDD_HHMMSS.json`:
```json
{
  "task": "user prompt",
  "duration_seconds": 12.34,
  "stop_reason": "Text 'TERMINATE' mentioned",
  "agent_turn_counts": {"manager_agent": 2, "research_agent": 1, ...},
  "messages": [{"timestamp", "source", "content"}, ...]
}
```
This provides review-defensible evidence of delegation, tool usage, and synthesis.

---

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `429 insufficient_quota` (OpenAI) | No credits on OpenAI account | Add billing, or switch to Gemini free tier (Section 5) |
| `404 model no longer available` | Deprecated Gemini model | Use `gemini-3.6-flash` (already configured) |
| `API key not found` | Missing `.env` | Recreate from `.env.example`, set `OPENAI_API_KEY` |
| `&&` errors in PowerShell | Old PowerShell doesn't support `&&` | Use `;` as statement separator |
| `No module named pytest` | Test deps not installed | `pip install pytest pytest-asyncio` |
| Free-tier rate limits (429 from Gemini) | Requests-per-minute cap | Wait, or switch to `gemini-3.6-flash-lite` |

---

## 13. Roadmap

- [x] Milestone 1: Environment setup & single-agent smoke test
- [x] Milestone 2: Specialized tools (`search_web` + `LocalCommandLineCodeExecutor`)
- [x] Milestone 3: Specialized agents (research & coding)
- [x] Milestone 4: Manager orchestrator & `SelectorGroupChat` team with TERMINATE control
- [x] Milestone 6 (early): Unit test suite & empirical benchmark (T-01…T-05)
- [x] Gemini free-tier integration (OpenAI-compatible endpoint)
- [ ] Milestone 5: SQLite session memory persistence across user turns
- [ ] Milestone 7: Optional FastAPI backend / advanced UI features