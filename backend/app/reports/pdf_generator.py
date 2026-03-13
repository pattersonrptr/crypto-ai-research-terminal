"""PDFGenerator — converts Markdown to PDF using WeasyPrint.

Generates PDF documents from Markdown content, suitable for
token reports and market reports.
"""

from pathlib import Path

import markdown
import structlog
from weasyprint import CSS, HTML

logger = structlog.get_logger(__name__)

# Default CSS for PDF styling
DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, sans-serif;
    font-size: 12pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    color: #1a1a1a;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5em;
    margin-top: 0;
}

h2 {
    color: #2c3e50;
    margin-top: 1.5em;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #f5f5f5;
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #fafafa;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 1.5em 0;
}

ul, ol {
    padding-left: 1.5em;
}

li {
    margin: 0.3em 0;
}

strong {
    color: #1a1a1a;
}

em {
    color: #666;
}

code {
    background-color: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
}
"""


class PDFGenerationError(Exception):
    """Exception raised when PDF generation fails."""

    pass


class PDFGenerator:
    """Generates PDF documents from Markdown content."""

    def __init__(self, css_path: Path | None = None) -> None:
        """Initialize the generator.

        Args:
            css_path: Optional path to custom CSS file.
        """
        self._css_path = css_path
        self._css = self._load_css()

    def _load_css(self) -> CSS:
        """Load CSS for PDF styling.

        Returns:
            WeasyPrint CSS object.
        """
        if self._css_path and self._css_path.exists():
            return CSS(filename=str(self._css_path))
        return CSS(string=DEFAULT_CSS)

    def markdown_to_html(self, md_content: str) -> str:
        """Convert Markdown to HTML.

        Args:
            md_content: Markdown content string.

        Returns:
            HTML string.
        """
        # Use markdown library with table extension
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code"],
        )

        # Wrap in full HTML document
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Report</title>
</head>
<body>
{html_body}
</body>
</html>
"""
        return html

    def generate_from_markdown(self, md_content: str) -> bytes:
        """Generate PDF from Markdown content.

        Args:
            md_content: Markdown content string.

        Returns:
            PDF file as bytes.

        Raises:
            PDFGenerationError: If PDF generation fails.
        """
        try:
            html_content = self.markdown_to_html(md_content)
            return self.generate_from_html(html_content)
        except Exception as e:
            logger.error("pdf_generation_failed", error=str(e))
            raise PDFGenerationError(f"Failed to generate PDF: {e}") from e

    def generate_from_html(self, html_content: str) -> bytes:
        """Generate PDF from HTML content.

        Args:
            html_content: HTML content string.

        Returns:
            PDF file as bytes.

        Raises:
            PDFGenerationError: If PDF generation fails.
        """
        try:
            html = HTML(string=html_content)
            result = html.write_pdf(stylesheets=[self._css])
            if result is None:
                raise PDFGenerationError("WeasyPrint returned empty PDF")
            pdf_bytes: bytes = result
            logger.debug("pdf_generated", size_bytes=len(pdf_bytes))
            return pdf_bytes
        except PDFGenerationError:
            raise
        except Exception as e:
            logger.error("pdf_generation_failed", error=str(e))
            raise PDFGenerationError(f"Failed to generate PDF: {e}") from e

    def generate_to_file(
        self,
        md_content: str,
        output_path: Path,
    ) -> None:
        """Generate PDF from Markdown and write to file.

        Args:
            md_content: Markdown content string.
            output_path: Path to write PDF file.

        Raises:
            PDFGenerationError: If PDF generation fails.
        """
        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pdf_bytes = self.generate_from_markdown(md_content)
        output_path.write_bytes(pdf_bytes)

        logger.info(
            "pdf_written_to_file",
            path=str(output_path),
            size_bytes=len(pdf_bytes),
        )
