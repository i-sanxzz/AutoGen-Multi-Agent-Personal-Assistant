# AutoGen Multi-Agent AI Personal Assistant — Project Blueprint

> Prepared as the architecture + review-readiness plan before any code is written, per the master project prompt. Framework choice (AutoGen) is locked per your constraint — see the technology note in Section 9 for one thing you should know before the panel asks about it.

---

## 1. Refined Project Title

**"AutoGen-Based Multi-Agent Personal Assistant: Task Delegation and Collaborative Reasoning Across Specialized AI Agents"**

Shorter version for slides/submission: **"AutoGen Multi-Agent AI Personal Assistant"** (your original title is fine — the long form is just there if your review format wants a formal thesis-style title).

---

## 2. One-Paragraph Project Concept

A single LLM handling every kind of request — research, coding, scheduling, writing — tends to produce shallow, generic answers because it has no specialization and no way to check its own work. This project builds a personal assistant where a **Manager Agent** receives a natural-language request, breaks it into subtasks, and routes each subtask to a **specialized agent** (research, coding, task-planning) built with Microsoft's AutoGen AgentChat framework. Agents communicate through AutoGen's group-chat message-passing, use real tools (web search, code execution) rather than just generating text, and hand a synthesized result back to the user. The system demonstrates — with working code, not slides — that multi-agent delegation produces more reliable, specialized, and inspectable results than a single monolithic chatbot call.

---

## 3. Problem Statement

Conventional single-agent AI assistants (a single LLM call, possibly with a few tools bolted on) suffer from three structural limitations:

1. **No specialization** — the same model, prompt, and context handle research, coding, and planning equally (badly), because there's no mechanism to give a task-specific persona, tool access, or reasoning strategy per task type.
2. **No self-checking** — a single agent cannot meaningfully validate its own output, since the model that made the mistake is the same one reviewing it.
3. **No decomposition trail** — when a request has multiple parts, a single-agent system either answers superficially or silently drops sub-requirements, and there's no visible record of *how* the task was broken down.

Multi-agent collaboration addresses this by assigning bounded roles to separate agents that communicate explicitly, so task decomposition, delegation, and (optionally) validation become visible, testable steps rather than one opaque generation. The practical problem this project solves: **build a demonstrably modular assistant where you can point to which agent did what, and prove it end-to-end**, rather than asserting it did.

---

## 4. Primary Objective

Design and implement a working multi-agent personal assistant using AutoGen AgentChat that accepts a natural-language user request, delegates it across at least two specialized agents through visible inter-agent communication, and returns a synthesized final response — with the full delegation trace inspectable as evidence.

---

## 5. Specific Objectives

1. Implement a Manager/Orchestrator agent that decomposes a user request into subtasks.
2. Implement at least two specialized agents (Research, Coding) with distinct system prompts and tool access.
3. Implement real tool usage — at minimum, a live web-search tool and a code-execution tool — not simulated outputs.
4. Demonstrate agent-to-agent message passing using AutoGen's `GroupChat`/`Team` abstractions, with the full transcript loggable.
5. Implement basic error handling for tool failures and empty/invalid agent responses.
6. Implement minimal persistent memory (SQLite) so the assistant retains context across turns within a session.
7. Build a test suite covering unit (single agent), integration (agent-to-agent), and workflow (full request) levels with a documented pass/fail table.
8. Produce a measured (not estimated) report of execution time, LLM call count, and success rate across the test suite.

---

## 6. Recommended MVP

Do **not** build all five specialized agents from the original diagram for the first review. The minimum viable architecture that is genuinely demonstrable and defensible:

- **Manager Agent** (orchestrator + synthesizer — one agent doing both jobs for now)
- **Research Agent** (web search tool)
- **Coding Agent** (code generation + local execution tool)

That's it — **3 agents total** for Phase 1. This is enough to prove delegation, tool use, and inter-agent communication, and small enough that you can explain every line of the transcript under questioning. A dedicated Reviewer/Validation agent, Task & Scheduling agent, File/Document agent, and Communication agent are **Phase 2**, added only once the 3-agent core is tested and reliable.

