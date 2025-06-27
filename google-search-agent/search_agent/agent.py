"""
Google Search Agent using ADK

This agent provides intelligent web search capabilities using Google's search API
through ADK's built-in Google Search tool.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import GoogleSearchTool
from typing import Dict, List
import datetime
import re

# Initialize Google Search tool
google_search = GoogleSearchTool(
    name="google_search",
    # The tool will use environment variables for API credentials
)

def search_and_summarize(query: str, num_results: int = 5) -> Dict[str, str]:
    """
    Perform a Google search and provide a summary of results.
    
    Args:
        query: The search query to execute
        num_results: Number of search results to include (default: 5)
    
    Returns:
        Dictionary with search results and summary
    """
    if not query or not query.strip():
        return {
            "status": "error",
            "message": "Please provide a search query."
        }
    
    try:
        # Perform the search using Google Search tool
        # Note: The actual search is handled by the LLM agent using the tool
        return {
            "status": "success",
            "query": query.strip(),
            "message": f"I'll search for '{query}' and provide you with the most relevant results.",
            "num_results": min(num_results, 10)  # Limit to max 10 results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }

def search_news(query: str, days_back: int = 7) -> Dict[str, str]:
    """
    Search for recent news articles on a topic.
    
    Args:
        query: The news topic to search for
        days_back: How many days back to search (default: 7)
    
    Returns:
        Dictionary with news search parameters
    """
    if not query or not query.strip():
        return {
            "status": "error", 
            "message": "Please provide a news topic to search for."
        }
    
    # Create a news-specific search query
    news_query = f"{query.strip()} news"
    if days_back <= 7:
        news_query += " recent"
    
    return {
        "status": "success",
        "query": news_query,
        "original_topic": query.strip(),
        "timeframe": f"last {days_back} days",
        "message": f"I'll search for recent news about '{query}' from the last {days_back} days."
    }

def search_academic(query: str) -> Dict[str, str]:
    """
    Search for academic papers and scholarly articles.
    
    Args:
        query: The academic topic to search for
    
    Returns:
        Dictionary with academic search parameters
    """
    if not query or not query.strip():
        return {
            "status": "error",
            "message": "Please provide an academic topic to search for."
        }
    
    # Create an academic-focused search query
    academic_query = f"{query.strip()} academic papers research studies"
    
    return {
        "status": "success",
        "query": academic_query,
        "original_topic": query.strip(),
        "search_type": "academic",
        "message": f"I'll search for academic papers and research on '{query}'."
    }

def search_how_to(topic: str) -> Dict[str, str]:
    """
    Search for how-to guides and tutorials on a specific topic.
    
    Args:
        topic: The topic to find tutorials for
    
    Returns:
        Dictionary with how-to search parameters
    """
    if not topic or not topic.strip():
        return {
            "status": "error",
            "message": "Please provide a topic you'd like to learn about."
        }
    
    # Create a how-to focused search query
    how_to_query = f"how to {topic.strip()} tutorial guide"
    
    return {
        "status": "success",
        "query": how_to_query,
        "original_topic": topic.strip(),
        "search_type": "tutorial",
        "message": f"I'll search for tutorials and guides on how to {topic}."
    }

def search_local(query: str, location: str = "") -> Dict[str, str]:
    """
    Search for local businesses or services.
    
    Args:
        query: What to search for (e.g., "restaurants", "dentist")
        location: Optional location (e.g., "San Francisco", "near me")
    
    Returns:
        Dictionary with local search parameters
    """
    if not query or not query.strip():
        return {
            "status": "error",
            "message": "Please specify what you're looking for locally."
        }
    
    # Create a local search query
    local_query = query.strip()
    if location and location.strip():
        local_query += f" in {location.strip()}"
    else:
        local_query += " near me"
    
    return {
        "status": "success",
        "query": local_query,
        "business_type": query.strip(),
        "location": location.strip() if location else "near me",
        "search_type": "local",
        "message": f"I'll search for {query} locally" + (f" in {location}" if location else " near you") + "."
    }

# Create the main search agent
root_agent = LlmAgent(
    name="GoogleSearchAgent",
    model="gemini-2.0-flash",
    description="An intelligent web search assistant powered by Google Search",
    instruction="""You are an expert web search assistant with access to Google Search. Your role is to:

🔍 **SEARCH CAPABILITIES:**
- Perform comprehensive web searches using Google
- Find current information, news, and academic papers  
- Locate how-to guides and tutorials
- Search for local businesses and services
- Provide summaries and key insights from search results

📋 **SEARCH STRATEGY:**
- Always use the google_search tool to get current, accurate information
- For general queries, search broadly then narrow down based on results
- For news, focus on recent and credible sources
- For tutorials, prioritize step-by-step guides and official documentation
- For local searches, include location context

💡 **RESPONSE STYLE:**
- Start by acknowledging what you're searching for
- Present search results in a clear, organized format
- Highlight the most relevant and credible sources
- Provide context and explain why sources are trustworthy
- Offer to search for more specific information if needed
- Include direct links when possible

🎯 **SPECIALIZED SEARCHES:**
Use these helper functions to refine searches:
- search_and_summarize(): General web search with summary
- search_news(): Recent news and current events  
- search_academic(): Scholarly articles and research papers
- search_how_to(): Tutorials and instructional content
- search_local(): Local businesses and services

**EXAMPLE INTERACTIONS:**
- "I'll search for the latest information about [topic]..."
- "Let me find recent news about [subject]..."
- "I'll look for tutorials on how to [skill]..."
- "Searching for [business type] near [location]..."

Always verify information is current and cite your sources. If search results seem outdated or insufficient, offer to search with different terms or approaches.""",
    
    tools=[
        google_search,
        search_and_summarize, 
        search_news,
        search_academic,
        search_how_to,
        search_local
    ]
) 