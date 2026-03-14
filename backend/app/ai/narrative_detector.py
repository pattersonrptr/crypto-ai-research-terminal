"""NarrativeDetector — detect emerging narratives from social media posts.

Uses embeddings and clustering to identify trending topics and map
them to tokens mentioned in the posts.
"""

import json
import re
from dataclasses import dataclass, field

import numpy as np
import structlog
from sklearn.cluster import HDBSCAN

from app.ai.llm_provider import LLMProvider

logger = structlog.get_logger(__name__)

LABELING_SYSTEM_PROMPT = """You are a crypto market analyst.
Given a collection of social media posts about cryptocurrency,
identify the main narrative or theme they represent.

Return ONLY valid JSON with this structure:
{
  "name": "Short narrative name (e.g., 'AI + Blockchain', 'Layer 2 Scaling')",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}
"""


@dataclass
class Narrative:
    """A detected market narrative."""

    name: str
    momentum_score: float
    trend: str  # accelerating, stable, declining
    tokens: list[str]
    keywords: list[str]


@dataclass
class NarrativeDetectorResult:
    """Result from narrative detection."""

    narratives: list[Narrative] = field(default_factory=list)


class NarrativeDetector:
    """Detects emerging market narratives from social media posts.

    Pipeline:
    1. Create embeddings for all posts
    2. Cluster embeddings using HDBSCAN
    3. Label clusters using LLM
    4. Extract tokens mentioned in each cluster
    5. Calculate momentum and trend
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        min_cluster_size: int = 5,
    ) -> None:
        """Initialize the detector.

        Args:
            llm_provider: LLM provider for cluster labeling.
            min_cluster_size: Minimum posts to form a cluster.
        """
        self.llm_provider = llm_provider
        self.min_cluster_size = min_cluster_size

    async def detect(self, posts: list[dict[str, str]]) -> NarrativeDetectorResult:
        """Detect narratives from social media posts.

        Args:
            posts: List of posts with 'text' and 'source' fields.

        Returns:
            NarrativeDetectorResult with detected narratives.
        """
        if not posts:
            return NarrativeDetectorResult(narratives=[])

        logger.info("narrative.detect.start", post_count=len(posts))

        # Create embeddings for all posts
        texts = [post["text"] for post in posts]
        embeddings = await self.llm_provider.embed_batch(texts)

        # Cluster embeddings
        labels = self._cluster_embeddings(embeddings)

        # Group posts by cluster
        clusters: dict[int, list[dict[str, str]]] = {}
        for i, label in enumerate(labels):
            if label == -1:  # Skip noise points
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(posts[i])

        # Process each cluster
        narratives = []
        for _cluster_id, cluster_posts in clusters.items():
            narrative = await self._process_cluster(cluster_posts)
            if narrative:
                narratives.append(narrative)

        logger.info("narrative.detect.complete", narrative_count=len(narratives))

        return NarrativeDetectorResult(narratives=narratives)

    def _cluster_embeddings(self, embeddings: list[list[float]]) -> list[int]:
        """Cluster embeddings using HDBSCAN.

        Args:
            embeddings: List of embedding vectors.

        Returns:
            List of cluster labels (-1 for noise).
        """
        if len(embeddings) < self.min_cluster_size:
            # Not enough data for clustering, put all in one cluster
            return [0] * len(embeddings)

        embedding_array = np.array(embeddings)

        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=2,
            metric="euclidean",
        )

        labels: list[int] = clusterer.fit_predict(embedding_array).tolist()

        return labels

    async def _process_cluster(self, posts: list[dict[str, str]]) -> Narrative | None:
        """Process a cluster of posts into a Narrative.

        Args:
            posts: Posts in the cluster.

        Returns:
            Narrative or None if processing fails.
        """
        # Extract tokens mentioned in cluster
        tokens = self._extract_tokens(posts)

        # Use LLM to label the cluster
        sample_texts = "\n".join(post["text"] for post in posts[:10])
        prompt = f"Analyze these crypto-related posts:\n\n{sample_texts}"

        try:
            response = await self.llm_provider.generate(
                prompt,
                system_prompt=LABELING_SYSTEM_PROMPT,
                temperature=0.3,
            )
            data = json.loads(response.text)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("narrative.label.failed", error=str(e))
            return None

        # Calculate momentum based on post count and engagement
        momentum_score = min(10.0, len(posts) / 5.0 * 2.5)

        # Determine trend (simplified — in production would compare to history)
        trend = self._determine_trend(len(posts))

        return Narrative(
            name=data.get("name", "Unknown"),
            momentum_score=round(momentum_score, 1),
            trend=trend,
            tokens=tokens,
            keywords=data.get("keywords", []),
        )

    def _extract_tokens(self, posts: list[dict[str, str]]) -> list[str]:
        """Extract token symbols from posts.

        Looks for $TOKEN patterns.

        Args:
            posts: List of posts.

        Returns:
            List of unique token symbols (uppercase).
        """
        tokens: set[str] = set()
        pattern = r"\$([A-Za-z]{2,10})"

        for post in posts:
            matches = re.findall(pattern, post["text"])
            for match in matches:
                tokens.add(match.upper())

        return list(tokens)

    def _determine_trend(self, post_count: int) -> str:
        """Determine trend direction based on post count.

        In production, this would compare to historical data.

        Args:
            post_count: Number of posts in cluster.

        Returns:
            Trend direction string.
        """
        # Simplified logic — in production would compare to prior period
        if post_count > 10:
            return "accelerating"
        elif post_count > 5:
            return "stable"
        else:
            return "declining"
