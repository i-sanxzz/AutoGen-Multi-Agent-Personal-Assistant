"""Runner CLI for AutoGen Multi-Agent Personal Assistant.

Supports:
  1. Interactive prompt loop
  2. Direct query execution via CLI argument
  3. Pre-configured demo scenarios (Scenario 1: Research, Scenario 2: Task Breakdown, Scenario 3: Coding)
  4. Real-time streaming output with clean agent badges
  5. Empirical metric logging (latency, message turns, agent participation)
  6. Transcript saving for evaluation and review defensibility
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseChatMessage, ToolCallExecutionEvent, ToolCallRequestEvent

from src.client import get_model_client
from src.agents import create_assistant_team

# Ensure transcripts directory exists
TRANSCRIPTS_DIR = Path("transcripts")
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Pre-defined Review Demo Scenarios from SD.md Section 15
DEMO_SCENARIOS = {
    "1": {
        "title": "Scenario 1: Grounded Research",
        "prompt": "Research the current state of quantum error correction and summarize the top 3 developments.",
        "expected_flow": "Manager -> Research Agent (search_web) -> Manager Synthesis",
    },
    "2": {
        "title": "Scenario 2: Complex Task Breakdown (Collaborative)",
        "prompt": "I need to build a personal budgeting app. Break this into a project plan combining key feature requirements and a starter Python data structure.",
        "expected_flow": "Manager -> Research Agent + Coding Agent -> Manager Synthesis",
    },
    "3": {
        "title": "Scenario 3: Coding & Verified Local Execution",
        "prompt": "Write a function to check if a string is a palindrome, and verify it works by running test cases.",
        "expected_flow": "Manager -> Coding Agent (execute_python_code) -> Manager Synthesis",
    },
}

# Color formatting constants for terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_agent_badge(source: str) -> str:
    """Returns a color-coded tag for each agent."""
    if "manager" in source.lower():
        return f"{BOLD}{MAGENTA}[Manager Agent]{RESET}"
    elif "research" in source.lower():
        return f"{BOLD}{CYAN}[Research Agent]{RESET}"
    elif "coding" in source.lower():
        return f"{BOLD}{GREEN}[Coding Agent]{RESET}"
    elif "user" in source.lower():
        return f"{BOLD}{BLUE}[User]{RESET}"
    else:
        return f"{BOLD}[{source}]{RESET}"


async def execute_task(task_prompt: str, scenario_info: dict = None):
    """Executes a single user prompt through the multi-agent team."""
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print(f"\n{YELLOW}[!] OPENAI_API_KEY is not configured.{RESET}")
        print("Please configure your .env file with your OpenAI or OpenRouter key:")
        print("  cp .env.example .env\n")
        return

    try:
        model_client = get_model_client()
    except Exception as e:
        print(f"\n{YELLOW}[X] Model client initialization failed: {e}{RESET}\n")
        return

    team = create_assistant_team(model_client, max_turns=15)

    print("\n" + "=" * 70)
    if scenario_info:
        print(f" {BOLD}▶ {scenario_info['title']}{RESET}")
        print(f"   {DIM}Expected Flow: {scenario_info['expected_flow']}{RESET}")
    else:
        print(f" {BOLD}▶ Executing Task{RESET}")
    print("=" * 70)
    print(f"{BOLD}User Request:{RESET} {task_prompt}\n")

    start_time = time.time()
    transcript = []
    agent_turn_counts = {}

    try:
        async for event in team.run_stream(task=task_prompt):
            # Capture tool request events
            if isinstance(event, ToolCallRequestEvent):
                calls = event.content if isinstance(event.content, list) else [event.content]
                for call in calls:
                    fn_name = getattr(call, "name", str(call))
                    print(f"  {YELLOW}⚡ [Tool Call Request]{RESET} -> {fn_name}")

            # Capture tool execution events
            elif isinstance(event, ToolCallExecutionEvent):
                results = event.content if isinstance(event.content, list) else [event.content]
                for r in results:
                    content_snippet = getattr(r, "content", str(r))[:120].replace("\n", " ")
                    print(f"  {DIM}✓ [Tool Result]{RESET} {content_snippet}...")

            # Capture chat messages between agents
            elif isinstance(event, BaseChatMessage):
                source = getattr(event, "source", "Unknown")
                content = getattr(event, "content", "")
                
                agent_turn_counts[source] = agent_turn_counts.get(source, 0) + 1
                
                # Format message content cleanly
                badge = format_agent_badge(source)
                print(f"\n{badge}")
                print("-" * 50)
                # Clean up TERMINATE token display from user presentation
                clean_content = content.replace("TERMINATE", f"{DIM}[TERMINATE]{RESET}")
                print(clean_content)
                print("-" * 50)

                transcript.append({
                    "timestamp": datetime.now().isoformat(),
                    "source": source,
                    "content": content
                })

            elif isinstance(event, TaskResult):
                total_duration = time.time() - start_time
                stop_reason = getattr(event, "stop_reason", "Completed")

                print("\n" + "=" * 70)
                print(f" {BOLD}✓ Task Finished — Execution Metrics{RESET}")
                print("=" * 70)
                print(f" • Total Wall-Clock Time:  {total_duration:.2f}s")
                print(f" • Stop Reason:            {stop_reason}")
                print(f" • Total Message Turns:    {len(transcript)}")
                print(f" • Agent Turn Breakdown:   {dict(agent_turn_counts)}")
                print("=" * 70)

                # Save transcript to file for inspection
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = TRANSCRIPTS_DIR / f"transcript_{session_id}.json"
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "task": task_prompt,
                        "duration_seconds": round(total_duration, 2),
                        "stop_reason": stop_reason,
                        "agent_turn_counts": agent_turn_counts,
                        "messages": transcript
                    }, f, indent=2)
                print(f"{DIM}Log saved to: {log_file}{RESET}\n")

    except Exception as e:
        print(f"\n{YELLOW}[X] Execution error during team run: {e}{RESET}\n")


def print_interactive_menu():
    print("\n" + "=" * 60)
    print(f" {BOLD}AutoGen Multi-Agent Personal Assistant{RESET}")
    print("=" * 60)
    print(" Select an option:")
    print("  [1] Demo Scenario 1: Grounded Research (Web Search)")
    print("  [2] Demo Scenario 2: Project Breakdown (Research + Coding)")
    print("  [3] Demo Scenario 3: Coding & Local Execution")
    print("  [c] Custom user prompt")
    print("  [q] Quit")
    print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="Run AutoGen Multi-Agent Personal Assistant")
    parser.add_argument("query", nargs="?", help="Direct query string to process")
    parser.add_argument("--demo", choices=["1", "2", "3"], help="Run one of the preset review scenarios")
    args = parser.parse_args()

    if args.demo:
        scenario = DEMO_SCENARIOS[args.demo]
        await execute_task(scenario["prompt"], scenario_info=scenario)
        return

    if args.query:
        await execute_task(args.query)
        return

    # Interactive Loop
    while True:
        print_interactive_menu()
        choice = input("Enter choice (1/2/3/c/q): ").strip().lower()

        if choice in ["q", "exit", "quit"]:
            print("Exiting assistant. Goodbye!")
            break
        elif choice in ["1", "2", "3"]:
            scenario = DEMO_SCENARIOS[choice]
            await execute_task(scenario["prompt"], scenario_info=scenario)
        elif choice == "c":
            custom_prompt = input("\nEnter your custom prompt:\n> ").strip()
            if custom_prompt:
                await execute_task(custom_prompt)
        else:
            print("Invalid selection. Please enter 1, 2, 3, c, or q.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(0)
