"""
News Router — handles area-based news search using Tavily API.
"""

from fastapi import APIRouter, Query, HTTPException
from app.services.tavily_service import search_news

router = APIRouter()


@router.get(
    "/search",
    summary="Search for news in a specific area or topic",
    response_description="List of relevant news articles with title, summary, source, and date",
)
async def search_news_endpoint(
    query: str = Query(
        ...,
        description="Topic or area to search news for (e.g., 'AI developments', 'tech industry', 'machine learning')",
        min_length=2,
        max_length=300,
    ),
    max_results: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of news articles to return (1–20)",
    ),
):
    """
    Searches for recent news articles on the given topic using Tavily API.

    - **query**: The area/topic to search (e.g., "AI startup funding", "Indonesian tech news")
    - **max_results**: How many results to return (default: 5, max: 20)

    Returns a list of articles with title, summary, source URL, and published date.
    """
    results = await search_news(query=query, max_results=max_results)
    return {
        "query": query,
        "total_results": len(results),
        "articles": results,
    }
