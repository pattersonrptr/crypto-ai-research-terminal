"""Tests for PDFGenerator — converts Markdown to PDF using WeasyPrint.

TDD RED phase: Tests written before implementation.
"""

from pathlib import Path

from app.reports.pdf_generator import PDFGenerationError, PDFGenerator


class TestPDFGeneratorInit:
    """Test PDFGenerator initialization."""

    def test_init_creates_instance(self) -> None:
        """PDFGenerator can be initialized."""
        generator = PDFGenerator()
        assert generator is not None

    def test_init_with_custom_css(self) -> None:
        """PDFGenerator accepts custom CSS path."""
        css_path = Path(__file__).parent / "custom.css"
        generator = PDFGenerator(css_path=css_path)
        assert generator is not None


class TestPDFGeneratorMethods:
    """Test PDFGenerator has required methods."""

    def test_has_generate_from_markdown_method(self) -> None:
        """Generator has generate_from_markdown method."""
        generator = PDFGenerator()
        assert hasattr(generator, "generate_from_markdown")
        assert callable(generator.generate_from_markdown)

    def test_has_generate_from_html_method(self) -> None:
        """Generator has generate_from_html method."""
        generator = PDFGenerator()
        assert hasattr(generator, "generate_from_html")
        assert callable(generator.generate_from_html)

    def test_has_markdown_to_html_method(self) -> None:
        """Generator has markdown_to_html method."""
        generator = PDFGenerator()
        assert hasattr(generator, "markdown_to_html")
        assert callable(generator.markdown_to_html)


class TestMarkdownToHtml:
    """Test PDFGenerator.markdown_to_html method."""

    def test_converts_basic_markdown(self) -> None:
        """Converts basic Markdown to HTML."""
        generator = PDFGenerator()
        markdown = "# Title\n\nParagraph text."

        html = generator.markdown_to_html(markdown)

        assert "<h1>" in html or "<H1>" in html.upper()
        assert "Title" in html
        assert "<p>" in html or "Paragraph" in html

    def test_converts_tables(self) -> None:
        """Converts Markdown tables to HTML tables."""
        generator = PDFGenerator()
        markdown = """
| Column A | Column B |
|----------|----------|
| Value 1  | Value 2  |
"""

        html = generator.markdown_to_html(markdown)

        assert "<table>" in html.lower() or "<table" in html.lower()
        assert "Column A" in html

    def test_converts_lists(self) -> None:
        """Converts Markdown lists to HTML."""
        generator = PDFGenerator()
        markdown = """
- Item 1
- Item 2
- Item 3
"""

        html = generator.markdown_to_html(markdown)

        assert "<ul>" in html.lower() or "<li>" in html.lower()


class TestGenerateFromMarkdown:
    """Test PDFGenerator.generate_from_markdown method."""

    def test_returns_pdf_bytes(self) -> None:
        """generate_from_markdown returns PDF bytes."""
        generator = PDFGenerator()
        markdown = "# Test Report\n\nThis is a test."

        result = generator.generate_from_markdown(markdown)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_starts_with_magic_bytes(self) -> None:
        """Generated PDF starts with PDF magic bytes."""
        generator = PDFGenerator()
        markdown = "# PDF Test\n\nContent here."

        result = generator.generate_from_markdown(markdown)

        # PDF files start with %PDF-
        assert result[:5] == b"%PDF-"

    def test_handles_unicode_content(self) -> None:
        """Handles Unicode characters in Markdown."""
        generator = PDFGenerator()
        markdown = "# Report 🚀\n\n✅ Success\n⚠️ Warning\n🔴 Error"

        result = generator.generate_from_markdown(markdown)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGenerateFromHtml:
    """Test PDFGenerator.generate_from_html method."""

    def test_returns_pdf_bytes(self) -> None:
        """generate_from_html returns PDF bytes."""
        generator = PDFGenerator()
        html = "<html><body><h1>Test</h1></body></html>"

        result = generator.generate_from_html(html)

        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_with_css_styling(self) -> None:
        """Generates PDF with CSS styling."""
        generator = PDFGenerator()
        html = """
        <html>
        <head><style>body { font-family: Arial; }</style></head>
        <body><h1>Styled Content</h1></body>
        </html>
        """

        result = generator.generate_from_html(html)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGenerateToFile:
    """Test PDFGenerator.generate_to_file method."""

    def test_writes_pdf_to_file(self, tmp_path: Path) -> None:
        """generate_to_file writes PDF to specified path."""
        generator = PDFGenerator()
        markdown = "# File Test\n\nContent for file."
        output_path = tmp_path / "test_report.pdf"

        generator.generate_to_file(markdown, output_path)

        assert output_path.exists()
        content = output_path.read_bytes()
        assert content[:5] == b"%PDF-"

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Creates parent directories if they don't exist."""
        generator = PDFGenerator()
        markdown = "# Nested Test"
        output_path = tmp_path / "nested" / "dir" / "report.pdf"

        generator.generate_to_file(markdown, output_path)

        assert output_path.exists()


class TestPDFGenerationError:
    """Test PDFGenerationError exception."""

    def test_is_exception(self) -> None:
        """PDFGenerationError is an Exception."""
        error = PDFGenerationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"


class TestPDFGeneratorWithReports:
    """Test PDFGenerator with actual report Markdown."""

    def test_generates_token_report_pdf(self) -> None:
        """Generates PDF from token report Markdown."""
        generator = PDFGenerator()
        markdown = """
# Bitcoin (BTC) — Token Report

**Generated:** 2024-01-15 12:00 UTC

---

## 📊 Market Data

| Metric | Value |
|--------|-------|
| **Price** | $45,000.00 |
| **Market Cap** | $880.00B |

---

## 🎯 Scores

| Score | Value | Assessment |
|-------|-------|------------|
| **Listing Score** | 0/100 | ⬜ Already Listed |
| **Risk Score** | 5% | ✅ Very Low Risk |

---

*Crypto AI Research Terminal*
"""

        result = generator.generate_from_markdown(markdown)

        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_generates_market_report_pdf(self) -> None:
        """Generates PDF from market report Markdown."""
        generator = PDFGenerator()
        markdown = """
# Daily Market Report — 2024-01-15

---

## 🌍 Market Overview

| Metric | Value |
|--------|-------|
| **Market Sentiment** | 🟢 Bullish |
| **Total Market Cap** | $1.80T |

---

## 🎯 Top Opportunities

| Rank | Token | Score |
|------|-------|-------|
| 1 | **Solana** (SOL) | 85% |
| 2 | **Avalanche** (AVAX) | 78% |

---

*Crypto AI Research Terminal*
"""

        result = generator.generate_from_markdown(markdown)

        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"
