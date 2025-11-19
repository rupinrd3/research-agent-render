"""
PDF Export Module

Generates professional PDF documents from research reports using reportlab.
"""

import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import re

logger = logging.getLogger(__name__)


async def export_to_pdf(
    report: str,
    query: str,
    sources: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Export research report to PDF format.

    Args:
        report: The final research report in markdown format
        query: Original research query
        sources: List of sources used
        metadata: Additional metadata (session_id, timestamps, costs, etc.)

    Returns:
        PDF file as bytes

    Raises:
        Exception: If PDF generation fails
    """
    try:
        # Create PDF buffer
        buffer = io.BytesIO()

        # Create document with margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build content
        story = []
        styles = _create_styles()

        # Title page
        story.extend(_create_title_page(query, metadata, styles))
        story.append(PageBreak())

        # Table of contents (optional, could be enhanced)
        story.extend(_create_toc(styles))
        story.append(PageBreak())

        # Main report content
        story.extend(_convert_markdown_to_pdf(report, styles))
        story.append(PageBreak())

        # Sources section
        if sources:
            story.extend(_create_sources_section(sources, styles))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated PDF report: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise


def _create_styles() -> Dict[str, ParagraphStyle]:
    """
    Create custom paragraph styles for PDF.

    Returns:
        Dictionary of custom styles
    """
    styles = getSampleStyleSheet()

    # Title style
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
    )

    # Subtitle style
    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#6b7280"),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
    )

    # Custom heading styles
    styles.add(
        ParagraphStyle(
            name="Heading2Custom",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=16,
            spaceAfter=12,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="Heading3Custom",
            parent=styles["Heading3"],
            fontSize=14,
            textColor=colors.HexColor("#374151"),
            spaceBefore=12,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )

    # Body text
    styles.add(
        ParagraphStyle(
            name="BodyText",
            parent=styles["Normal"],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        )
    )

    # Code style
    styles.add(
        ParagraphStyle(
            name="Code",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Courier",
            textColor=colors.HexColor("#1f2937"),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10,
            backColor=colors.HexColor("#f3f4f6"),
        )
    )

    # Bullet point style
    styles.add(
        ParagraphStyle(
            name="Bullet",
            parent=styles["Normal"],
            fontSize=11,
            leftIndent=20,
            spaceAfter=6,
        )
    )

    return styles


def _create_title_page(
    query: str, metadata: Optional[Dict[str, Any]], styles: Dict
) -> List:
    """Create title page content."""
    content = []

    # Spacer from top
    content.append(Spacer(1, 1.5 * inch))

    # Main title
    content.append(Paragraph("Research Report", styles["CustomTitle"]))
    content.append(Spacer(1, 0.5 * inch))

    # Query
    query_text = f"<b>Research Query:</b><br/>{query}"
    content.append(Paragraph(query_text, styles["BodyText"]))
    content.append(Spacer(1, 0.5 * inch))

    # Metadata table
    if metadata:
        metadata_data = []

        if metadata.get("session_id"):
            metadata_data.append(["Session ID:", metadata["session_id"]])

        if metadata.get("created_at"):
            created_at = metadata["created_at"]
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            metadata_data.append(["Generated:", str(created_at)])

        if metadata.get("duration"):
            duration = metadata["duration"]
            if duration:
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                metadata_data.append(["Duration:", f"{minutes}m {seconds}s"])

        if metadata.get("cost"):
            cost = metadata["cost"]
            if cost:
                metadata_data.append(["Cost:", f"${cost:.4f} USD"])

        if metadata_data:
            metadata_table = Table(metadata_data, colWidths=[2 * inch, 3 * inch])
            metadata_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                        ("ALIGN", (1, 0), (1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            content.append(metadata_table)

    return content


def _create_toc(styles: Dict) -> List:
    """Create table of contents."""
    content = []
    content.append(Paragraph("Table of Contents", styles["Heading2Custom"]))
    content.append(Spacer(1, 0.2 * inch))
    content.append(
        Paragraph(
            "1. Executive Summary<br/>"
            "2. Key Findings<br/>"
            "3. Detailed Analysis<br/>"
            "4. Sources<br/>",
            styles["BodyText"],
        )
    )
    return content


def _convert_markdown_to_pdf(markdown_text: str, styles: Dict) -> List:
    """
    Convert markdown text to PDF elements.

    Simple markdown parser that handles:
    - Headers (# ## ###)
    - Bold (**text**)
    - Italic (*text*)
    - Code blocks (```code```)
    - Bullet points (- item)
    - Numbered lists (1. item)
    - Links ([text](url))

    Args:
        markdown_text: Markdown formatted text
        styles: Paragraph styles

    Returns:
        List of PDF elements
    """
    content = []
    lines = markdown_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i].strip()

        # Code block detection
        if line.startswith("```"):
            if in_code_block:
                # End code block
                code_text = "\n".join(code_lines)
                content.append(Paragraph(f"<pre>{code_text}</pre>", styles["Code"]))
                code_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Headers
        if line.startswith("### "):
            text = _clean_markdown(line[4:])
            content.append(Paragraph(text, styles["Heading3Custom"]))
        elif line.startswith("## "):
            text = _clean_markdown(line[3:])
            content.append(Paragraph(text, styles["Heading2Custom"]))
        elif line.startswith("# "):
            text = _clean_markdown(line[2:])
            content.append(Paragraph(text, styles["CustomTitle"]))
        # Bullet points
        elif line.startswith("- ") or line.startswith("* "):
            text = _clean_markdown(line[2:])
            content.append(Paragraph(f"• {text}", styles["Bullet"]))
        # Numbered lists
        elif re.match(r"^\d+\.\s", line):
            text = _clean_markdown(re.sub(r"^\d+\.\s", "", line))
            number = re.match(r"^(\d+)\.", line).group(1)
            content.append(Paragraph(f"{number}. {text}", styles["Bullet"]))
        # Regular paragraph
        else:
            text = _clean_markdown(line)
            if text:
                content.append(Paragraph(text, styles["BodyText"]))

        i += 1

    return content


def _clean_markdown(text: str) -> str:
    """
    Clean markdown formatting for PDF output.

    Converts markdown syntax to HTML tags supported by reportlab.
    """
    # Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Italic: *text* -> <i>text</i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

    # Inline code: `code` -> <font name="Courier">code</font>
    text = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', text)

    # Links: [text](url) -> text (url)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'\1 (<font color="blue">\2</font>)', text)

    # Escape special characters
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # Restore our HTML tags
    text = text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    text = text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    text = text.replace("&lt;font", "<font").replace("&lt;/font&gt;", "</font>")

    return text


def _create_sources_section(sources: List[Dict[str, Any]], styles: Dict) -> List:
    """Create sources/references section."""
    content = []

    content.append(Paragraph("Sources & References", styles["Heading2Custom"]))
    content.append(Spacer(1, 0.2 * inch))

    for idx, source in enumerate(sources, 1):
        source_text = f"<b>[{idx}]</b> "

        if source.get("title"):
            source_text += f"{source['title']}<br/>"

        if source.get("url"):
            source_text += f'<font color="blue">{source["url"]}</font><br/>'

        if source.get("author"):
            source_text += f"Author: {source['author']}<br/>"

        if source.get("date"):
            source_text += f"Date: {source['date']}<br/>"

        content.append(Paragraph(source_text, styles["BodyText"]))
        content.append(Spacer(1, 0.1 * inch))

    return content
