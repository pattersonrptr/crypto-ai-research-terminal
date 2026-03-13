"""SummaryGenerator — generate plain-language project summaries.

Produces human-readable explanations of why a project may be interesting
or risky, suitable for display in reports and UI.
"""

import json
from dataclasses import dataclass
from typing import Any

import structlog

from app.ai.llm_provider import LLMProvider

logger = structlog.get_logger(__name__)


@dataclass
class ProjectSummary:
    """Structured summary of a crypto project."""

    summary_text: str
    key_strengths: list[str]
    key_risks: list[str]
    investment_thesis: str
    target_audience: str


SUMMARY_SYSTEM_PROMPT = """You are a cryptocurrency research analyst writing for
intelligent investors who may not be deeply technical.

Your summaries should be:
- Clear and jargon-free where possible
- Balanced (mention both strengths and risks)
- Actionable (explain why someone might care)
- Concise (respect the word limit)

Return ONLY valid JSON with this structure:
{
  "summary_text": "Plain language summary of the project",
  "key_strengths": ["strength1", "strength2", "strength3"],
  "key_risks": ["risk1", "risk2", "risk3"],
  "investment_thesis": "One sentence on why this might be interesting",
  "target_audience": "Who would be interested in this project"
}
"""

PLAIN_TEXT_SYSTEM_PROMPT = """You are a cryptocurrency research analyst.
Write a clear, plain-language summary of this project.
Be balanced, mentioning both strengths and risks.
Keep your response concise."""


class SummaryGenerator:
    """Generates human-readable project summaries using LLM."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        max_words: int = 300,
    ) -> None:
        """Initialize the generator.

        Args:
            llm_provider: LLM provider for generation.
            max_words: Maximum words in plain text summaries.
        """
        self.llm_provider = llm_provider
        self.max_words = max_words

    async def generate(
        self,
        name: str,
        description: str,
        market_data: dict[str, Any] | None = None,
        scores: dict[str, float] | None = None,
    ) -> ProjectSummary:
        """Generate structured project summary.

        Args:
            name: Project name.
            description: Project description.
            market_data: Optional market data (price, volume, etc.).
            scores: Optional scores (fundamental, growth, etc.).

        Returns:
            ProjectSummary with structured information.

        Raises:
            ValueError: If LLM response cannot be parsed.
        """
        prompt = self._build_prompt(name, description, market_data, scores)

        logger.info("summary.generate.start", name=name)

        response = await self.llm_provider.generate(
            prompt,
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            temperature=0.5,
        )

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error("summary.generate.json_error", error=str(e))
            raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e

        logger.info("summary.generate.complete", name=name)

        return ProjectSummary(
            summary_text=data.get("summary_text", ""),
            key_strengths=data.get("key_strengths", []),
            key_risks=data.get("key_risks", []),
            investment_thesis=data.get("investment_thesis", ""),
            target_audience=data.get("target_audience", ""),
        )

    async def generate_plain_text(
        self,
        name: str,
        description: str,
        market_data: dict[str, Any] | None = None,
        scores: dict[str, float] | None = None,
    ) -> str:
        """Generate plain text summary.

        Args:
            name: Project name.
            description: Project description.
            market_data: Optional market data.
            scores: Optional scores.

        Returns:
            Plain text summary string.
        """
        prompt = self._build_prompt(name, description, market_data, scores)
        prompt += f"\n\nKeep your response under {self.max_words} words."

        response = await self.llm_provider.generate(
            prompt,
            system_prompt=PLAIN_TEXT_SYSTEM_PROMPT,
            temperature=0.5,
        )

        return response.text

    def _build_prompt(
        self,
        name: str,
        description: str,
        market_data: dict[str, Any] | None = None,
        scores: dict[str, float] | None = None,
    ) -> str:
        """Build prompt from project data.

        Args:
            name: Project name.
            description: Project description.
            market_data: Optional market data.
            scores: Optional scores.

        Returns:
            Formatted prompt string.
        """
        prompt = f"""Analyze and summarize this cryptocurrency project:

Name: {name}
Description: {description}
"""

        if market_data:
            prompt += "\nMarket Data:\n"
            for key, value in market_data.items():
                prompt += f"- {key}: {value}\n"

        if scores:
            prompt += "\nScores:\n"
            for key, value in scores.items():
                prompt += f"- {key}: {value}\n"

        return prompt
