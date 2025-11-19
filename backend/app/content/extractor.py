"""
Content Extractor

Extracts clean text from PDFs and web pages.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts text from PDFs and web pages.

    Uses:
    - PyMuPDF for PDF extraction
    - Trafilatura for web content (if available)
    - BeautifulSoup4 as fallback
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize content extractor.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._client = None

        # Track failures for observability
        self._recent_failures: List[Dict[str, str]] = []

        # Try importing optional dependencies
        self._has_trafilatura = self._check_trafilatura()
        self._has_pymupdf = self._check_pymupdf()

        logger.info(
            f"Initialized ContentExtractor "
            f"(trafilatura: {self._has_trafilatura}, "
            f"pymupdf: {self._has_pymupdf})"
        )

    def _check_trafilatura(self) -> bool:
        """Check if trafilatura is available."""
        try:
            import trafilatura
            return True
        except ImportError:
            logger.warning(
                "trafilatura not installed - web extraction will be limited"
            )
            return False

    def _check_pymupdf(self) -> bool:
        """Check if PyMuPDF is available."""
        try:
            import pymupdf

            try:
                pymupdf.TOOLS.mupdf_display_errors(False)
            except Exception:
                pass
            return True
        except ImportError:
            logger.warning(
                "PyMuPDF (pymupdf) not installed - PDF extraction disabled"
            )
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def extract(
        self, item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from a single item.

        Args:
            item: Classified item with 'type' and 'url'

        Returns:
            Dict with 'url', 'content', 'metadata' or None if failed
        """
        content_type = item.get("type")
        url = item.get("url")

        try:
            if content_type == "pdf":
                return await self._extract_pdf(url, item)
            elif content_type in ("web", "arxiv", "github"):
                return await self._extract_web(url, item)
            else:
                logger.warning(f"Unknown content type: {content_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return None

    async def extract_batch(
        self, items: List[Dict[str, Any]], max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract content from multiple items in parallel.

        Args:
            items: List of classified items
            max_concurrent: Maximum concurrent extractions

        Returns:
            List of extracted content items (failed items filtered)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        self._recent_failures.clear()

        async def extract_with_semaphore(item):
            async with semaphore:
                return await self.extract(item)

        # Ensure client is initialized
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS)

        try:
            results = await asyncio.gather(
                *[extract_with_semaphore(item) for item in items],
                return_exceptions=True
            )

            # Filter out None and exceptions
            extracted = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Extraction error: {result}")
                elif result is not None:
                    extracted.append(result)

            logger.info(
                f"Extracted {len(extracted)}/{len(items)} items "
                f"({len(items) - len(extracted)} failed)"
            )

            return extracted

        finally:
            # Keep client open for reuse
            pass

    async def _extract_pdf(
        self, url: str, item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract text from PDF.

        Args:
            url: PDF URL
            item: Original item

        Returns:
            Extracted content dict or None
        """
        if not self._has_pymupdf:
            logger.warning("PyMuPDF not available - skipping PDF")
            return None

        try:
            import pymupdf
            # Download PDF
            if not self._client:
                self._client = httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS)

            response = await self._client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Open PDF from bytes
            pdf_data = response.content
            pdf_document = pymupdf.open(stream=pdf_data, filetype="pdf")

            # Extract text from all pages (up to 50)
            max_pages = min(50, pdf_document.page_count)
            total_pages = pdf_document.page_count
            text_parts = []

            for page_num in range(max_pages):
                page = pdf_document[page_num]
                text_parts.append(page.get_text())

            pdf_document.close()

            full_text = "\n\n".join(text_parts)

            return {
                "url": url,
                "content": full_text,
                "metadata": {
                    "type": "pdf",
                    "pages": max_pages,
                    "total_pages": total_pages,
                    "chars": len(full_text),
                },
            }

        except Exception as e:
            logger.error(f"PDF extraction failed for {url}: {e}")
            self._record_failure(url, str(e))
            return None

    async def _extract_web(
        self, url: str, item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract clean text from web page.

        Args:
            url: Web page URL
            item: Original item

        Returns:
            Extracted content dict or None
        """
        try:
            # Download HTML
            if not self._client:
                self._client = httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS)

            response = await self._client.get(url, follow_redirects=True)
            response.raise_for_status()

            html = response.text

            # Try trafilatura first (cleaner extraction)
            if self._has_trafilatura:
                content = self._extract_with_trafilatura(html, url)
            else:
                content = self._extract_with_beautifulsoup(html)

            min_chars = 100
            if not content or len(content.strip()) < min_chars:
                snippet = item.get("snippet") or item.get("summary")
                if snippet and snippet.strip():
                    logger.warning(
                        "Insufficient content extracted from %s; using snippet fallback",
                        url,
                    )
                    content = snippet
                elif not content:
                    logger.warning(
                        "Insufficient content extracted from %s and no snippet available",
                        url,
                    )
                    self._record_failure(
                        url,
                        "Insufficient content extracted and no snippet available",
                    )
                    return None
                else:
                    logger.warning(
                        "Content extracted from %s is shorter than %s characters; continuing anyway",
                        url,
                        min_chars,
                    )

            return {
                "url": url,
                "content": content,
                "metadata": {
                    "type": "web",
                    "chars": len(content),
                    "method": "trafilatura" if self._has_trafilatura else "beautifulsoup",
                },
            }

        except Exception as e:
            logger.error(f"Web extraction failed for {url}: {e}")
            self._record_failure(url, str(e))
            return None

    def _extract_with_trafilatura(self, html: str, url: str) -> Optional[str]:
        """
        Extract content using trafilatura.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Extracted text or None
        """
        try:
            import trafilatura

            content = trafilatura.extract(
                html,
                include_tables=True,
                include_comments=False,
                output_format="txt",
                url=url,
            )

            return content

        except Exception as e:
            logger.error(f"Trafilatura extraction failed: {e}")
            return None

    def _extract_with_beautifulsoup(self, html: str) -> Optional[str]:
        """
        Extract content using BeautifulSoup (fallback).

        Args:
            html: HTML content

        Returns:
            Extracted text or None
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (
                phrase.strip() for line in lines for phrase in line.split("  ")
            )
            text = "\n".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed: {e}")
            return None

    def _record_failure(self, url: Optional[str], reason: str) -> None:
        """Record extraction failure for downstream diagnostics."""
        self._recent_failures.append(
            {
                "url": url or "unknown",
                "error": reason[:300],
            }
        )

    def pop_failures(self) -> List[Dict[str, str]]:
        """Return and clear recently recorded failures."""
        failures = list(self._recent_failures)
        self._recent_failures.clear()
        return failures
