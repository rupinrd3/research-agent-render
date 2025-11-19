"""
Export Module

Provides functions to export research reports in various formats:
- PDF (reportlab)
- Word (python-docx)
- HTML (Jinja2 templates with embedded CSS)
- Markdown (direct)
- JSON (structured data)
"""

from .pdf import export_to_pdf
from .word import export_to_word
from .html import export_to_html

__all__ = [
    "export_to_pdf",
    "export_to_word",
    "export_to_html",
]
