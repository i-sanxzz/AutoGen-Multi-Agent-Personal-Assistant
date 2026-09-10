"""Unit tests for Research and Coding tools (Milestone 2 & 3)."""

import pytest
from src.tools.search import search_web
from src.tools.executor import execute_python_code


def test_search_web_empty_query():
    """Verify search tool handles empty queries gracefully without crashing."""
    result = search_web("")
    assert "Query cannot be empty" in result or "error" in result.lower()


def test_search_web_live():
    """Verify search tool performs live web search and formats citations."""
    result = search_web("Python programming language", max_results=2)
    assert "[1]" in result
    assert "URL:" in result
    assert "Summary:" in result


@pytest.mark.asyncio
async def test_execute_python_code_success():
    """Verify code executor runs valid code and captures stdout."""
    code = "print(100 + 200)"
    result = await execute_python_code(code)
    assert "SUCCESS" in result
    assert "300" in result


@pytest.mark.asyncio
async def test_execute_python_code_syntax_error():
    """Verify code executor handles syntax errors and returns actual trace (T-05)."""
    code = "def invalid_python(: print('error')"
    result = await execute_python_code(code)
    assert "FAILED" in result
    assert "SyntaxError" in result


@pytest.mark.asyncio
async def test_execute_python_code_empty():
    """Verify code executor rejects empty code strings gracefully."""
    result = await execute_python_code("   ")
    assert "No code provided" in result
