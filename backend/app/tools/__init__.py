"""
Research Tools

This module provides four research tools for the agent:
- Web Search (DuckDuckGo/SerpAPI)
- ArXiv Search
- GitHub Search
- PDF Parser
"""

from .web_search import web_search
from .arxiv_search import arxiv_search
from .github_search import github_search
from .pdf_parser import pdf_to_text
from .definitions import (
    get_all_tool_definitions,
    WEB_SEARCH_DEFINITION,
    ARXIV_SEARCH_DEFINITION,
    GITHUB_SEARCH_DEFINITION,
    PDF_TO_TEXT_DEFINITION,
)

__all__ = [
    "web_search",
    "arxiv_search",
    "github_search",
    "pdf_to_text",
    "WEB_SEARCH_DEFINITION",
    "ARXIV_SEARCH_DEFINITION",
    "GITHUB_SEARCH_DEFINITION",
    "PDF_TO_TEXT_DEFINITION",
    "get_all_tool_definitions",
]