Rationale: a 5+ agent system that half-works is a worse review outcome than a 3-agent system that fully works and is fully explained.

---

## 7. Recommended Agent Architecture

```
Phase 1 (MVP — this review):

  User
    |
    v
  Manager Agent  (decomposes request, routes subtasks, synthesizes final answer)
    |
    +--> Research Agent   (web search tool)
    |
    +--> Coding Agent     (code-gen + execution tool)
    |
    v
  Final Response to User


Phase 2 (next milestone, not claimed as done):

  User -> Manager -> Planner -> {Research, Coding, Task/Scheduling} -> Reviewer -> Manager -> User
```

Communication mechanism: AutoGen AgentChat's `SelectorGroupChat` (or `RoundRobinGroupChat` for the simplest version), where the Manager acts as the natural termination/synthesis point. Each agent is an `AssistantAgent` with its own `system_message`, its own tool list, and a shared `model_client`.

---

## 8. Agent Specifications

### Manager Agent
- **Role:** Orchestrator and final synthesizer.
- **Responsibilities:** Parse user request, decide which specialized agent(s) are needed, sequence the conversation, merge results into one coherent answer.
- **Input:** Raw user request (natural language).
- **Output:** Final synthesized response + (for demo/logging purposes) the delegation trace.
- **Tools:** None directly — it delegates. It can carry a `TERMINATE`-style condition to end the group chat.
- **Communicates with:** Research Agent, Coding Agent.
- **Failure conditions:** No specialized agent's response is usable → Manager must say so explicitly rather than fabricating an answer; ambiguous request → Manager should ask a clarifying question rather than silently guessing (log this as a known limitation if not yet implemented).

