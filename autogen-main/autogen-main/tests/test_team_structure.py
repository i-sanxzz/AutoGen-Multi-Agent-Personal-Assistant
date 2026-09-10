"""Structural unit tests for agent initialization and team assembly (Milestones 3 & 4)."""

import pytest
from src.client import get_model_client
from src.agents.manager import create_manager_agent
from src.agents.research import create_research_agent
from src.agents.coding import create_coding_agent
from src.agents.team import create_assistant_team


@pytest.fixture
def mock_client():
    """Provides a configured client with dummy key for structural validation."""
    return get_model_client(api_key="sk-test-structural-verification-key")


def test_research_agent_init(mock_client):
    """Verify Research Agent configuration, description, and tool binding."""
    agent = create_research_agent(mock_client)
    assert agent.name == "research_agent"
    tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in agent._tools]
    assert "search_web" in tool_names
    assert "research" in agent.description.lower()


def test_coding_agent_init(mock_client):
    """Verify Coding Agent configuration, description, and tool binding."""
    agent = create_coding_agent(mock_client)
    assert agent.name == "coding_agent"
    tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in agent._tools]
    assert "execute_python_code" in tool_names
    assert "code" in agent.description.lower()


def test_manager_agent_init(mock_client):
    """Verify Manager Agent configuration and role."""
    agent = create_manager_agent(mock_client)
    assert agent.name == "manager_agent"
    assert "manager" in agent.description.lower() or "coordinator" in agent.description.lower()


def test_team_assembly(mock_client):
    """Verify 3-agent SelectorGroupChat team construction."""
    team = create_assistant_team(mock_client, max_turns=10)
    participant_names = [p.name for p in team._participants]
    assert "manager_agent" in participant_names
    assert "research_agent" in participant_names
    assert "coding_agent" in participant_names
    assert len(participant_names) == 3
