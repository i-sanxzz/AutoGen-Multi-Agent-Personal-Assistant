"""Web search tool using DuckDuckGo (ddgs) for grounded research."""

from typing import List, Dict, Any
from ddgs import DDGS


def search_web(query: str, max_results: int = 5) -> str:
    """Performs a live web search using DuckDuckGo.
    
    Args:
        query: The search query string.
        max_results: Maximum number of search results to return (default 5).

    Returns:
        A structured string containing titles, snippets, and URLs of search results,
        or an explicit message if no results or an error occurred.
    """
    if not query or not query.strip():
        return "Search error: Query cannot be empty."

    try:
        results = list(DDGS().text(query.strip(), max_results=max_results))
        if not results:
            return f"No search results found for query: '{query}'."

        formatted_results = []
        for i, res in enumerate(results, start=1):
            title = res.get("title", "No Title")
            snippet = res.get("body", "No description available.")
            url = res.get("href", "")
            formatted_results.append(
                f"[{i}] {title}\n    URL: {url}\n    Summary: {snippet}"
            )

        return "\n\n".join(formatted_results)

    except Exception as e:
        return f"Search error occurred: {str(e)}. Please retry or refine the query."
