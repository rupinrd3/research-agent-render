"""
Tool Definitions

OpenAI-compatible function definitions for all research tools.
"""

from typing import List, Dict, Any


WEB_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information, news, articles, "
            "and general knowledge. Best for recent events, trends, "
            "and practical information. Returns up to 20 results."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Be specific and use keywords.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-20)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20,
                },
                "date_filter": {
                    "type": "string",
                    "enum": ["day", "week", "month", "year", None],
                    "description": (
                        "Filter by recency. Use for time-sensitive queries."
                    ),
                    "default": None,
                },
            },
            "required": ["query"],
        },
    },
}


ARXIV_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "arxiv_search",
        "description": (
            "Search academic papers on ArXiv. Best for research papers, "
            "ML/AI topics, physics, math, and computer science. "
            "Returns paper metadata and abstracts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Use technical terms.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum papers to return (1-50)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50,
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                    "description": "Sort order for results",
                    "default": "relevance",
                },
                "date_from": {
                    "type": "string",
                    "description": "Filter papers from this date (YYYY-MM-DD)",
                    "default": None,
                },
            },
            "required": ["query"],
        },
    },
}


GITHUB_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "github_search",
        "description": (
            "Search GitHub for repositories, code, or users. "
            "Best for finding implementations, libraries, and "
            "open-source projects."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Use project names or keywords.",
                },
                "search_type": {
                    "type": "string",
                    "enum": ["repositories", "code", "users"],
                    "description": "What to search for",
                    "default": "repositories",
                },
                "sort": {
                    "type": "string",
                    "enum": ["stars", "forks", "updated"],
                    "description": "Sort order (repositories only)",
                    "default": "stars",
                },
                "language": {
                    "type": "string",
                    "description": (
                        "Filter by language (e.g., 'Python', 'JavaScript')"
                    ),
                    "default": None,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results (1-30)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 30,
                },
            },
            "required": ["query"],
        },
    },
}


PDF_TO_TEXT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "pdf_to_text",
        "description": (
            "Extract text from PDF documents. Use when you find a "
            "relevant PDF paper or document that you need to read. "
            "Returns structured text content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "PDF URL (https://...) or file path",
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum pages to extract (default: 50)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 200,
                },
            },
            "required": ["source"],
        },
    },
}


FINISH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "finish",
        "description": (
            "Call this only after you have gathered enough high-quality evidence to craft the final Deep Research Report. "
            "The output should be a detailed narrative that adapts the section structure to the query, mixes prose with tables/bullets, "
            "and documents how evidence was gathered."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "report": {
                    "type": "string",
                    "description": (
                        "Comprehensive Markdown Deep Research Report (>=600 words) with adaptive structure:\n"
                        "1. # {Topic Title}\n"
                        "2. ## TL;DR - 4-6 bullet takeaways with quantified facts when possible.\n"
                        "3. ## Methodology & Evidence Quality - summarize tools/sources, recency filters, and explicitly state a Coverage gaps & confidence clause.\n"
                        "4. ## Key Facts - table or bullet list of the most critical quantitative facts (specs, timelines, stakeholder impacts, etc.) tailored to the topic.\n"
                        "5. ## Findings & Analysis - create topic-appropriate sections (### ...) that can span business, technical, policy, societal, academic, political, or cultural angles.\n"
                        "6. ## Implementation / Impact - deployments, market traction, costs, or architecture as relevant.\n"
                        "7. ## Gaps & Open Questions - highlight missing data or research needs.\n"
                        "8. ## Recommended Next Steps - actionable guidance for decision-makers.\n"
                        "Do not include a Sources section in the report body; sources are supplied separately via the structured sources field."
                    ),
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered list of source URLs cited in the report (matches [#] references).",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in the report's completeness (0-1).",
                    "default": 0.8,
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": ["report", "sources"],
        },
    },
}


def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get all tool definitions for agent.

    Returns:
        List of OpenAI-compatible tool definitions
    """
    return [
        WEB_SEARCH_DEFINITION,
        ARXIV_SEARCH_DEFINITION,
        GITHUB_SEARCH_DEFINITION,
        PDF_TO_TEXT_DEFINITION,
        FINISH_DEFINITION,
    ]
