"""
HTML Export Module

Generates standalone HTML documents from research reports using Jinja2 templates.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from jinja2 import Template
import markdown

logger = logging.getLogger(__name__)


# HTML template (embedded for simplicity, could be loaded from file)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report - {{ query[:50] }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 2px solid #e5e7eb;
        }

        .title {
            font-size: 32px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 20px;
        }

        .query-box {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .query-label {
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }

        .query-text {
            font-size: 16px;
            color: #1f2937;
        }

        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: #f9fafb;
            border-radius: 8px;
        }

        .metadata-item {
            display: flex;
            flex-direction: column;
        }

        .metadata-label {
            font-size: 12px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metadata-value {
            font-size: 14px;
            color: #1f2937;
            margin-top: 4px;
        }

        .toc {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
        }

        .toc h2 {
            font-size: 20px;
            margin-bottom: 15px;
            color: #111827;
        }

        .toc ul {
            list-style: none;
        }

        .toc li {
            padding: 8px 0;
        }

        .toc a {
            color: #3b82f6;
            text-decoration: none;
        }

        .toc a:hover {
            text-decoration: underline;
        }

        .content {
            margin: 40px 0;
        }

        .content h1 {
            font-size: 28px;
            color: #111827;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 1px solid #e5e7eb;
        }

        .content h2 {
            font-size: 24px;
            color: #1f2937;
            margin: 25px 0 12px 0;
        }

        .content h3 {
            font-size: 20px;
            color: #374151;
            margin: 20px 0 10px 0;
        }

        .content p {
            margin: 15px 0;
            text-align: justify;
        }

        .content ul, .content ol {
            margin: 15px 0 15px 30px;
        }

        .content li {
            margin: 8px 0;
        }

        .content code {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
        }

        .content pre {
            background: #1f2937;
            color: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
        }

        .content pre code {
            background: transparent;
            padding: 0;
            color: #f9fafb;
        }

        .content a {
            color: #3b82f6;
            text-decoration: none;
        }

        .content a:hover {
            text-decoration: underline;
        }

        .sources {
            margin-top: 50px;
            padding-top: 30px;
            border-top: 2px solid #e5e7eb;
        }

        .sources h2 {
            font-size: 24px;
            color: #111827;
            margin-bottom: 20px;
        }

        .source-item {
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #3b82f6;
        }

        .source-number {
            font-weight: 700;
            color: #3b82f6;
            margin-right: 10px;
        }

        .source-title {
            font-weight: 600;
            color: #111827;
            margin-bottom: 5px;
        }

        .source-url {
            color: #3b82f6;
            font-size: 14px;
            word-break: break-all;
            display: block;
            margin-top: 5px;
        }

        .source-meta {
            font-size: 13px;
            color: #6b7280;
            margin-top: 8px;
        }

        .footer {
            margin-top: 50px;
            padding-top: 30px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                padding: 20px;
            }

            .source-item {
                page-break-inside: avoid;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }

            .title {
                font-size: 24px;
            }

            .metadata {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1 class="title">Research Report</h1>

            <div class="query-box">
                <div class="query-label">Research Query:</div>
                <div class="query-text">{{ query }}</div>
            </div>

            {% if metadata %}
            <div class="metadata">
                {% if metadata.session_id %}
                <div class="metadata-item">
                    <span class="metadata-label">Session ID</span>
                    <span class="metadata-value">{{ metadata.session_id }}</span>
                </div>
                {% endif %}

                {% if metadata.created_at %}
                <div class="metadata-item">
                    <span class="metadata-label">Generated</span>
                    <span class="metadata-value">{{ metadata.created_at }}</span>
                </div>
                {% endif %}

                {% if metadata.duration %}
                <div class="metadata-item">
                    <span class="metadata-label">Duration</span>
                    <span class="metadata-value">{{ metadata.duration_formatted }}</span>
                </div>
                {% endif %}

                {% if metadata.cost %}
                <div class="metadata-item">
                    <span class="metadata-label">Cost</span>
                    <span class="metadata-value">${{ "%.4f"|format(metadata.cost) }} USD</span>
                </div>
                {% endif %}
            </div>
            {% endif %}
        </header>

        <nav class="toc">
            <h2>Table of Contents</h2>
            <ul>
                <li><a href="#content">Research Report</a></li>
                {% if sources %}
                <li><a href="#sources">Sources & References ({{ sources|length }})</a></li>
                {% endif %}
            </ul>
        </nav>

        <article id="content" class="content">
            {{ report_html|safe }}
        </article>

        {% if sources %}
        <section id="sources" class="sources">
            <h2>Sources & References</h2>

            {% for source in sources %}
            <div class="source-item">
                <span class="source-number">[{{ loop.index }}]</span>

                {% if source.title %}
                <div class="source-title">{{ source.title }}</div>
                {% endif %}

                {% if source.url %}
                <a href="{{ source.url }}" class="source-url" target="_blank" rel="noopener noreferrer">
                    {{ source.url }}
                </a>
                {% endif %}

                {% if source.author or source.date %}
                <div class="source-meta">
                    {% if source.author %}Author: {{ source.author }}{% endif %}
                    {% if source.author and source.date %} | {% endif %}
                    {% if source.date %}Date: {{ source.date }}{% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </section>
        {% endif %}

        <footer class="footer">
            <p>Generated by Agentic AI Research System</p>
            <p>© {{ current_year }} - All rights reserved</p>
        </footer>
    </div>
</body>
</html>
"""


async def export_to_html(
    report: str,
    query: str,
    sources: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Export research report to standalone HTML format.

    Args:
        report: The final research report in markdown format
        query: Original research query
        sources: List of sources used
        metadata: Additional metadata (session_id, timestamps, costs, etc.)

    Returns:
        HTML content as string

    Raises:
        Exception: If HTML generation fails
    """
    try:
        # Convert markdown to HTML
        report_html = markdown.markdown(
            report,
            extensions=[
                "fenced_code",
                "tables",
                "nl2br",
                "sane_lists",
            ],
        )

        # Format metadata
        formatted_metadata = _format_metadata(metadata) if metadata else None

        # Prepare template context
        context = {
            "query": query,
            "report_html": report_html,
            "sources": sources,
            "metadata": formatted_metadata,
            "current_year": datetime.now().year,
        }

        # Render template
        template = Template(HTML_TEMPLATE)
        html_content = template.render(**context)

        logger.info(f"Generated HTML report: {len(html_content)} characters")
        return html_content

    except Exception as e:
        logger.error(f"HTML generation failed: {e}", exc_info=True)
        raise


def _format_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format metadata for display in HTML.

    Args:
        metadata: Raw metadata dictionary

    Returns:
        Formatted metadata dictionary
    """
    formatted = metadata.copy()

    # Format created_at
    if "created_at" in formatted:
        created_at = formatted["created_at"]
        if isinstance(created_at, datetime):
            formatted["created_at"] = created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted["created_at"] = str(created_at)

    # Format duration
    if "duration" in formatted:
        duration = formatted["duration"]
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            formatted["duration_formatted"] = f"{minutes}m {seconds}s"

    return formatted


def load_template_from_file(template_path: str) -> str:
    """
    Load HTML template from file (optional, for custom templates).

    Args:
        template_path: Path to template file

    Returns:
        Template content as string
    """
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load template from {template_path}: {e}")
        raise
