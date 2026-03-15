"""PipelineScorer — orchestrates real scorers with heuristic fallbacks.

Central wiring point that decides, per token, which real scorer to use
(GrowthScorer, RiskScorer, ListingScorer) based on data availability,
falling back to HeuristicSubScorer for any missing pillar.

This module replaces the pattern of calling HeuristicSubScorer directly
in the pipeline.  When richer data sources are available (GitHub, social,
risk analysis, exchange listings, narrative clusters), the corresponding
real scorer is used; otherwise the heuristic provides a reasonable default.

.. note::

   The NarrativeScorer (LLM-based) is replaced here by a lighter
   category-based scoring function that doesn't require an LLM provider.
   The real NarrativeScorer can be wired in later when LLM is available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from app.ml.cycle_leader_model import CycleLeaderModel
from app.ml.feature_builder import FeatureBuilder, RawTokenData
from app.processors.normalizer import clamp, min_max_normalize
from app.scoring.growth_scorer import GrowthScorer
from app.scoring.heuristic_sub_scorer import HeuristicSubScorer
from app.scoring.listing_scorer import ListingScorer
from app.scoring.risk_scorer import RiskScorer

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Required fields for each real scorer
_GROWTH_FIELDS = {
    "dev_activity_score",
    "commit_growth_pct",
    "contributor_growth_pct",
    "social_engagement_score",
    "subscriber_growth_pct",
    "mention_growth_pct",
}

_RISK_FIELDS = {
    "rugpull_risk",
    "manipulation_risk",
    "tokenomics_risk",
    "whale_risk",
}

_LISTING_FIELDS = {
    "signal_strength",
    "prediction_probability",
    "exchange_count",
}

_NARRATIVE_FIELDS = {
    "categories",
    "token_symbol",
}


@dataclass(frozen=True, slots=True)
class PipelineScorerResult:
    """Immutable container for the 9 sub-scores with source tracking.

    ``sources`` maps each score name to which scorer produced it:
    ``"heuristic"``, ``"GrowthScorer"``, ``"RiskScorer"``,
    ``"ListingScorer"``, ``"category"``.
    """

    technology_score: float
    tokenomics_score: float
    adoption_score: float
    dev_activity_score: float
    narrative_score: float
    growth_score: float
    risk_score: float
    listing_probability: float
    cycle_leader_prob: float
    sources: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float]:
        """Return all 9 sub-scores as a plain dict for easy merging."""
        return {
            "technology_score": self.technology_score,
            "tokenomics_score": self.tokenomics_score,
            "adoption_score": self.adoption_score,
            "dev_activity_score": self.dev_activity_score,
            "narrative_score": self.narrative_score,
            "growth_score": self.growth_score,
            "risk_score": self.risk_score,
            "listing_probability": self.listing_probability,
            "cycle_leader_prob": self.cycle_leader_prob,
        }


class PipelineScorer:
    """Orchestrates real scorers with heuristic fallbacks.

    For each scoring pillar, checks whether the required input data is
    present.  If yes, delegates to the real scorer; if no, uses the
    heuristic from ``HeuristicSubScorer``.
    """

    @classmethod
    def score(
        cls,
        data: dict[str, Any],
        *,
        model_path: str | None = None,
    ) -> PipelineScorerResult:
        """Compute all 9 sub-scores using the best available scorer per pillar.

        Args:
            data: Combined dict containing market data and optionally
                  dev/social metrics, risk data, listing data, and
                  narrative context.
            model_path: Optional path to a trained CycleLeaderModel pickle.
                        When provided and the file exists, the model is used
                        for ``cycle_leader_prob``; otherwise the heuristic
                        fallback is used.

        Returns:
            PipelineScorerResult with scores and source tracking.
        """
        # Always compute heuristic baseline
        heuristic = HeuristicSubScorer.score(data)
        sources: dict[str, str] = {}

        # ── Growth ────────────────────────────────────────────────
        growth_score, growth_src = cls._score_growth(data, heuristic.growth_score)
        sources["growth_score"] = growth_src

        # ── Risk ──────────────────────────────────────────────────
        risk_score, risk_src = cls._score_risk(data, heuristic.risk_score)
        sources["risk_score"] = risk_src

        # ── Listing ───────────────────────────────────────────────
        listing_score, listing_src = cls._score_listing(data, heuristic.listing_probability)
        sources["listing_probability"] = listing_src

        # ── Narrative ─────────────────────────────────────────────
        narrative_score, narrative_src = cls._score_narrative(data, heuristic.narrative_score)
        sources["narrative_score"] = narrative_src

        # ── Cycle leader ──────────────────────────────────────────
        cycle_prob, cycle_src = cls._score_cycle_leader(
            data,
            heuristic.cycle_leader_prob,
            model_path=model_path,
        )
        sources["cycle_leader_prob"] = cycle_src

        # ── Fundamental sub-pillars (always from heuristic for now) ──
        sources["technology_score"] = "heuristic"
        sources["tokenomics_score"] = "heuristic"
        sources["adoption_score"] = "heuristic"
        sources["dev_activity_score"] = "heuristic"

        return PipelineScorerResult(
            technology_score=heuristic.technology_score,
            tokenomics_score=heuristic.tokenomics_score,
            adoption_score=heuristic.adoption_score,
            dev_activity_score=heuristic.dev_activity_score,
            narrative_score=narrative_score,
            growth_score=growth_score,
            risk_score=risk_score,
            listing_probability=listing_score,
            cycle_leader_prob=cycle_prob,
            sources=sources,
        )

    # ------------------------------------------------------------------
    # Per-pillar scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_growth(data: dict[str, Any], fallback: float) -> tuple[float, str]:
        """Use GrowthScorer if all required fields are present."""
        if _GROWTH_FIELDS.issubset(data.keys()):
            try:
                score = GrowthScorer.score(data)
                return score, "GrowthScorer"
            except Exception:
                logger.warning("pipeline_scorer.growth_scorer_failed", exc_info=True)
        return fallback, "heuristic"

    @staticmethod
    def _score_risk(data: dict[str, Any], fallback: float) -> tuple[float, str]:
        """Use RiskScorer if all required fields are present."""
        if _RISK_FIELDS.issubset(data.keys()):
            try:
                result = RiskScorer.score(data)
                return result.composite_score, "RiskScorer"
            except Exception:
                logger.warning("pipeline_scorer.risk_scorer_failed", exc_info=True)
        return fallback, "heuristic"

    @staticmethod
    def _score_listing(data: dict[str, Any], fallback: float) -> tuple[float, str]:
        """Use ListingScorer if all required fields are present."""
        if _LISTING_FIELDS.issubset(data.keys()):
            try:
                result = ListingScorer.score(data)
                return result.score, "ListingScorer"
            except Exception:
                logger.warning("pipeline_scorer.listing_scorer_failed", exc_info=True)
        return fallback, "heuristic"

    @staticmethod
    def _score_narrative(data: dict[str, Any], fallback: float) -> tuple[float, str]:
        """Score narrative from categories and narrative clusters.

        Uses a lightweight category-based approach (no LLM required):
        - Base score from number of categories (more = more narrative fit)
        - Bonus if token appears in active narrative clusters
        """
        if not _NARRATIVE_FIELDS.issubset(data.keys()):
            return fallback, "heuristic"

        categories = data.get("categories", [])
        if not isinstance(categories, list) or not categories:
            return fallback, "heuristic"

        token_symbol = str(data.get("token_symbol", "")).upper()
        narrative_clusters = data.get("narrative_clusters", {})

        # Base score from category count (1 cat = 0.3, 5+ cats = 0.6)
        cat_count = len(categories)
        base_score = min_max_normalize(float(cat_count), 0.0, 5.0) * 0.6

        # Bonus if token is in active narrative clusters
        cluster_bonus = 0.0
        if isinstance(narrative_clusters, dict) and token_symbol:
            for _name, symbols in narrative_clusters.items():
                if token_symbol in [s.upper() for s in symbols]:
                    cluster_bonus += 0.15

        cluster_bonus = min(cluster_bonus, 0.4)

        score = clamp(base_score + cluster_bonus, 0.0, 1.0)
        return score, "category"

    @staticmethod
    def _score_cycle_leader(
        data: dict[str, Any],
        fallback: float,
        *,
        model_path: str | None = None,
    ) -> tuple[float, str]:
        """Use CycleLeaderModel if a trained model is available.

        Requires ``model_path`` to point to a valid pickle file AND the
        pipeline dict to contain the minimum fields needed to construct
        a ``RawTokenData`` (symbol, market_cap_usd, volume_24h_usd,
        price_usd, ath_usd).
        """
        if model_path is None:
            return fallback, "heuristic"

        if not Path(model_path).exists():
            logger.debug(
                "pipeline_scorer.cycle_leader_model_not_found",
                path=model_path,
            )
            return fallback, "heuristic"

        # Check minimum required fields for RawTokenData
        required = {"symbol", "market_cap_usd", "volume_24h_usd", "price_usd", "ath_usd"}
        if not required.issubset(data.keys()):
            logger.debug(
                "pipeline_scorer.cycle_leader_missing_fields",
                missing=required - data.keys(),
            )
            return fallback, "heuristic"

        try:
            model = CycleLeaderModel()
            model.load(model_path)

            builder = FeatureBuilder()
            raw = RawTokenData(
                symbol=str(data["symbol"]),
                market_cap_usd=float(data["market_cap_usd"]),
                volume_24h_usd=float(data["volume_24h_usd"]),
                price_usd=float(data["price_usd"]),
                ath_usd=float(data["ath_usd"]),
                circulating_supply=(
                    float(data["circulating_supply"])
                    if data.get("circulating_supply") is not None
                    else None
                ),
                commits_30d=(
                    int(data["commits_30d"]) if data.get("commits_30d") is not None else None
                ),
                contributors=(
                    int(data["contributors"]) if data.get("contributors") is not None else None
                ),
                stars=(int(data["stars"]) if data.get("stars") is not None else None),
                forks=(int(data["forks"]) if data.get("forks") is not None else None),
                reddit_subscribers=(
                    int(data["reddit_subscribers"])
                    if data.get("reddit_subscribers") is not None
                    else None
                ),
                reddit_posts_24h=(
                    int(data["reddit_posts_24h"])
                    if data.get("reddit_posts_24h") is not None
                    else None
                ),
                sentiment_score=(
                    float(data["sentiment_score"])
                    if data.get("sentiment_score") is not None
                    else None
                ),
                fundamental_score=(
                    float(data["fundamental_score"])
                    if data.get("fundamental_score") is not None
                    else None
                ),
                opportunity_score=(
                    float(data["opportunity_score"])
                    if data.get("opportunity_score") is not None
                    else None
                ),
            )
            fv = builder.build(raw)
            prob = model.predict(fv)
            return clamp(prob, 0.0, 1.0), "CycleLeaderModel"
        except Exception:
            logger.warning("pipeline_scorer.cycle_leader_failed", exc_info=True)
            return fallback, "heuristic"
