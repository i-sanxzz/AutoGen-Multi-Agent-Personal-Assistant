"""Team Assembly: Configures and coordinates the Multi-Agent SelectorGroupChat."""

from typing import Optional
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_core.models import ChatCompletionClient

from .manager import create_manager_agent
from .research import create_research_agent
from .coding import create_coding_agent


TEAM_SELECTOR_PROMPT = """You are coordinating a multi-agent personal assistant team.

Available roles:
{roles}

Conversation history:
{history}

Follow these exact selection guidelines:
1. If the conversation just began or the user asked a new request, select 'manager_agent' to decompose the task.
2. If 'manager_agent' asked for web research, factual lookup, or news, select 'research_agent'.
3. If 'manager_agent' asked for writing, running, or testing Python code, select 'coding_agent'.
4. After 'research_agent' or 'coding_agent' finishes and reports their output, select 'manager_agent' to synthesize the final answer.
5. If 'manager_agent' has synthesized the final response and ended with TERMINATE, do not select any more specialized agents.

Select the next role from {participants} to speak. Output ONLY the role name.
"""


def create_assistant_team(
    model_client: ChatCompletionClient,
    max_turns: int = 15
) -> SelectorGroupChat:
    """Builds and returns the 3-agent SelectorGroupChat team."""
    manager = create_manager_agent(model_client)
    researcher = create_research_agent(model_client)
    coder = create_coding_agent(model_client)

    termination_condition = (
        TextMentionTermination("TERMINATE") |
        MaxMessageTermination(max_messages=max_turns)
    )

    team = SelectorGroupChat(
        participants=[manager, researcher, coder],
        model_client=model_client,
        termination_condition=termination_condition,
        selector_prompt=TEAM_SELECTOR_PROMPT,
        max_turns=max_turns,
    )

    return team
