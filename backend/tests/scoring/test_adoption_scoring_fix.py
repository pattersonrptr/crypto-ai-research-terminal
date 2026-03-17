"""TDD tests for fixed adoption scoring logic.

Item 4 of Ranking Credibility Sprint: adoption score must reflect real
adoption metrics (rank, market cap, categories/ecosystem) instead of
Reddit subscribers. Social data (Reddit, sentiment) belongs in narrative.

Changes:
- pipeline_scorer._score_adoption() → rank + mcap + category-based
- heuristic_sub_scorer._adoption() → rank_norm + mcap_norm (no volume)
- pipeline_scorer._score_narrative() → include social data when present
"""

from __future__ import annotations

from typing import Any

import pytest

from app.scoring.heuristic_sub_scorer import HeuristicSubScorer
from app.scoring.pipeline_scorer import PipelineScorer


def _base_data() -> dict[str, Any]:
    """Minimal CoinGecko market data dict."""
    return {
        "symbol": "SOL",
        "name": "Solana",
        "coingecko_id": "solana",
        "rank": 5,
        "market_cap_usd": 62_000_000_000,
        "volume_24h_usd": 2_800_000_000,
        "price_usd": 142.0,
        "price_change_24h_pct": 4.5,
        "ath_usd": 260.0,
        "circulating_supply": 430_000_000,
    }


# -----------------------------------------------------------------------
# A) pipeline_scorer._score_adoption() must NOT use Reddit data
# -----------------------------------------------------------------------
class TestAdoptionNoLongerUsesSocialData:
    """Reddit/social data must NOT influence adoption_score."""

    def test_adoption_source_not_social_when_reddit_data_present(self) -> None:
        """Even with Reddit data, adoption source must NOT be 'social'."""
        data = _base_data()
        data["reddit_subscribers"] = 5_000_000
        data["reddit_posts_24h"] = 50
        data["sentiment_score"] = 0.7

        result = PipelineScorer.score(data)

        assert result.sources.get("adoption_score") != "social"

    def test_adoption_score_unchanged_by_reddit_subscribers(self) -> None:
        """Adding Reddit data must not change the adoption_score."""
        data_no_social = _base_data()

        data_with_social = _base_data()
        data_with_social["reddit_subscribers"] = 10_000_000
        data_with_social["reddit_posts_24h"] = 500
        data_with_social["sentiment_score"] = 1.0

        result_no = PipelineScorer.score(data_no_social)
        result_with = PipelineScorer.score(data_with_social)

        assert result_no.adoption_score == pytest.approx(result_with.adoption_score, abs=0.01)


# -----------------------------------------------------------------------
# B) pipeline_scorer._score_adoption() uses rank + mcap + categories
# -----------------------------------------------------------------------
class TestAdoptionUsesRankAndEcosystem:
    """Adoption must be driven by rank, market cap, and ecosystem size."""

    def test_adoption_source_is_market_when_rank_present(self) -> None:
        """With standard market data, adoption source must be 'market'."""
        data = _base_data()

        result = PipelineScorer.score(data)

        # Now market data always provides adoption — no more heuristic fallback
        assert result.sources.get("adoption_score") == "market"

    def test_top_rank_token_scores_higher_adoption(self) -> None:
        """Rank #5 token must score higher adoption than rank #500."""
        data_top = _base_data()
        data_top["rank"] = 5
        data_top["market_cap_usd"] = 62_000_000_000

        data_low = _base_data()
        data_low["rank"] = 500
        data_low["market_cap_usd"] = 50_000_000

        result_top = PipelineScorer.score(data_top)
        result_low = PipelineScorer.score(data_low)

        assert result_top.adoption_score > result_low.adoption_score

    def test_categories_boost_adoption(self) -> None:
        """Token with rich ecosystem categories scores higher adoption."""
        data_rich = _base_data()
        data_rich["categories"] = [
            "Smart Contract Platform",
            "Layer 1",
            "DeFi",
            "Staking",
            "NFTs",
        ]

        data_none = _base_data()
        # No categories

        result_rich = PipelineScorer.score(data_rich)
        result_none = PipelineScorer.score(data_none)

        assert result_rich.adoption_score > result_none.adoption_score

    def test_adoption_score_in_range(self) -> None:
        """Adoption score must be in [0.0, 1.0]."""
        data = _base_data()
        data["rank"] = 1
        data["market_cap_usd"] = 1_000_000_000_000
        data["categories"] = ["L1", "DeFi", "Staking", "NFTs", "Gaming"]

        result = PipelineScorer.score(data)

        assert 0.0 <= result.adoption_score <= 1.0

    def test_adoption_score_low_for_micro_cap(self) -> None:
        """Micro-cap unknown token should have low adoption score."""
        data = _base_data()
        data["rank"] = 900
        data["market_cap_usd"] = 1_000_000  # $1M

        result = PipelineScorer.score(data)

        assert result.adoption_score < 0.40


