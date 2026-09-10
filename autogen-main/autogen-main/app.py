"""Streamlit Interface for AutoGen Multi-Agent Personal Assistant.

Design Principles:
- Zero 'AI slob' aesthetic: No purple neon glows, no juvenile emojis, no bloated margins.
- Clean, high-density, developer-grade engineering layout.
- Stripped of default Streamlit loading animations (running man, spinners).
- Transparent multi-agent observability (inspectable agent traces, tool outputs, metrics).
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseChatMessage, ToolCallExecutionEvent, ToolCallRequestEvent

from src.client import get_model_client
from src.agents import create_assistant_team

# Ensure transcripts directory exists
TRANSCRIPTS_DIR = Path("transcripts")
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Preset Review Scenarios from SD.md Section 15
DEMO_SCENARIOS = {
    "Scenario 1: Grounded Research": {
        "prompt": "Research the current state of quantum error correction and summarize the top 3 developments.",
        "badge": "Research Agent (Web Search)",
        "expected": "Manager delegates to Research Agent -> search_web called -> Manager synthesizes top 3 with citations."
    },
    "Scenario 2: Project Breakdown": {
        "prompt": "I need to build a personal budgeting app. Break this into a project plan combining key feature requirements and a starter Python data structure.",
        "badge": "Collaborative (Research + Coding)",
        "expected": "Manager fans out to Research Agent + Coding Agent -> Code tested -> Manager synthesizes unified plan."
    },
    "Scenario 3: Coding & Local Execution": {
        "prompt": "Write a function to check if a string is a palindrome, and verify it works by running test cases.",
        "badge": "Coding Agent (Local Sandbox)",
        "expected": "Manager delegates to Coding Agent -> Code executed locally -> Verified stdout returned -> Manager synthesizes."
    }
}

# Page Configuration
st.set_page_config(
    page_title="AutoGen Multi-Agent Assistant",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Density CSS: Completely suppress default running animations and AI slob styling
st.markdown("""
<style>
    /* =========================================================================
       1. Completely remove default Streamlit running animation & decorations
       ========================================================================= */
    div[data-testid="stStatusWidget"],
    .stStatusWidget,
    div[data-testid="stDecoration"],
    header[data-testid="stHeader"],
    .stDeployButton,
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Suppress default spinner pulsing animations */
    .stSpinner, div[data-testid="stSpinner"] > div {
        animation: none !important;
        border-top-color: #64748b !important;
    }

    /* =========================================================================
       2. Developer-grade typography and crisp borders (No AI slob)
       ========================================================================= */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 2rem !important;
        max-width: 1250px !important;
    }

    /* Top system status header */
    .sys-header {
        border-bottom: 1px solid var(--border-color, #e2e8f0);
        padding-bottom: 12px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .sys-title {
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
    }

    .status-tag {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        background: #f8fafc;
        color: #475569;
    }

    /* Agent Message Cards */
    .agent-box {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
        background: #ffffff;
    }

    .agent-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 6px;
    }

    .badge {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 2px 7px;
        border-radius: 3px;
    }
    .badge-manager {
        background-color: #f3e8ff;
        color: #6b21a8;
        border: 1px solid #d8b4fe;
    }
    .badge-research {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #7dd3fc;
    }
    .badge-coding {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #6ee7b7;
    }
    .badge-user {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
    }

    /* Tool Call Details */
    .tool-box {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 12px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #0284c7;
        padding: 8px 12px;
        margin: 8px 0;
        border-radius: 2px;
    }

    /* Metrics Summary Bar */
    .metrics-bar {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 12px;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 10px 14px;
        margin-top: 14px;
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
    }
    .metric-item {
        display: flex;
        gap: 6px;
    }
    .metric-label {
        color: #64748b;
    }
    .metric-val {
        font-weight: 600;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = ""


# Sidebar Controls
with st.sidebar:
    st.markdown("### Architecture & Config")
    load_dotenv()
    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    provider = "OpenRouter" if "openrouter.ai" in base_url else ("Gemini" if "generativelanguage" in base_url else "OpenAI")

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Framework")
        st.code("AutoGen 0.7.5", language="text")
    with col_b:
        st.caption("Provider")
        st.code(provider, language="text")

    st.caption("Model & Endpoint")
    st.code(f"{model_name}\n{base_url}", language="text")

    if not api_key_present:
        st.error("OPENAI_API_KEY not found in .env")

    st.markdown("---")
    st.markdown("### Review Demo Scenarios")
    st.caption("Click a scenario to preload prompt (SD.md §15):")

    for title, data in DEMO_SCENARIOS.items():
        if st.button(title, use_container_width=True):
            st.session_state.selected_prompt = data["prompt"]

    st.markdown("---")
    st.markdown("### Session Controls")
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.history = []
        st.session_state.metrics = None
        st.session_state.last_transcript = None
        st.session_state.selected_prompt = ""
        st.rerun()


# Main Application Header
st.markdown("""
<div class="sys-header">
    <div>
        <h1 class="sys-title">AutoGen Multi-Agent Assistant — Inspection Console</h1>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
            Active Team: <strong>Manager Agent</strong> (Orchestrator) ⇄ 
            <strong>Research Agent</strong> (Search) ⇄ 
            <strong>Coding Agent</strong> (Local Sandbox)
        </div>
    </div>
    <div>
        <span class="status-tag">STATUS: READY</span>
    </div>
</div>
""", unsafe_allow_html=True)


# Async execution engine
async def run_multi_agent_pipeline(user_prompt: str):
    model_client = get_model_client()
    team = create_assistant_team(model_client, max_turns=14)

    start_time = time.time()
    events_log = []
    messages = []
    turn_counts = {}

    async for event in team.run_stream(task=user_prompt):
        if isinstance(event, ToolCallRequestEvent):
            calls = event.content if isinstance(event.content, list) else [event.content]
            for call in calls:
                fn_name = getattr(call, "name", str(call))
                events_log.append({
                    "type": "tool_call",
                    "name": fn_name,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

        elif isinstance(event, ToolCallExecutionEvent):
            results = event.content if isinstance(event.content, list) else [event.content]
            for r in results:
                content = getattr(r, "content", str(r))
                events_log.append({
                    "type": "tool_result",
                    "content": content,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

        elif isinstance(event, BaseChatMessage):
            src = getattr(event, "source", "Unknown")
            cnt = getattr(event, "content", "")
            turn_counts[src] = turn_counts.get(src, 0) + 1
            msg_obj = {
                "source": src,
                "content": cnt,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            messages.append(msg_obj)
            events_log.append({"type": "chat_message", **msg_obj})

        elif isinstance(event, TaskResult):
            total_duration = time.time() - start_time
            stop_reason = getattr(event, "stop_reason", "Completed")
            
            # Save transcript
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = TRANSCRIPTS_DIR / f"transcript_{session_id}.json"
            transcript_data = {
                "task": user_prompt,
                "duration_seconds": round(total_duration, 2),
                "stop_reason": stop_reason,
                "turn_counts": turn_counts,
                "events": events_log,
                "messages": messages
            }
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(transcript_data, f, indent=2)

            return {
                "messages": messages,
                "events": events_log,
                "metrics": {
                    "duration": f"{total_duration:.2f}s",
                    "stop_reason": stop_reason,
                    "turns": len(messages),
                    "breakdown": turn_counts,
                    "log_file": str(log_file)
                }
            }


# Tabs for High-Density Inspection
tab_conversation, tab_traces, tab_transcript = st.tabs([
    "Final Output & Summary", 
    "Multi-Agent Trace Timeline", 
    "Audit Log (JSON)"
])


# Prompt Input Area
with st.container():
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        default_val = st.session_state.selected_prompt or ""
        user_query = st.text_input(
            "User Request", 
            value=default_val, 
            placeholder="Type your request or pick a review scenario from the left sidebar...",
            label_visibility="collapsed"
        )
    with col_btn:
        execute_clicked = st.button("Execute Task", use_container_width=True, type="primary")

if execute_clicked and user_query.strip():
    # Simple static execution indicator (NO bouncing animations, NO AI slob)
    status_placeholder = st.empty()
    status_placeholder.info(f"Delegating task across agents: \"{user_query.strip()}\"...")
    
    try:
        result = asyncio.run(run_multi_agent_pipeline(user_query.strip()))
        st.session_state.history = result["messages"]
        st.session_state.events = result["events"]
        st.session_state.metrics = result["metrics"]
        st.session_state.last_transcript = result
        status_placeholder.empty()
        st.session_state.selected_prompt = ""
    except Exception as e:
        status_placeholder.empty()
        st.error(f"Execution Error: {str(e)}")


# -----------------------------------------------------------------------------
# TAB 1: Final Output & Conversation
# -----------------------------------------------------------------------------
with tab_conversation:
    if not st.session_state.history:
        st.caption("No task executed yet. Select a scenario from the sidebar or enter a prompt above.")
    else:
        # Separate the user request and final synthesized response
        user_msg = next((m for m in st.session_state.history if m["source"] == "user"), None)
        manager_msgs = [m for m in st.session_state.history if m["source"] == "manager_agent"]
        final_msg = manager_msgs[-1] if manager_msgs else st.session_state.history[-1]

        if user_msg:
            st.markdown(f"""
            <div class="agent-box">
                <div class="agent-header">
                    <span class="badge badge-user">User Request</span>
                    <span style="font-size: 11px; color: #94a3b8;">{user_msg['timestamp']}</span>
                </div>
                <div>{user_msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

        if final_msg:
            clean_final = final_msg["content"].replace("TERMINATE", "").strip()
            st.markdown(f"""
            <div class="agent-box" style="border-left: 3px solid #7c3aed;">
                <div class="agent-header">
                    <span class="badge badge-manager">Synthesized Final Response</span>
                    <span style="font-size: 11px; color: #94a3b8;">{final_msg['timestamp']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(clean_final)

        # Performance Metrics Bar
        if st.session_state.metrics:
            m = st.session_state.metrics
            breakdown_str = " | ".join([f"{k}: {v}" for k, v in m["breakdown"].items()])
            st.markdown(f"""
            <div class="metrics-bar">
                <div class="metric-item">
                    <span class="metric-label">Wall-Clock Time:</span>
                    <span class="metric-val">{m['duration']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Message Turns:</span>
                    <span class="metric-val">{m['turns']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Halt Condition:</span>
                    <span class="metric-val">{m['stop_reason']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Agent Activity:</span>
                    <span class="metric-val">{breakdown_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# TAB 2: Multi-Agent Trace Timeline
# -----------------------------------------------------------------------------
with tab_traces:
    if not st.session_state.history:
        st.caption("Agent trace will appear here after task execution.")
    else:
        st.caption("Step-by-step inter-agent handoff trace proving task delegation:")
        for idx, event in enumerate(st.session_state.get("events", []), start=1):
            etype = event.get("type")

            if etype == "chat_message":
                source = event.get("source", "agent")
                ts = event.get("timestamp", "")
                content = event.get("content", "")
                
                badge_class = "badge-manager" if "manager" in source else ("badge-research" if "research" in source else ("badge-coding" if "coding" in source else "badge-user"))
                st.markdown(f"""
                <div class="agent-box">
                    <div class="agent-header">
                        <span class="badge {badge_class}">Step {idx} — {source}</span>
                        <span style="font-size: 11px; color: #94a3b8;">{ts}</span>
                    </div>
                    <div>{content.replace("TERMINATE", "<code>[TERMINATE]</code>")}</div>
                </div>
                """, unsafe_allow_html=True)

            elif etype == "tool_call":
                st.markdown(f"""
                <div class="tool-box">
                    <strong>⚡ Tool Call Invoked:</strong> <code>{event.get('name')}</code>
                    <span style="float: right; color: #94a3b8;">{event.get('timestamp')}</span>
                </div>
                """, unsafe_allow_html=True)

            elif etype == "tool_result":
                snippet = event.get("content", "")[:350]
                st.markdown(f"""
                <div class="tool-box" style="border-left-color: #10b981;">
                    <strong>✓ Tool Output:</strong>
                    <pre style="margin: 4px 0 0 0; white-space: pre-wrap; font-size: 11px;">{snippet}...</pre>
                </div>
                """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# TAB 3: Audit Log (JSON)
# -----------------------------------------------------------------------------
with tab_transcript:
    if not st.session_state.last_transcript:
        st.caption("No transcript data available.")
    else:
        st.caption("Full verifiable session payload saved to disk:")
        st.json(st.session_state.last_transcript)
        st.download_button(
            "Download Transcript JSON",
            data=json.dumps(st.session_state.last_transcript, indent=2),
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
