"""Research Agent: Specialized in factual information retrieval and web search."""

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from src.tools.search import search_web


RESEARCH_SYSTEM_MESSAGE = """You are the Research Agent, a specialized member of an AI multi-agent assistant team.

Your responsibilities:
1. Receive research tasks or factual queries delegated by the Manager Agent.
2. Use the 'search_web' tool to gather up-to-date, accurate real-world information.
3. Synthesize your findings into a clear, concise summary.
4. Explicitly cite your sources by including the URLs and titles returned by the search tool.

Strict Rules:
- ALWAYS call the 'search_web' tool for factual, current, or domain-specific questions.
- If the search tool returns no results or an error, report 'No results found' or explain the error honestly. NEVER fabricate facts or URLs.
- Do NOT attempt to write or execute code; focus solely on research and information retrieval.
- Once your research summary is ready, report it back clearly so the Manager Agent can use it.
"""


def create_research_agent(model_client: ChatCompletionClient) -> AssistantAgent:
    """Creates and returns the specialized Research Agent."""
    return AssistantAgent(
        name="research_agent",
        model_client=model_client,
        tools=[search_web],
        description="Specialized in conducting live web research, gathering facts, and citing sources.",
        system_message=RESEARCH_SYSTEM_MESSAGE,
    )
