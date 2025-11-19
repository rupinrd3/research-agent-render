"""
GitHub Search Tool

Implements repository and code search using the GitHub API.

Features:
- Repository, code, and user search
- Content pipeline integration for ranking
- Language filtering
- Multiple sort options
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


async def github_search(
    query: str,
    search_type: str = "repositories",
    sort: str = "stars",
    language: Optional[str] = None,
    max_results: int = 10,
    content_pipeline=None,
) -> Dict[str, Any]:
    """
    Search GitHub and return results.

    Args:
        query: Search query string
        search_type: 'repositories', 'code', or 'users'
        sort: Sort order ('stars', 'forks', 'updated')
        language: Filter by programming language
        max_results: Number of results (1-30)
        content_pipeline: Optional content pipeline for processing results

    Returns:
        Dict containing:
            - repositories/code/users: List of search results (processed if pipeline provided)
            - total_found: Total number of results found
            - timestamp: Search timestamp
            - query: Original query
            - pipeline_stats: Pipeline statistics (if pipeline used)

    Raises:
        Exception: If search fails
    """
    try:
        logger.info(
            f"[GithubSearch] Starting | query='{query}' type={search_type} sort={sort}"
        )

        # Ensure max_results is an integer (LLM may pass as string)
        max_results = int(max_results)
        max_results = max(1, min(max_results, 30))  # Clamp to 1-30

        # Build query with language filter
        search_query = query
        if language:
            search_query = f"{query} language:{language}"

        # Get GitHub token from environment (optional but increases rate limit)
        github_token = os.getenv("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        # Perform search based on type
        base_url = "https://api.github.com/search"
        endpoint = f"{base_url}/{search_type}"

        params = {
            "q": search_query,
            "per_page": min(max_results, 100),
        }

        # Add sort parameter for repositories
        if search_type == "repositories":
            params["sort"] = sort

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                endpoint, params=params, headers=headers
            )
            response.raise_for_status()
            data = response.json()

        # Process results based on type
        if search_type == "repositories":
            results = await _process_repositories(data.get("items", []))
        elif search_type == "code":
            results = _process_code(data.get("items", []))
        elif search_type == "users":
            results = _process_users(data.get("items", []))
        else:
            results = []

        logger.info(f"[GithubSearch] Retrieved {len(results)} {search_type}")

        # Process through content pipeline if provided (for repositories)
        processed_results = results
        pipeline_stats = None
        pipeline_notes: List[str] = []

        if content_pipeline and results and search_type == "repositories":
            try:
                logger.info(
                    f"[GithubSearch] Processing {len(results)} repos via content pipeline"
                )
                pipeline_output = await content_pipeline.process_github_results(
                    results, query
                )
                processed_results = pipeline_output.get("top_items", results)
                pipeline_stats = pipeline_output.get("stats")
                pipeline_notes = pipeline_output.get("notes", [])
                logger.info(
                    f"[GithubSearch] Pipeline reduced {len(results)} → {len(processed_results)} repos"
                )
            except Exception as e:
                logger.error(f"Content pipeline processing failed: {e}")
                # Fall back to raw results if pipeline fails
                processed_results = results

        response = {
            search_type: processed_results,
            "total_found": data.get("total_count", len(processed_results)),
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "status": "success",
            "notes": pipeline_notes,
        }

        if pipeline_stats:
            response["pipeline_stats"] = pipeline_stats

        logger.info(
            f"[GithubSearch] Complete | returned={len(processed_results)} status=success type={search_type}"
        )

        return response

    except Exception as e:
        logger.error(f"[GithubSearch] Failed: {e}")
        return {
            search_type: [],
            "total_found": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "status": "error",
            "error": str(e),
        }


async def _process_repositories(items: List[Dict]) -> List[Dict]:
    """
    Process repository search results.

    Args:
        items: Raw repository items from API

    Returns:
        Processed repository list
    """
    repositories = []
    for item in items:
        repo = {
            "name": item.get("name", ""),
            "full_name": item.get("full_name", ""),
            "description": item.get("description", ""),
            "snippet": item.get("description", "")[:200] if item.get("description") else "",
            "url": item.get("html_url", ""),
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "watchers": item.get("watchers_count", 0),
            "language": item.get("language", ""),
            "topics": item.get("topics", []),
            "last_updated": item.get("updated_at", ""),
            "created_at": item.get("created_at", ""),
            "license": item.get("license", {}).get("name", "") if item.get("license") else "",
            "is_fork": item.get("fork", False),
            "has_wiki": item.get("has_wiki", False),
            "homepage": item.get("homepage", ""),
            "content_type": "github_repository",
            "relevance_score": 0.8,  # Default relevance
        }
        repositories.append(repo)
    return repositories


def _process_code(items: List[Dict]) -> List[Dict]:
    """
    Process code search results.

    Args:
        items: Raw code items from API

    Returns:
        Processed code list
    """
    code_results = []
    for item in items:
        code = {
            "name": item.get("name", ""),
            "path": item.get("path", ""),
            "url": item.get("html_url", ""),
            "repository": item.get("repository", {}).get("full_name", ""),
            "repository_url": item.get("repository", {}).get("html_url", ""),
            "sha": item.get("sha", ""),
            "content_type": "github_code",
        }
        code_results.append(code)
    return code_results


def _process_users(items: List[Dict]) -> List[Dict]:
    """
    Process user search results.

    Args:
        items: Raw user items from API

    Returns:
        Processed user list
    """
    users = []
    for item in items:
        user = {
            "login": item.get("login", ""),
            "name": item.get("name", ""),
            "url": item.get("html_url", ""),
            "avatar_url": item.get("avatar_url", ""),
            "type": item.get("type", ""),
            "bio": item.get("bio", ""),
            "public_repos": item.get("public_repos", 0),
            "followers": item.get("followers", 0),
            "following": item.get("following", 0),
            "content_type": "github_user",
        }
        users.append(user)
    return users
