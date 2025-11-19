"""
ArXiv Search Tool

Implements academic paper search using the ArXiv API.

Features:
- ArXiv API integration
- Content pipeline processing for ranking and summarization
- Date filtering
- Multiple sort options
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import arxiv

logger = logging.getLogger(__name__)


async def arxiv_search(
    query: str,
    max_results: int = 20,
    sort_by: str = "relevance",
    date_from: Optional[str] = None,
    content_pipeline=None,
) -> Dict[str, Any]:
    """
    Search ArXiv and return papers with abstracts.

    Args:
        query: Search query string
        max_results: Maximum papers to return (1-50)
        sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate')
        date_from: Filter papers from this date (YYYY-MM-DD)
        content_pipeline: Optional content pipeline for processing results

    Returns:
        Dict containing:
            - papers: List of papers with metadata (processed if pipeline provided)
            - total_found: Total number of papers found
            - timestamp: Search timestamp
            - query: Original query
            - pipeline_stats: Pipeline statistics (if pipeline used)

    Raises:
        Exception: If search fails
    """
    try:
        logger.info(f"[ArxivSearch] Starting | query='{query}' max_results={max_results} sort={sort_by}")

        # Ensure max_results is an integer (LLM may pass as string)
        max_results = int(max_results)
        max_results = max(1, min(max_results, 50))  # Clamp to 1-50

        # Map sort_by to arxiv.SortCriterion
        sort_criterion = arxiv.SortCriterion.Relevance
        if sort_by == "lastUpdatedDate":
            sort_criterion = arxiv.SortCriterion.LastUpdatedDate
        elif sort_by == "submittedDate":
            sort_criterion = arxiv.SortCriterion.SubmittedDate

        # Create search client
        client = arxiv.Client()

        # Perform search
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion,
        )

        papers = []
        for result in client.results(search):
            # Filter by date if specified
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                    published_dt = result.published
                    if published_dt.tzinfo is None:
                        published_dt = published_dt.replace(tzinfo=timezone.utc)
                    else:
                        published_dt = published_dt.astimezone(timezone.utc)
                    if published_dt < from_date:
                        continue
                except ValueError:
                    logger.warning(f"Invalid date format: {date_from}")

            # Extract paper information
            paper = {
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "abstract": result.summary,
                "snippet": result.summary[:300],  # Short snippet
                "pdf_url": result.pdf_url,
                "url": result.entry_id,  # ArXiv URL for pipeline
                "arxiv_id": result.entry_id.split("/")[-1],
                "published_date": result.published.isoformat(),
                "updated_date": result.updated.isoformat(),
                "categories": result.categories,
                "primary_category": result.primary_category,
                "doi": result.doi,
                "journal_ref": result.journal_ref,
                "comment": result.comment,
                "content_type": "academic_paper",
            }
            papers.append(paper)

        logger.info(f"[ArxivSearch] Retrieved {len(papers)} raw papers")

        # Process through content pipeline if provided
        processed_papers = papers
        pipeline_stats = None
        pipeline_notes: List[str] = []

        if content_pipeline and papers:
            try:
                logger.info(
                    f"[ArxivSearch] Processing {len(papers)} papers via content pipeline"
                )
                pipeline_output = await content_pipeline.process_arxiv_results(
                    papers, query
                )
                processed_papers = pipeline_output.get("top_items", papers)
                pipeline_stats = pipeline_output.get("stats")
                pipeline_notes = pipeline_output.get("notes", [])
                logger.info(
                    f"[ArxivSearch] Pipeline reduced {len(papers)} → {len(processed_papers)} papers"
                )
            except Exception as e:
                logger.error(f"Content pipeline processing failed: {e}")
                # Fall back to raw papers if pipeline fails
                processed_papers = papers

        response = {
            "papers": processed_papers,
            "total_found": len(processed_papers),
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "status": "success",
            "notes": pipeline_notes,
        }

        if pipeline_stats:
            response["pipeline_stats"] = pipeline_stats

        logger.info(
            f"[ArxivSearch] Complete | returned={len(processed_papers)} status=success"
        )

        return response

    except Exception as e:
        logger.error(f"[ArxivSearch] Failed: {e}")
        return {
            "papers": [],
            "total_found": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "status": "error",
            "error": str(e),
        }
