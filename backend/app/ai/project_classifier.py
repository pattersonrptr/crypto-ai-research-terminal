"""ProjectClassifier — classify crypto projects into categories.

Uses LLM to classify tokens into categories like Layer1, DeFi, AI, etc.
"""

import json
from dataclasses import dataclass
from enum import Enum

import structlog

from app.ai.llm_provider import LLMProvider

logger = structlog.get_logger(__name__)


class ProjectCategory(Enum):
    """Categories for crypto projects."""

    LAYER1 = "layer1"
    LAYER2 = "layer2"
    DEFI = "defi"
    AI = "ai"
    GAMING = "gaming"
    INFRASTRUCTURE = "infrastructure"
    DEPIN = "depin"
    ORACLE = "oracle"
    PRIVACY = "privacy"
    MEMECOIN = "memecoin"
    RWA = "rwa"
    RESTAKING = "restaking"


@dataclass
class ClassificationResult:
    """Result of project classification."""

    primary_category: ProjectCategory
    secondary_categories: list[ProjectCategory]
    confidence: float


CLASSIFICATION_SYSTEM_PROMPT = """You are a cryptocurrency analyst.
Classify the following project into one of these categories:
- LAYER1: Base layer blockchains (Bitcoin, Ethereum, Solana)
- LAYER2: Scaling solutions built on top of L1s (Arbitrum, Optimism)
- DEFI: Decentralized finance protocols (Uniswap, Aave)
- AI: AI and machine learning focused projects (Fetch.ai, Render)
- GAMING: Gaming and metaverse projects
- INFRASTRUCTURE: Infrastructure and tooling (Chainlink, The Graph)
- DEPIN: Decentralized physical infrastructure
- ORACLE: Oracle networks
- PRIVACY: Privacy-focused projects
- MEMECOIN: Meme-based tokens
- RWA: Real-world assets
- RESTAKING: Restaking protocols

Return ONLY valid JSON with this structure:
{
  "primary_category": "CATEGORY_NAME",
  "secondary_categories": ["OTHER", "CATEGORIES"],
  "confidence": 0.85
}
"""


class ProjectClassifier:
    """Classifies crypto projects into predefined categories."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the classifier.

        Args:
            llm_provider: LLM provider for classification.
        """
        self.llm_provider = llm_provider

    async def classify(
        self,
        name: str,
        description: str,
    ) -> ClassificationResult:
        """Classify a single project.

        Args:
            name: Project name.
            description: Project description.

        Returns:
            ClassificationResult with category and confidence.

        Raises:
            ValueError: If classification fails or category is invalid.
        """
        prompt = f"""Classify this cryptocurrency project:

Name: {name}
Description: {description}

Return the classification in JSON format."""

        logger.info("project.classify.start", name=name)

        response = await self.llm_provider.generate(
            prompt,
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
            temperature=0.2,  # Low temperature for consistent classification
        )

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error("project.classify.json_error", error=str(e))
            raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e

        # Parse primary category
        primary_str = data.get("primary_category", "").upper()
        try:
            primary_category = ProjectCategory[primary_str]
        except KeyError as e:
            raise ValueError(f"Unknown category: {primary_str}") from e

        # Parse secondary categories
        secondary_categories = []
        for cat_str in data.get("secondary_categories", []):
            try:
                secondary_categories.append(ProjectCategory[cat_str.upper()])
            except KeyError:
                # Skip invalid secondary categories
                logger.warning("project.classify.invalid_secondary", category=cat_str)

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        logger.info(
            "project.classify.complete",
            name=name,
            category=primary_category.name,
            confidence=confidence,
        )

        return ClassificationResult(
            primary_category=primary_category,
            secondary_categories=secondary_categories,
            confidence=confidence,
        )

    async def classify_batch(
        self,
        projects: list[dict[str, str]],
    ) -> list[ClassificationResult]:
        """Classify multiple projects.

        Args:
            projects: List of dicts with 'name' and 'description' keys.

        Returns:
            List of ClassificationResults.
        """
        results = []
        for project in projects:
            result = await self.classify(
                name=project["name"],
                description=project["description"],
            )
            results.append(result)
        return results
