"""WhitepaperAnalyzer — extract structured insights from project whitepapers.

Uses LLM to analyze whitepaper text and produce structured JSON output
with summary, problem solved, technology, risks, etc.
"""

import json
from dataclasses import dataclass
from io import BytesIO

import httpx
import structlog
from pypdf import PdfReader

from app.ai.llm_provider import LLMProvider

logger = structlog.get_logger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are a cryptocurrency research analyst.
Analyze the following whitepaper and extract key information in JSON format.
Be objective and factual.

Return ONLY valid JSON with this exact structure:
{
  "summary": "Plain-language summary (max 300 words)",
  "problem_solved": "The core problem this project addresses",
  "technology": "How the technology works at a high level",
  "token_utility": "What the native token is used for",
  "competitors": ["List", "of", "competitors"],
  "main_risks": ["List", "of", "main", "risks"],
  "innovation_score": 7.5,
  "differentiators": ["What", "makes", "it", "unique"]
}

The innovation_score should be 0-10 based on technical novelty and differentiation.
"""


@dataclass
class WhitepaperAnalysis:
    """Structured analysis result from whitepaper."""

    summary: str
    problem_solved: str
    technology: str
    token_utility: str
    competitors: list[str]
    main_risks: list[str]
    innovation_score: float
    differentiators: list[str]


class WhitepaperAnalyzer:
    """Analyzes cryptocurrency project whitepapers using LLM.

    Extracts structured information including summary, risks,
    technology description, and innovation score.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        max_summary_words: int = 300,
    ) -> None:
        """Initialize the analyzer.

        Args:
            llm_provider: LLM provider for text analysis.
            max_summary_words: Maximum words in summary output.
        """
        self.llm_provider = llm_provider
        self.max_summary_words = max_summary_words

    async def analyze_text(self, content: str) -> WhitepaperAnalysis:
        """Analyze whitepaper text content.

        Args:
            content: Raw text content from whitepaper.

        Returns:
            WhitepaperAnalysis with extracted information.

        Raises:
            ValueError: If LLM response cannot be parsed as JSON.
        """
        prompt = f"""Analyze this whitepaper content:

{content}

Remember to return ONLY valid JSON matching the required schema."""

        logger.info("whitepaper.analyze.start", content_length=len(content))

        response = await self.llm_provider.generate(
            prompt,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for structured output
        )

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error("whitepaper.analyze.json_error", error=str(e))
            raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e

        # Clamp innovation score to valid range
        innovation_score = float(data.get("innovation_score", 5.0))
        innovation_score = max(0.0, min(10.0, innovation_score))

        logger.info(
            "whitepaper.analyze.complete",
            innovation_score=innovation_score,
            provider=response.provider,
        )

        return WhitepaperAnalysis(
            summary=data.get("summary", ""),
            problem_solved=data.get("problem_solved", ""),
            technology=data.get("technology", ""),
            token_utility=data.get("token_utility", ""),
            competitors=data.get("competitors", []),
            main_risks=data.get("main_risks", []),
            innovation_score=innovation_score,
            differentiators=data.get("differentiators", []),
        )

    async def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text content from PDF bytes.

        Args:
            pdf_bytes: Raw PDF file bytes.

        Returns:
            Concatenated text from all pages.
        """
        reader = PdfReader(BytesIO(pdf_bytes))
        pages_text = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        full_text = "\n\n".join(pages_text)
        logger.debug("whitepaper.pdf.extracted", pages=len(reader.pages), chars=len(full_text))

        return full_text

    async def analyze_from_url(self, url: str) -> WhitepaperAnalysis:
        """Download and analyze whitepaper from URL.

        Args:
            url: URL to PDF whitepaper.

        Returns:
            WhitepaperAnalysis with extracted information.
        """
        logger.info("whitepaper.download.start", url=url)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            pdf_bytes = response.content

        text = await self.extract_text_from_pdf(pdf_bytes)
        return await self.analyze_text(text)
