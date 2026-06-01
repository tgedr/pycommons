"""Markdown to PDF conversion.

Example:
    `uv run python -c "from tgedr_pycommons.cicd.markdown_to_pdf import convert; convert('input.md', 'output.pdf')"`

"""

from pathlib import Path

import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def convert(input_path: str, output_path: str) -> None:
    """Convert a markdown file to a PDF file preserving formatting.

    Args:
        input_path: Path to the source markdown file.
        output_path: Path for the generated PDF file.

    Raises:
        FileNotFoundError: If the input markdown file does not exist.
    """
    src = Path(input_path)
    if not src.exists():
        msg = f"Markdown file not found: {input_path}"
        raise FileNotFoundError(msg)

    md_content = src.read_text(encoding="utf-8")
    html = markdown.markdown(md_content, extensions=["fenced_code", "tables"])

    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm)
    styles = getSampleStyleSheet()
    story: list = []

    for block in _split_html_blocks(html):
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith("<h") and len(stripped) > 2 and stripped[2].isdigit():
            level = int(stripped[2])
            style_name = f"Heading{level}" if f"Heading{level}" in [s.name for s in styles.byName.values()] else "Heading1"
            story.append(Paragraph(stripped, styles[style_name]))
            story.append(Spacer(1, 3 * mm))
        elif stripped.startswith(("<pre", "<code")):
            code_style = ParagraphStyle("Code", parent=styles["Code"], fontName="Courier", fontSize=9, leading=12)
            story.append(Paragraph(stripped, code_style))
            story.append(Spacer(1, 2 * mm))
        else:
            story.append(Paragraph(stripped, styles["BodyText"]))
            story.append(Spacer(1, 2 * mm))

    if not story:
        story.append(Spacer(1, 1 * mm))

    doc.build(story)


def _split_html_blocks(html: str) -> list[str]:
    """Split HTML into top-level block elements.

    Args:
        html: The HTML string produced by the markdown library.

    Returns:
        A list of HTML block strings.
    """
    blocks: list[str] = []
    current = ""
    for line in html.split("\n"):
        if line.startswith("<") and current:
            blocks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        blocks.append(current)
    return blocks
