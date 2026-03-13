"""Tests for WhitepaperAnalyzer — TDD [RED] phase."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.llm_provider import LLMProvider, LLMResponse
from app.ai.whitepaper_analyzer import WhitepaperAnalysis, WhitepaperAnalyzer


class TestWhitepaperAnalysis:
    """Tests for WhitepaperAnalysis dataclass."""

    def test_whitepaper_analysis_has_required_fields(self) -> None:
        """WhitepaperAnalysis should have all required fields."""
        analysis = WhitepaperAnalysis(  # nosec B106
            summary="Test summary",
            problem_solved="Test problem",
            technology="Test tech",
            token_utility="Test utility",
            competitors=["ETH", "SOL"],
            main_risks=["risk1", "risk2"],
            innovation_score=7.5,
            differentiators=["fast", "cheap"],
        )
        assert analysis.summary == "Test summary"
        assert analysis.problem_solved == "Test problem"
        assert analysis.technology == "Test tech"
        assert analysis.token_utility == "Test utility"  # nosec B105
        assert analysis.competitors == ["ETH", "SOL"]
        assert analysis.main_risks == ["risk1", "risk2"]
        assert analysis.innovation_score == 7.5
        assert analysis.differentiators == ["fast", "cheap"]


class TestWhitepaperAnalyzerInit:
    """Tests for WhitepaperAnalyzer initialization."""

    def test_init_requires_llm_provider(self) -> None:
        """Should accept an LLMProvider instance."""
        provider = LLMProvider()
        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        assert analyzer.llm_provider is provider

    def test_init_stores_max_summary_words(self) -> None:
        """Should store configurable max summary words."""
        provider = LLMProvider()
        analyzer = WhitepaperAnalyzer(llm_provider=provider, max_summary_words=500)
        assert analyzer.max_summary_words == 500

    def test_init_default_max_summary_words(self) -> None:
        """Default max summary words should be 300."""
        provider = LLMProvider()
        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        assert analyzer.max_summary_words == 300


class TestWhitepaperAnalyzerAnalyze:
    """Tests for WhitepaperAnalyzer analyze method."""

    @pytest.fixture
    def mock_llm_response(self) -> LLMResponse:
        """Create a mock LLM response."""
        return LLMResponse(
            text="""{
                "summary": "A scalable blockchain platform.",
                "problem_solved": "Transaction throughput limitations",
                "technology": "Proof of History consensus",
                "token_utility": "Gas fees and staking",
                "competitors": ["Ethereum", "Avalanche"],
                "main_risks": ["centralization", "outages"],
                "innovation_score": 8.0,
                "differentiators": ["speed", "low cost"]
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=500,
        )

    @pytest.mark.asyncio
    async def test_analyze_text_returns_whitepaper_analysis(
        self, mock_llm_response: LLMResponse
    ) -> None:
        """analyze_text should return WhitepaperAnalysis."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        result = await analyzer.analyze_text("Solana whitepaper content...")
        assert isinstance(result, WhitepaperAnalysis)
        assert result.summary == "A scalable blockchain platform."
        assert result.innovation_score == 8.0

    @pytest.mark.asyncio
    async def test_analyze_text_passes_content_to_llm(self, mock_llm_response: LLMResponse) -> None:
        """analyze_text should pass whitepaper content to LLM."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        await analyzer.analyze_text("Test whitepaper content")

        provider.generate.assert_called_once()
        call_args = provider.generate.call_args
        assert "Test whitepaper content" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_analyze_text_uses_system_prompt(self, mock_llm_response: LLMResponse) -> None:
        """analyze_text should use appropriate system prompt."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        await analyzer.analyze_text("Content")

        call_args = provider.generate.call_args
        # Should pass system_prompt as kwarg
        assert "system_prompt" in call_args[1]

    @pytest.mark.asyncio
    async def test_analyze_text_handles_malformed_json(self) -> None:
        """analyze_text should handle malformed JSON from LLM."""
        provider = LLMProvider()
        bad_response = LLMResponse(
            text="This is not valid JSON",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=bad_response)

        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        with pytest.raises(ValueError, match="Failed to parse"):
            await analyzer.analyze_text("Content")

    @pytest.mark.asyncio
    async def test_analyze_text_clamps_innovation_score(self) -> None:
        """innovation_score should be clamped to 0-10 range."""
        provider = LLMProvider()
        response = LLMResponse(
            text="""{
                "summary": "Test",
                "problem_solved": "Test",
                "technology": "Test",
                "token_utility": "Test",
                "competitors": [],
                "main_risks": [],
                "innovation_score": 15.0,
                "differentiators": []
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        analyzer = WhitepaperAnalyzer(llm_provider=provider)
        result = await analyzer.analyze_text("Content")
        assert result.innovation_score == 10.0  # Clamped to max


class TestWhitepaperAnalyzerPdfExtraction:
    """Tests for PDF text extraction."""

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_extracts_content(self) -> None:
        """extract_text_from_pdf should extract text from PDF bytes."""
        provider = LLMProvider()
        analyzer = WhitepaperAnalyzer(llm_provider=provider)

        # Mock pypdf
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 content"
        mock_reader.pages = [mock_page]

        with patch("app.ai.whitepaper_analyzer.PdfReader", return_value=mock_reader):
            pdf_bytes = b"%PDF-1.4 test content"
            result = await analyzer.extract_text_from_pdf(pdf_bytes)
            assert "Page 1 content" in result

    @pytest.mark.asyncio
    async def test_extract_text_concatenates_all_pages(self) -> None:
        """extract_text_from_pdf should concatenate text from all pages."""
        provider = LLMProvider()
        analyzer = WhitepaperAnalyzer(llm_provider=provider)

        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2"
        mock_reader.pages = [mock_page1, mock_page2]

        with patch("app.ai.whitepaper_analyzer.PdfReader", return_value=mock_reader):
            pdf_bytes = b"%PDF-1.4 test"
            result = await analyzer.extract_text_from_pdf(pdf_bytes)
            assert "Page 1" in result
            assert "Page 2" in result


class TestWhitepaperAnalyzerFromUrl:
    """Tests for analyze_from_url method."""

    @pytest.mark.asyncio
    async def test_analyze_from_url_downloads_and_analyzes(self) -> None:
        """analyze_from_url should download PDF and analyze it."""
        provider = LLMProvider()
        mock_llm_response = LLMResponse(
            text="""{
                "summary": "URL test",
                "problem_solved": "Test",
                "technology": "Test",
                "token_utility": "Test",
                "competitors": [],
                "main_risks": [],
                "innovation_score": 7.0,
                "differentiators": []
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=mock_llm_response)

        analyzer = WhitepaperAnalyzer(llm_provider=provider)

        # Mock PDF extraction
        analyzer.extract_text_from_pdf = AsyncMock(return_value="Extracted text")

        # Mock HTTP download - use respx or patch httpx
        mock_response = MagicMock()
        mock_response.content = b"%PDF-1.4 content"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await analyzer.analyze_from_url("https://example.com/whitepaper.pdf")
            assert isinstance(result, WhitepaperAnalysis)
            assert result.summary == "URL test"
