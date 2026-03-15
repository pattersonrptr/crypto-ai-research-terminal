"""NarrativePersister — converts NarrativeDetector output to DB-ready ORM objects.

Two modes:
1. ``to_clusters()`` — convert ``NarrativeDetectorResult`` (from real social data)
   into ``NarrativeCluster`` rows.
2. ``build_from_categories()`` — fallback that derives basic narratives from
   CoinGecko token category metadata when social data is unavailable.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from datetime import date

    from app.ai.narrative_detector import NarrativeDetectorResult

from app.models.narrative import NarrativeCluster

logger = structlog.get_logger(__name__)

# Category keywords → narrative name mapping for fallback mode
_CATEGORY_MAPPING: dict[str, str] = {
    "artificial-intelligence": "AI & Machine Learning",
    "ai": "AI & Machine Learning",
    "machine learning": "AI & Machine Learning",
    "machine-learning": "AI & Machine Learning",
    "gpu": "AI & Machine Learning",
    "layer 2": "Layer 2 Scaling",
    "layer-2": "Layer 2 Scaling",
    "optimistic rollup": "Layer 2 Scaling",
    "zk-rollup": "Layer 2 Scaling",
    "real world assets": "Real World Assets",
    "rwa": "Real World Assets",
    "tokenised assets": "Real World Assets",
    "defi": "DeFi",
    "decentralized-finance": "DeFi",
    "lending": "DeFi Lending",
    "borrowing": "DeFi Lending",
    "meme": "Meme Coins",
    "meme-token": "Meme Coins",
    "gaming": "GameFi & Metaverse",
    "gamefi": "GameFi & Metaverse",
    "metaverse": "GameFi & Metaverse",
    "nft": "NFT & Digital Collectibles",
    "privacy": "Privacy",
    "oracle": "Oracles & Data",
    "storage": "Decentralized Storage",
    "layer 1": "Layer 1 Platforms",
    "layer-1": "Layer 1 Platforms",
    "modular blockchain": "Modular Blockchains",
}

_MIN_TOKENS_PER_NARRATIVE = 2


class NarrativePersister:
    """Converts narrative detection output into persistable ORM objects."""

    @staticmethod
    def to_clusters(
        result: NarrativeDetectorResult,
        *,
        snapshot_date: date,
    ) -> list[NarrativeCluster]:
        """Convert NarrativeDetector output to NarrativeCluster ORM objects.

        Args:
            result: Output from :meth:`NarrativeDetector.detect`.
            snapshot_date: Date to tag the snapshot.

        Returns:
            List of :class:`NarrativeCluster` ORM instances (not yet persisted).
        """
        clusters: list[NarrativeCluster] = []

        for narrative in result.narratives:
            momentum = min(narrative.momentum_score, 10.0)

            cluster = NarrativeCluster(
                name=narrative.name,
                momentum_score=round(momentum, 2),
                trend=narrative.trend,
                token_symbols=narrative.tokens,
                keywords=narrative.keywords,
                snapshot_date=snapshot_date,
            )
            clusters.append(cluster)

        logger.info(
            "narrative_persister.to_clusters",
            count=len(clusters),
            snapshot_date=str(snapshot_date),
        )
        return clusters

    @staticmethod
    def build_from_categories(
        token_data: list[dict[str, Any]],
        *,
        snapshot_date: date,
    ) -> list[NarrativeCluster]:
        """Build basic narratives from token category metadata.

        This is the fallback path when social data is unavailable (no
        Twitter/Reddit posts to cluster). Groups tokens by their CoinGecko
        categories and creates one narrative per group.

        Args:
            token_data: List of dicts with ``symbol`` and ``categories`` keys.
            snapshot_date: Date to tag the snapshot.

        Returns:
            List of :class:`NarrativeCluster` ORM instances.
        """
        if not token_data:
            return []

        # Group tokens by mapped narrative
        narrative_tokens: dict[str, list[str]] = defaultdict(list)

        for token in token_data:
            symbol = token.get("symbol", "")
            categories: list[str] = token.get("categories", [])
            if not categories:
                continue

            for category in categories:
                cat_lower = category.lower().strip()
                narrative_name = _CATEGORY_MAPPING.get(cat_lower)
                if narrative_name and symbol not in narrative_tokens[narrative_name]:
                    narrative_tokens[narrative_name].append(symbol)

        # Build clusters, filtering out those with too few tokens
        clusters: list[NarrativeCluster] = []
        for name, tokens in sorted(narrative_tokens.items()):
            if len(tokens) < _MIN_TOKENS_PER_NARRATIVE:
                continue

            cluster = NarrativeCluster(
                name=name,
                momentum_score=5.0,  # neutral default for category-based
                trend="stable",
                token_symbols=tokens,
                keywords=[name.lower()],
                snapshot_date=snapshot_date,
            )
            clusters.append(cluster)

        logger.info(
            "narrative_persister.build_from_categories",
            count=len(clusters),
            snapshot_date=str(snapshot_date),
        )
        return clusters