# -----------------------------------------------------------------------
# C) Social data now boosts narrative, not adoption
# -----------------------------------------------------------------------
class TestSocialDataBoostsNarrative:
    """Reddit/sentiment data must increase narrative_score."""

    def test_narrative_higher_with_reddit_data(self) -> None:
        """Adding Reddit data must raise the narrative_score."""
        data_base = _base_data()
        data_base["categories"] = ["Layer 1"]
        data_base["token_symbol"] = "SOL"

        data_social = _base_data()
        data_social["categories"] = ["Layer 1"]
        data_social["token_symbol"] = "SOL"
        data_social["reddit_subscribers"] = 5_000_000
        data_social["reddit_posts_24h"] = 100
        data_social["sentiment_score"] = 0.8

        result_base = PipelineScorer.score(data_base)
        result_social = PipelineScorer.score(data_social)

        assert result_social.narrative_score > result_base.narrative_score


# -----------------------------------------------------------------------
# D) heuristic_sub_scorer._adoption() no longer uses volume
# -----------------------------------------------------------------------
class TestHeuristicAdoptionNoVolume:
    """Heuristic adoption must use rank + mcap, not volume."""

    def test_heuristic_adoption_unaffected_by_volume(self) -> None:
        """Two tokens with same rank/mcap but different volume → same adoption."""
        data_high_vol = {
            "rank": 50,
            "market_cap_usd": 5_000_000_000,
            "volume_24h_usd": 10_000_000_000,  # extreme volume
            "price_usd": 10.0,
            "price_change_24h_pct": 50.0,
            "ath_usd": 15.0,
            "circulating_supply": 500_000_000,
            "volume_mcap_ratio": 2.0,
            "price_velocity": 50.0,
            "ath_distance_pct": 33.0,
        }
        data_low_vol = {
            "rank": 50,
            "market_cap_usd": 5_000_000_000,
            "volume_24h_usd": 100_000_000,  # normal volume
            "price_usd": 10.0,
            "price_change_24h_pct": 2.0,
            "ath_usd": 15.0,
            "circulating_supply": 500_000_000,
            "volume_mcap_ratio": 0.02,
            "price_velocity": 2.0,
            "ath_distance_pct": 33.0,
        }

        result_high = HeuristicSubScorer.score(data_high_vol)
        result_low = HeuristicSubScorer.score(data_low_vol)

        assert result_high.adoption_score == pytest.approx(result_low.adoption_score, abs=0.01)

    def test_heuristic_adoption_higher_for_top_rank(self) -> None:
        """Rank #5 token must have higher heuristic adoption than rank #500."""
        data_top = {
            "rank": 5,
            "market_cap_usd": 60_000_000_000,
            "volume_24h_usd": 1_000_000_000,
            "price_usd": 100.0,
            "price_change_24h_pct": 0.0,
            "ath_usd": 200.0,
            "circulating_supply": 600_000_000,
            "volume_mcap_ratio": 0.017,
            "price_velocity": 0.0,
            "ath_distance_pct": 50.0,
        }
        data_low = {
            "rank": 500,
            "market_cap_usd": 50_000_000,
            "volume_24h_usd": 5_000_000,
            "price_usd": 0.5,
            "price_change_24h_pct": 0.0,
            "ath_usd": 1.0,
            "circulating_supply": 100_000_000,
            "volume_mcap_ratio": 0.1,
            "price_velocity": 0.0,
            "ath_distance_pct": 50.0,
        }

        result_top = HeuristicSubScorer.score(data_top)
        result_low = HeuristicSubScorer.score(data_low)

        assert result_top.adoption_score > result_low.adoption_score
