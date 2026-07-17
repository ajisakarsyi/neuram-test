"""
Tavily Service — searches for news articles using the Tavily Search API.

Tavily is optimized for real-time web search and returns structured results
with titles, summaries, source URLs, and publish dates.
"""

import os
from typing import Optional
import httpx
from fastapi import HTTPException

# Tavily API endpoint
TAVILY_API_URL = "https://api.tavily.com/search"


async def search_news(query: str, max_results: int = 5) -> list[dict]:
    """
    Searches for recent news articles related to the given query using Tavily.

    Args:
        query: The search topic or area (e.g., "AI developments 2025").
        max_results: Maximum number of articles to return (1–20).

    Returns:
        List of dicts, each with: title, summary, url, published_date, source.

    Raises:
        HTTPException: On API failure or missing credentials.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TAVILY_API_KEY is not set. Please configure your .env file.",
        )

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",      # "basic" is faster; use "advanced" for deeper results
        "topic": "news",              # Focus on news content
        "max_results": max_results,
        "include_answer": False,      # We want raw articles, not a summarized answer
        "include_raw_content": False, # Skip raw HTML — we only need metadata
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(TAVILY_API_URL, json=payload)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Tavily API request timed out.")
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to reach Tavily API: {e}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Tavily API error {response.status_code}: {response.text}",
        )

    data = response.json()

    # Extract and format articles from Tavily response
    raw_results = data.get("results", [])
    articles = []

    for item in raw_results:
        articles.append(
            {
                # Article title from Tavily
                "title": item.get("title", "No title"),
                # Short excerpt/summary provided by Tavily
                "summary": item.get("content", "No summary available."),
                # Original article URL
                "url": item.get("url", ""),
                # Publication date (may be None if Tavily couldn't determine it)
                "published_date": item.get("published_date", None),
                # Source domain extracted from URL
                "source": _extract_domain(item.get("url", "")),
                # Relevance score from Tavily (0.0 – 1.0)
                "relevance_score": round(item.get("score", 0.0), 4),
            }
        )

    return articles


def _extract_domain(url: str) -> str:
    """
    Extracts the domain name from a URL for display as the 'source'.

    Example: "https://www.bbc.com/news/article" → "bbc.com"
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        # Remove 'www.' prefix if present
        domain = parsed.netloc.replace("www.", "")
        return domain if domain else url
    except Exception:
        return url