### Research Agent
- **Role:** Information gathering and summarization.
- **Responsibilities:** Take a research sub-question from the Manager, run a web search tool, summarize findings with source attribution.
- **Input:** A specific research question (not the raw user request).
- **Output:** A summary with cited sources.
- **Tools:** Web search function (e.g., wrapped Bing/Tavily/SerpAPI call, or `autogen_ext`'s available search tool).
- **Communicates with:** Manager Agent only (Phase 1).
- **Failure conditions:** Search API failure or empty results → return an explicit "no results found" message, not a hallucinated summary.

### Coding Agent
- **Role:** Code generation and execution.
- **Responsibilities:** Take a coding sub-task, generate a solution, execute it in a sandboxed code executor, return the code + actual execution output.
- **Input:** A specific coding/programming task description.
- **Output:** Code block + execution result (stdout/stderr) + brief explanation.
- **Tools:** AutoGen's `CodeExecutorAgent`/local code executor (Docker or local Python executor — see tech stack note below).
- **Communicates with:** Manager Agent only (Phase 1).
- **Failure conditions:** Code fails to execute → return the actual error trace, not a claim of success; execution timeout → return partial output with a timeout flag.

*(Reviewer/Validation, Task & Scheduling, File/Document, and Communication agents: specs deferred to Phase 2 — listing them now with responsibilities you haven't built would violate the "don't claim planned as completed" rule.)*

---

## 9. Technology Stack

| Technology | Why required | Why selected | Alternatives considered |
|---|---|---|---|
| Python 3.10+ | AutoGen's minimum supported version | Team's existing Python familiarity | N/A — required by framework |
| `autogen-agentchat` + `autogen-ext` | Core multi-agent framework, current stable line (v0.7.x at time of writing) | Directly specified by project constraint | Microsoft Agent Framework (see note below), CrewAI, LangGraph |
| An LLM API (OpenAI-compatible) | Powers every agent's reasoning | Widest AutoGen `model_client` support, easiest to demo | Azure OpenAI, local Ollama model (cheaper for repeated testing, worth considering if API cost is a concern) |
| SQLite | Lightweight persistent memory | Zero-setup, file-based, fine for a single-user demo | JSON file (even simpler, less queryable) |
| FastAPI or Streamlit | Simple interface for the live demo | Streamlit is faster to build a demo UI in for a review; FastAPI better if you want an API-first architecture | Plain CLI (fine for Phase 1, arguably *more* credible for showing raw agent transcripts) |
| Langfuse (optional) | Trace/log agent-to-agent calls, execution time, and call counts with minimal instrumentation | Directly answers your "measured, not invented" results requirement — every agent call gets a timestamped trace you can screenshot for the review | Manual logging module (more control, more work) |

### ⚠️ Important technology note — read before the review

Your prompt asked me to verify AutoGen's current status rather than assume. I did, and there's something you should know:

**As of 2026, Microsoft has placed AutoGen in maintenance mode.** It still works, is still installable (`pip install -U "autogen-agentchat" "autogen-ext[openai]"`, currently v0.7.x), and receives bug/security fixes — but Microsoft's actively developed successor is **Microsoft Agent Framework** (unifying AutoGen + Semantic Kernel, reached v1.0 in April 2026), which they recommend for *new* projects.

Since your constraint is "have to use AutoGen" (a faculty/curriculum requirement, presumably), **I'm keeping AutoGen** — this isn't a reason to switch. But it *is* likely faculty question material ("why AutoGen and not the current Microsoft framework?"), so I've written you a ready answer for it in Section 16. Better to walk in knowing this than get caught by it.

---

## 10. System Architecture Diagram

```
+-------------------------------------------------------------+
|                          USER (CLI/UI)                       |
+-------------------------------+-----------------------------+
                                |  natural-language request
                                v
                    +-----------------------+
                    |     Manager Agent     |
                    |  (decompose, route,   |
                    |   synthesize)         |
                    +-----+------------+----+
                          |            |
             subtask A    |            |  subtask B
                          v            v
              +---------------+  +---------------+
              | Research Agent|  | Coding Agent  |
              | (web search)  |  | (codegen+exec)|
              +-------+-------+  +-------+-------+
                      |                  |
                      +--------+---------+
                               |  results
                               v
                    +-----------------------+
                    |     Manager Agent     |
                    |   (final synthesis)   |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |    Final Response      |
                    +-----------------------+

Cross-cutting: SQLite (session memory) <-> Manager Agent
               Langfuse/logging       <-> all agent calls
```

---

## 11. Modules to Demonstrate in the First Review

| Module | Status you should be able to claim |
|---|---|
| Manager Agent (decomposition + routing) | Implemented, tested |
| Research Agent + web search tool | Implemented, tested |
| Coding Agent + code executor | Implemented, tested |
| Agent-to-agent message passing (group chat transcript) | Implemented, tested — show the raw transcript live |
| Basic error handling (tool failure, empty result) | Implemented, tested |
| SQLite session memory | Implemented, partially tested (state clearly) |
| CLI or minimal Streamlit interface | Implemented |
| Reviewer/Validation agent | Not started — Phase 2, and say so plainly |

---

## 12. Testing Plan

**Unit tests** — each agent in isolation, mocked tool responses, verify it produces well-formed output for a known input.

**Integration tests** — Manager ↔ Research, Manager ↔ Coding: verify the subtask sent matches what the Manager intended, and the response returned is correctly attributed back.

**Workflow tests** — full user request end-to-end, at least one per demo scenario (Section 15).

**Error tests** — invalid input, search API returns nothing, code execution throws, agent returns empty string, simulated timeout.

**Performance tests** — total wall-clock time per request, number of LLM calls per request, number of inter-agent messages, failure rate across N runs.

Test-case table template to fill in as you actually run tests (do not pre-fill the Actual/Status columns):

| Test ID | Module | Input | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| T-01 | Research Agent | "Summarize recent news on X" | Summary with ≥1 cited source | *to be measured* | *to be measured* |
| T-02 | Coding Agent | "Write a function to reverse a string" | Valid Python, executes, correct output | *to be measured* | *to be measured* |
| T-03 | Manager | Multi-part request needing both agents | Both subtasks delegated, both results present in final answer | *to be measured* | *to be measured* |
| T-04 | Error handling | Search tool forced to fail | Explicit "no results" message, no hallucination | *to be measured* | *to be measured* |
| T-05 | Error handling | Code with a syntax error | Actual error trace returned, not a false "success" claim | *to be measured* | *to be measured* |

---

## 13. Expected Results

- Functional: Manager correctly routes research-only, coding-only, and mixed requests. **To be measured during testing.**
- Collaboration: inter-agent transcripts show correct subtask handoff and no message loss. **To be measured during testing.**
- Reliability: percentage of test-suite requests completing without manual intervention. **To be measured during testing.**
- Performance: average execution time and LLM call count per request. **To be measured during testing.**

No numbers are asserted here — plug in real measurements once you've run the test suite, using Langfuse traces or manual timing as your source of truth.

---

## 14. Completion Roadmap

| Component | Status | Evidence | Next Step |
|---|---|---|---|
| Architecture | ✅ Completed | This document | — |
| AutoGen setup | ⚪ Planned | — | Milestone 1 |
| Manager Agent | ⚪ Planned | — | Milestone 3 |
| Research Agent | ⚪ Planned | — | Milestone 4 |
| Coding Agent | ⚪ Planned | — | Milestone 4 |
| Tool Integration | ⚪ Planned | — | Milestone 6 |
| Memory (SQLite) | ⚪ Planned | — | Milestone 7 |
| UI | ⚪ Planned | — | Milestone 9 |
| Testing | ⚪ Planned | — | Milestone 8/10 |
| Documentation | 🟡 In Progress | This document | Ongoing |

**Completion estimate: ~10%** (architecture and planning done; zero lines of working code yet). This is a transparent floor, not a discouraging number — architecture-before-code is exactly the right order for a review-ready project.

---

## 15. Three Live Demo Scenarios

### Scenario 1 — Research
- **User request:** "Research the current state of quantum error correction and summarize the top 3 developments."
- **Agent flow:** Manager → Research Agent → Manager.
- **Internal delegation:** Manager sends Research Agent the exact sub-question; Research Agent calls the search tool, returns a cited summary.
- **Result:** User sees a synthesized 3-point summary with sources.
- **Why it's genuinely multi-agent:** The Manager doesn't answer from its own knowledge — it delegates to an agent whose entire role is grounding claims in a live tool call, and the transcript proves that happened.

### Scenario 2 — Complex Task Breakdown
- **User request:** "I need to build a personal budgeting app. Break this into a project plan."
- **Agent flow:** Manager decomposes into research (what features do budgeting apps need) + coding (scaffold) subtasks → Research Agent → Coding Agent → Manager synthesizes.
- **Internal delegation:** Research Agent gets "common features in budgeting apps"; Coding Agent gets "generate a basic project structure for a budgeting app."
- **Result:** User sees a structured plan combining researched feature list + a real starter code scaffold.
- **Why it's genuinely multi-agent:** One request fans out into two *different kinds* of subtasks handled by two agents with different tools — this is the clearest demonstration of specialization.

### Scenario 3 — Coding
- **User request:** "Write a function to check if a string is a palindrome, and verify it works."
- **Agent flow:** Manager → Coding Agent → Manager.
- **Internal delegation:** Coding Agent receives the task, generates code, executes it against test inputs via the code executor.
- **Result:** User sees the code plus actual execution output (not a claimed result).
- **Why it's genuinely multi-agent:** Demonstrates tool-grounded execution — the "verify it works" part is a real code run, not the LLM asserting correctness.

Prefer starting the live demo with Scenario 3 (most reliable, fewest moving parts) before attempting Scenario 2 (most impressive, most can go wrong).

---

## 16. Likely Faculty Questions

**Q: Why use AutoGen instead of building this with plain API calls?**
- *Viva answer:* AutoGen gives us structured multi-agent conversation management (group chats, message routing, termination conditions) out of the box, so we're not reinventing agent orchestration from scratch.
- *Deeper answer:* Plain API calls would require us to manually manage conversation state, role-switching, and message routing between agents — AutoGen's `AgentChat` layer abstracts that into `AssistantAgent` + `Team` objects, letting us focus on agent specialization and tool design rather than plumbing.

**Q: Why multiple agents instead of one LLM with a big prompt?**
- *Viva answer:* Specialization — a narrow system prompt and tool set per agent produces more focused, checkable output than one prompt trying to do everything.
- *Deeper answer:* A single agent conflates reasoning about *what* to do with *doing* it, so errors compound invisibly. Separate agents make the decomposition an explicit, inspectable artifact (the message transcript) rather than an internal, unauditable step.

**Q: AutoGen is in maintenance mode — why not use Microsoft Agent Framework instead?**
- *Viva answer:* AutoGen is stable, fully functional, and receiving security/bug fixes; it remains a valid and widely-used framework for current multi-agent systems, and it's the framework specified for this project.
- *Deeper answer:* Microsoft Agent Framework (v1.0, April 2026) is the actively developed successor, unifying AutoGen and Semantic Kernel with a workflow-graph model. For a time-boxed academic project, AutoGen's simpler `Team`/`GroupChat` abstraction is lower-overhead to learn and demonstrate; migrating later is a documented, mechanical process (Microsoft publishes an official migration guide) if the project continues beyond this course.

**Q: How do agents communicate?**
- *Viva answer:* Through AutoGen's group-chat message passing — each agent's output becomes a message visible to the next agent/Manager in the conversation.
- *Deeper answer:* Concretely, a `SelectorGroupChat` (or `RoundRobinGroupChat`) maintains a shared message thread; the Manager's routing logic (or a selector function) determines which agent responds next based on the conversation state.

**Q: How do you prevent infinite agent conversations?**
- *Viva answer:* Explicit termination conditions — e.g., max message count, or the Manager emitting a `TERMINATE` signal once synthesis is complete.
- *Deeper answer:* AutoGen supports composable termination conditions (`MaxMessageTermination`, `TextMentionTermination`, etc.) that we combine so the group chat halts on the first condition met, preventing runaway loops even if the Manager fails to synthesize cleanly.

**Q: How do you handle hallucinations?**
- *Viva answer:* Tool grounding — Research and Coding agents must use real tools (search, execution) rather than answering from memory, and failures are surfaced explicitly instead of papered over.
- *Deeper answer:* This is a mitigation, not a solution — we don't currently have a dedicated fact-checking/Reviewer agent (that's Phase 2). We're honest about this limitation rather than claiming hallucinations are "solved."

**Q: What happens when an agent fails?**
- *Viva answer:* The failure is caught and surfaced explicitly to the Manager and, ultimately, the user — not silently swallowed.
- *Deeper answer:* Each tool call is wrapped in error handling that returns a structured failure message rather than raising an uncaught exception, so the Manager can decide whether to retry, report the limitation, or proceed with partial results.

**Q: What is the future scope?**
- *Viva answer:* Phase 2 adds a Reviewer/Validation agent, Task/Scheduling agent, and richer memory; Phase 3 adds full integration, a polished UI, and complete test coverage.
- *Deeper answer:* See Section 6/14 — the roadmap is explicit about what's deferred and why, rather than an open-ended wishlist.

---

## 17. First Implementation Milestone

### Milestone 1 — Environment and Project Structure

- **Goal:** A working AutoGen install and a runnable "hello world" single agent, proving the toolchain works before any multi-agent logic is written.
- **Modules involved:** None yet (infrastructure only).
- **Files to create:**
  - `requirements.txt`
  - `.env.example` (API key placeholder, never a real key)
  - `main.py` (single `AssistantAgent` hello-world)
  - `README.md` (setup + run instructions)
- **Dependencies:** `autogen-agentchat`, `autogen-ext[openai]`, `python-dotenv`
- **Implementation steps:**
  1. Create a virtual environment, Python 3.10+.
  2. `pip install -U "autogen-agentchat" "autogen-ext[openai]" python-dotenv`
  3. Set `OPENAI_API_KEY` via `.env` (loaded with `python-dotenv`, since AutoGen does not auto-load `.env`).
  4. Write a single `AssistantAgent` that responds to `"Say hello and confirm you're running."`
- **Expected output:** A confirmation message printed to console proving the model client, agent, and API key are all wired correctly.
- **Testing method:** Manual run — does it print a coherent response without errors?
- **Completion criteria:** Script runs end-to-end with no exceptions, on a fresh environment, using only the README instructions.
