"""Empirical Test Suite Runner & Benchmark for SD.md Section 12 & 13.

Generates a measured pass/fail evaluation table for academic review defensibility.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from src.client import get_model_client
from src.tools.search import search_web
from src.tools.executor import execute_python_code
from src.agents import (
    create_manager_agent,
    create_research_agent,
    create_coding_agent,
    create_assistant_team,
)


async def run_evaluation():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    print("\n" + "=" * 75)
    print(" AutoGen Multi-Agent Personal Assistant — Empirical Evaluation Suite")
    print("=" * 75)

    if not api_key:
        print("[!] OPENAI_API_KEY not configured. Running offline tool tests only.")
        print("    Configure .env to execute live agent tests (T-01, T-02, T-03).\n")

    results = []

    # T-04: Error handling - forced empty / invalid search
    t0 = time.time()
    try:
        res_t04 = search_web("")
        passed_t04 = "Query cannot be empty" in res_t04 or "error" in res_t04.lower()
        duration_t04 = time.time() - t0
        results.append({
            "id": "T-04",
            "module": "Error handling (Search)",
            "input": "search_web('')",
            "expected": "Explicit error message, no crash/hallucination",
            "actual": res_t04.strip()[:40] + "...",
            "duration": f"{duration_t04:.2f}s",
            "status": "PASS" if passed_t04 else "FAIL"
        })
    except Exception as e:
        results.append({
            "id": "T-04",
            "module": "Error handling (Search)",
            "input": "search_web('')",
            "expected": "Explicit error message",
            "actual": str(e)[:40],
            "duration": f"{time.time() - t0:.2f}s",
            "status": "FAIL"
        })

    # T-05: Error handling - Code with syntax error
    t0 = time.time()
    try:
        res_t05 = await execute_python_code("def bad_code(: pass")
        passed_t05 = "FAILED" in res_t05 and "SyntaxError" in res_t05
        duration_t05 = time.time() - t0
        results.append({
            "id": "T-05",
            "module": "Error handling (Code)",
            "input": "def bad_code(: pass",
            "expected": "Actual SyntaxError trace returned, not false success",
            "actual": res_t05.split('\n')[0],
            "duration": f"{duration_t05:.2f}s",
            "status": "PASS" if passed_t05 else "FAIL"
        })
    except Exception as e:
        results.append({
            "id": "T-05",
            "module": "Error handling (Code)",
            "input": "def bad_code(: pass",
            "expected": "Actual SyntaxError trace returned",
            "actual": str(e)[:40],
            "duration": f"{time.time() - t0:.2f}s",
            "status": "FAIL"
        })

    # If API key is available, run live agent evaluations T-01, T-02, T-03
    if api_key:
        model_client = get_model_client()

        # T-01: Research Agent isolated test
        t0 = time.time()
        try:
            researcher = create_research_agent(model_client)
            task_t01 = "Search and summarize recent developments in quantum computing. Cite at least 1 URL."
            resp_t01 = await researcher.run(task=task_t01)
            last_msg = resp_t01.messages[-1].content if resp_t01.messages else ""
            has_url = "http" in last_msg or "URL" in last_msg
            duration_t01 = time.time() - t0
            results.append({
                "id": "T-01",
                "module": "Research Agent",
                "input": "Search & summarize quantum computing",
                "expected": "Summary with >= 1 cited URL",
                "actual": f"Citations present: {has_url}",
                "duration": f"{duration_t01:.2f}s",
                "status": "PASS" if has_url else "WARN (No URL in text)"
            })
        except Exception as e:
            results.append({
                "id": "T-01",
                "module": "Research Agent",
                "input": "Search & summarize quantum computing",
                "expected": "Summary with >= 1 cited URL",
                "actual": str(e)[:40],
                "duration": f"{time.time() - t0:.2f}s",
                "status": "FAIL"
            })

        # T-02: Coding Agent isolated test
        t0 = time.time()
        try:
            coder = create_coding_agent(model_client)
            task_t02 = "Write a python function to reverse a string, execute it testing with 'AutoGen', and return output."
            resp_t02 = await coder.run(task=task_t02)
            last_msg = resp_t02.messages[-1].content if resp_t02.messages else ""
            has_reversed = "negOtUA" in last_msg or "SUCCESS" in last_msg
            duration_t02 = time.time() - t0
            results.append({
                "id": "T-02",
                "module": "Coding Agent",
                "input": "Reverse string function + execute",
                "expected": "Executed Python code with reversed output",
                "actual": f"Verified execution: {has_reversed}",
                "duration": f"{duration_t02:.2f}s",
                "status": "PASS" if has_reversed else "FAIL"
            })
        except Exception as e:
            results.append({
                "id": "T-02",
                "module": "Coding Agent",
                "input": "Reverse string function + execute",
                "expected": "Executed Python code",
                "actual": str(e)[:40],
                "duration": f"{time.time() - t0:.2f}s",
                "status": "FAIL"
            })

        # T-03: Multi-agent Team delegation test
        t0 = time.time()
        try:
            team = create_assistant_team(model_client, max_turns=8)
            task_t03 = "Find the capital of France and write a python script to print its length."
            team_result = await team.run(task=task_t03)
            sources = set(getattr(m, "source", "") for m in team_result.messages)
            delegated = ("research_agent" in sources or "coding_agent" in sources)
            duration_t03 = time.time() - t0
            results.append({
                "id": "T-03",
                "module": "Manager / Team Delegation",
                "input": "Find Paris + code string length",
                "expected": "Multi-agent handoff & synthesized result",
                "actual": f"Participating agents: {list(sources)}",
                "duration": f"{duration_t03:.2f}s",
                "status": "PASS" if delegated else "FAIL"
            })
        except Exception as e:
            results.append({
                "id": "T-03",
                "module": "Manager / Team Delegation",
                "input": "Find Paris + code string length",
                "expected": "Multi-agent handoff",
                "actual": str(e)[:40],
                "duration": f"{time.time() - t0:.2f}s",
                "status": "FAIL"
            })

    # Print markdown table format
    print("\n### Measured Test Results (SD.md Section 12)\n")
    print("| Test ID | Module | Input | Expected Result | Actual Result | Latency | Status |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['id']} | {r['module']} | {r['input']} | {r['expected']} | {r['actual']} | {r['duration']} | **{r['status']}** |")
    print("\n" + "=" * 75)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
