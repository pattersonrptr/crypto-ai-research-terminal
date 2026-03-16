"""TDD tests for PipelineScorer using real social + dev + CMC data.

Phase 13: when real data fields are present in the pipeline dict,
the scorer must use them instead of heuristic fallbacks.
"""

from __future__ import annotations

from typing import Any

from app.scoring.pipeline_scorer import PipelineScorer


def _base_data() -> dict[str, Any]:
    """Return minimal market data dict for a token."""
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


class TestPipelineScorerWithSocialData:
    """When reddit_subscribers and reddit_posts_24h are present,
    adoption_score should use real data, not heuristic."""

    def test_adoption_score_from_real_social_data(self) -> None:
        """With reddit data, adoption_score source must be 'social'."""
        data = _base_data()
        data["reddit_subscribers"] = 5_000_000
        data["reddit_posts_24h"] = 50
        data["sentiment_score"] = 0.7

        result = PipelineScorer.score(data)

        assert result.sources.get("adoption_score") == "social"

    def test_adoption_score_higher_with_more_subscribers(self) -> None:
        """Token with 5M subscribers should score higher than one with 1K."""
        data_high = _base_data()
        data_high["reddit_subscribers"] = 5_000_000
        data_high["reddit_posts_24h"] = 100
        data_high["sentiment_score"] = 0.5

        data_low = _base_data()
        data_low["reddit_subscribers"] = 1_000
        data_low["reddit_posts_24h"] = 2
        data_low["sentiment_score"] = 0.5

        result_high = PipelineScorer.score(data_high)
        result_low = PipelineScorer.score(data_low)

        assert result_high.adoption_score > result_low.adoption_score

    def test_adoption_score_still_in_range(self) -> None:
        """Adoption score must be in [0.0, 10.0]."""
        data = _base_data()
        data["reddit_subscribers"] = 10_000_000
        data["reddit_posts_24h"] = 500
        data["sentiment_score"] = 1.0

        result = PipelineScorer.score(data)

        assert 0.0 <= result.adoption_score <= 10.0


class TestPipelineScorerWithDevData:
    """When commits_30d, stars, etc. are present,
    dev_activity_score should use real data."""

    def test_dev_activity_from_real_dev_data(self) -> None:
        """With dev data, dev_activity_score source must be 'dev'."""
        data = _base_data()
        data["commits_30d"] = 200
        data["contributors"] = 50
        data["stars"] = 15000
        data["forks"] = 3000

        result = PipelineScorer.score(data)

        assert result.sources.get("dev_activity_score") == "dev"

    def test_dev_activity_higher_with_more_commits(self) -> None:
        """Token with 200 commits should score higher than one with 5."""
        data_active = _base_data()
        data_active["commits_30d"] = 200
        data_active["contributors"] = 50
        data_active["stars"] = 15000
        data_active["forks"] = 3000

        data_inactive = _base_data()
        data_inactive["commits_30d"] = 5
        data_inactive["contributors"] = 2
        data_inactive["stars"] = 100
        data_inactive["forks"] = 10

        result_active = PipelineScorer.score(data_active)
        result_inactive = PipelineScorer.score(data_inactive)

        assert result_active.dev_activity_score > result_inactive.dev_activity_score

    def test_dev_activity_score_in_range(self) -> None:
        """dev_activity_score must be in [0.0, 10.0]."""
        data = _base_data()
        data["commits_30d"] = 500
        data["contributors"] = 100
        data["stars"] = 50000
        data["forks"] = 10000

        result = PipelineScorer.score(data)

        assert 0.0 <= result.dev_activity_score <= 10.0


class TestPipelineScorerWithCmcData:
    """When cmc_rank and cmc_tags are present,
    technology_score should benefit from CMC metadata."""

    def test_technology_from_cmc_data(self) -> None:
        """With CMC data, technology_score source must be 'cmc'."""
        data = _base_data()
        data["cmc_rank"] = 5
        data["cmc_tags"] = ["smart-contracts", "layer-1", "ethereum-ecosystem"]
        data["cmc_category"] = "Smart Contract Platform"

        result = PipelineScorer.score(data)

        assert result.sources.get("technology_score") == "cmc"

    def test_technology_higher_with_more_tags(self) -> None:
        """Token with more relevant tags should score higher."""
        data_rich = _base_data()
        data_rich["cmc_rank"] = 5
        data_rich["cmc_tags"] = [
            "smart-contracts",
            "layer-1",
            "ethereum-ecosystem",
            "defi",
            "staking",
        ]
        data_rich["cmc_category"] = "Smart Contract Platform"

        data_poor = _base_data()
        data_poor["cmc_rank"] = 200
        data_poor["cmc_tags"] = []
        data_poor["cmc_category"] = ""

        result_rich = PipelineScorer.score(data_rich)
        result_poor = PipelineScorer.score(data_poor)

        assert result_rich.technology_score >= result_poor.technology_score


class TestPipelineScorerFallbackPreserved:
    """Without real data, heuristic fallback must still work."""

    def test_heuristic_fallback_when_no_extra_data(self) -> None:
        """With only market data, all scores should use 'heuristic'."""
        data = _base_data()

        result = PipelineScorer.score(data)

        assert result.sources.get("technology_score") == "heuristic"
        assert result.sources.get("adoption_score") == "heuristic"
        assert result.sources.get("dev_activity_score") == "heuristic"
