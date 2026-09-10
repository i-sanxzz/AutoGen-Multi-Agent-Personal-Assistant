# AutoGen Multi-Agent AI Personal Assistant

A modular, multi-agent personal assistant built with Microsoft's AutoGen (`autogen-agentchat` v0.7+) framework. The system implements task decomposition and delegation across specialized agents (Manager, Research, Coding) with tool execution and full transcript observability.

---

## 1. Project Setup

### Prerequisites
- Python 3.10 to 3.12 (Python 3.12 recommended)
- `uv` (recommended) or standard `pip`/`venv`
- OpenAI API key (or OpenAI-compatible endpoint such as Gemini, Groq, OpenRouter)

### Installation

1. **Create and activate a virtual environment:**
   ```bash
   # Using uv:
   uv venv --python 3.12 .venv
   source .venv/bin/activate

   # Or using standard python:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in your API key:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set for **OpenRouter**:
   ```env
   OPENAI_API_KEY="sk-or-v1-..."
   OPENAI_BASE_URL="https://openrouter.ai/api/v1"
   OPENAI_MODEL="openai/gpt-4o-mini"
   ```
   *(Or choose models like `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-chat`, etc.)*


---

## 2. Running Milestone 1 (Environment Smoke Test)

Run the single-agent verification script:
```bash
python main.py
```

---

## 3. Running the Multi-Agent Assistant (Milestones 3 & 4)

### Interactive Mode
Launch the interactive terminal interface:
```bash
python run_assistant.py
```

### Pre-Configured Demo Scenarios (From SD.md Section 15)
Run the exact review demo scenarios directly:
```bash
# Scenario 1: Grounded Research with Web Search Tool
python run_assistant.py --demo 1

# Scenario 2: Project Breakdown (Collaborative: Research + Code generation)
python run_assistant.py --demo 2

# Scenario 3: Coding & Local Execution Verification
python run_assistant.py --demo 3
```

### Direct Query Execution
Pass any prompt directly as a CLI argument:
```bash
python run_assistant.py "Explain quantum computing in 2 paragraphs"
```

Transcripts and execution metrics are automatically timestamped and saved into `transcripts/` in JSON format for review auditability.

---

## 4. Running the Streamlit Web Console

To launch the high-density inspection web UI:
```bash
streamlit run app.py
```
* **Developer-grade UI:** Stripped of default Streamlit loading animations (no running man, no bouncing spinners, no AI-slob glowing gradients).
* **Multi-tab inspection:** Dedicated tabs for Synthesized Final Answers, Step-by-Step Inter-Agent Handoff Traces, and Downloadable JSON Transcripts.
* **1-Click Preset Demos:** Preload and run Scenarios 1, 2, or 3 directly from the sidebar.

---

## 5. Testing & Empirical Evaluation (SD.md Section 12)

### Run Unit Tests
Executes unit tests for tools, agents, and team structure:
```bash
pytest tests/
```

### Run Empirical Review Benchmark Table
Executes test cases T-01 through T-05 and outputs the measured result table:
```bash
python tests/run_evaluation.py
```

---

## 5. Project Roadmap

- [x] **Milestone 1:** Environment setup & single agent smoke test
- [x] **Milestone 2:** Specialized tools setup (`search_web` via `ddgs` + `LocalCommandLineCodeExecutor`)
- [x] **Milestone 3:** Specialized Agents (`research_agent` & `coding_agent`)
- [x] **Milestone 4:** Manager Orchestrator & Multi-Agent Team (`SelectorGroupChat` with `TERMINATE` control)
- [x] **Milestone 6 (Early):** Automated unit test suite & empirical pass/fail benchmark table (T-01 to T-05)
- [ ] **Milestone 5:** SQLite Session Memory persistence across user turns
- [ ] **Milestone 7:** Optional Streamlit/FastAPI UI for live demonstration
