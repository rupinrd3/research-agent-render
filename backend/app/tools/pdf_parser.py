"""
PDF Parser Tool

Extracts text from PDF documents from URLs or local files.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import io

try:
    import pymupdf

    try:
        pymupdf.TOOLS.mupdf_display_errors(False)
    except Exception:
        pass
except ImportError:  # pragma: no cover - dependency optional at runtime
    pymupdf = None

from .definitions import PDF_TO_TEXT_DEFINITION

logger = logging.getLogger(__name__)


async def pdf_to_text(source: str, max_pages: int = 50) -> Dict[str, Any]:
    """
    Extract text from PDF.

    Args:
        source: PDF URL (https://...) or file path
        max_pages: Maximum pages to extract (default: 50)

    Returns:
        Dict containing:
            - title: Extracted title
            - sections: List of sections with headings and content
            - total_pages: Total pages in PDF
            - extracted_pages: Number of pages extracted
            - full_text: All text concatenated
            - metadata: PDF metadata
            - timestamp: Extraction timestamp

    Raises:
        Exception: If PDF extraction fails
    """
    try:
        logger.info(f"Extracting text from PDF: {source}")

        if pymupdf is None:
            raise RuntimeError(
                "PyMuPDF is not installed. Run `pip install PyMuPDF` to enable PDF extraction."
            )

        # Ensure max_pages is an integer (LLM may pass as string)
        max_pages = int(max_pages)
        max_pages = max(1, min(max_pages, 200))  # Clamp to 1-200

        # Download PDF if URL, otherwise open local file
        if source.startswith("http://") or source.startswith("https://"):
            if not source.lower().endswith(".pdf"):
                raise ValueError(
                    "The pdf_to_text tool requires a direct PDF URL ending with '.pdf'. "
                    "Use web_search/arxiv_search/pdf metadata to retrieve the downloadable PDF link first."
                )
            pdf_data = await _download_pdf(source)
            pdf_doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        else:
            if not source.lower().endswith(".pdf"):
                raise ValueError(
                    "The pdf_to_text tool can only open PDF files. Please provide a .pdf path."
                )
            pdf_doc = pymupdf.open(source)

        # Extract metadata
        metadata = {
            "title": pdf_doc.metadata.get("title", ""),
            "author": pdf_doc.metadata.get("author", ""),
            "subject": pdf_doc.metadata.get("subject", ""),
            "creator": pdf_doc.metadata.get("creator", ""),
            "producer": pdf_doc.metadata.get("producer", ""),
        }

        total_pages = pdf_doc.page_count
        pages_to_extract = min(max_pages, total_pages)

        # Extract text from pages
        text_parts = []
        sections = []

        for page_num in range(pages_to_extract):
            page = pdf_doc[page_num]
            page_text = page.get_text()
            text_parts.append(page_text)

            # Try to identify sections (simple heuristic)
            lines = page_text.split("\n")
            for line in lines:
                if (
                    line.isupper()
                    or (len(line) < 100 and line.endswith(":"))
                ):
                    # Potential section heading
                    sections.append(
                        {
                            "heading": line.strip(),
                            "page_number": page_num + 1,
                        }
                    )

        full_text = "\n\n".join(text_parts)

        # Extract title from first page if not in metadata
        title = metadata["title"]
        if not title and text_parts:
            # Use first non-empty line as title
            first_lines = text_parts[0].split("\n")
            for line in first_lines:
                if line.strip():
                    title = line.strip()
                    break

        pdf_doc.close()

        logger.info(
            f"Extracted {pages_to_extract} pages from PDF: {source}"
        )

        return {
            "title": title,
            "sections": sections[:10],  # Limit to 10 sections
            "total_pages": total_pages,
            "extracted_pages": pages_to_extract,
            "full_text": full_text[:50000],  # Limit to 50K characters
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "status": "success",
            "word_count": len(full_text.split()),
        }

    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return {
            "title": "",
            "sections": [],
            "total_pages": 0,
            "extracted_pages": 0,
            "full_text": "",
            "metadata": {},
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "status": "error",
            "error": str(e),
        }


async def _download_pdf(url: str) -> bytes:
    """
    Download PDF from URL.

    Args:
        url: PDF URL

    Returns:
        PDF content as bytes

    Raises:
        Exception: If download fails
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.content
