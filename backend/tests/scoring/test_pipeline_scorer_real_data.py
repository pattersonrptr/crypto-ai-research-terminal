"""TDD tests for PipelineScorer using real social + dev + CMC data.

Phase 13: when real data fields are present in the pipeline dict,
the scorer must use them instead of heuristic fallbacks.
"""

from __future__ import annotations

from typing import Any

from app.scoring.fundamental_scorer import FundamentalScorer
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
    """Reddit/social data now boosts narrative_score, not adoption_score.

    Adoption is driven by rank + market cap + categories instead.
    """

    def test_social_data_boosts_narrative_not_adoption(self) -> None:
        """With Reddit data, narrative source is 'category' and adoption is 'market'."""
        data = _base_data()
        data["reddit_subscribers"] = 5_000_000
        data["reddit_posts_24h"] = 50
        data["sentiment_score"] = 0.7
        data["categories"] = ["Layer 1"]
        data["token_symbol"] = "SOL"

        result = PipelineScorer.score(data)

        assert result.sources.get("adoption_score") == "market"
        assert result.sources.get("narrative_score") == "category"

    def test_narrative_higher_with_more_subscribers(self) -> None:
        """Token with 5M subscribers should have higher narrative than one with 1K."""
        data_high = _base_data()
        data_high["reddit_subscribers"] = 5_000_000
        data_high["reddit_posts_24h"] = 100
        data_high["sentiment_score"] = 0.5
        data_high["categories"] = ["Layer 1"]
        data_high["token_symbol"] = "SOL"

        data_low = _base_data()
        data_low["reddit_subscribers"] = 1_000
        data_low["reddit_posts_24h"] = 2
        data_low["sentiment_score"] = 0.5
        data_low["categories"] = ["Layer 1"]
        data_low["token_symbol"] = "SOL"

        result_high = PipelineScorer.score(data_high)
        result_low = PipelineScorer.score(data_low)

        assert result_high.narrative_score > result_low.narrative_score

    def test_adoption_score_still_in_range(self) -> None:
        """Adoption score must be in [0.0, 1.0] for FundamentalScorer compatibility."""
        data = _base_data()
        data["reddit_subscribers"] = 10_000_000
        data["reddit_posts_24h"] = 500
        data["sentiment_score"] = 1.0

        result = PipelineScorer.score(data)

        assert 0.0 <= result.adoption_score <= 1.0


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
        """dev_activity_score must be in [0.0, 1.0] for FundamentalScorer compatibility."""
        data = _base_data()
        data["commits_30d"] = 500
        data["contributors"] = 100
        data["stars"] = 50000
        data["forks"] = 10000

        result = PipelineScorer.score(data)

        assert 0.0 <= result.dev_activity_score <= 1.0


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
    """Without real data, heuristic fallback must still work for dev/tech."""

    def test_heuristic_fallback_when_no_extra_data(self) -> None:
        """With only market data, dev/tech use 'heuristic', adoption uses 'market'."""
        data = _base_data()

        result = PipelineScorer.score(data)

        assert result.sources.get("technology_score") == "heuristic"
        # Adoption now always uses rank+mcap (market data) instead of heuristic
        assert result.sources.get("adoption_score") == "market"
        assert result.sources.get("dev_activity_score") == "heuristic"


class TestPipelineScorerTechnologyRange:
    """technology_score from CMC data must be in [0, 1]."""

    def test_technology_score_in_range(self) -> None:
        """technology_score must be in [0.0, 1.0] for FundamentalScorer compatibility."""
        data = _base_data()
        data["cmc_rank"] = 1
        data["cmc_tags"] = ["smart-contracts", "layer-1", "defi", "staking", "web3"]
        data["cmc_category"] = "Smart Contract Platform"

        result = PipelineScorer.score(data)

        assert 0.0 <= result.technology_score <= 1.0


class TestPipelineScorerFundamentalIntegration:
    """PipelineScorer sub-scores must be consumable by FundamentalScorer
    without raising ScoringError — i.e. all in [0, 1]."""

    def test_real_social_data_passes_fundamental_scorer(self) -> None:
        """adoption_score from social data must not raise ScoringError."""
        data = _base_data()
        data["reddit_subscribers"] = 5_000_000
        data["reddit_posts_24h"] = 100
        data["sentiment_score"] = 0.8

        result = PipelineScorer.score(data)

        # Must not raise
        FundamentalScorer.sub_pillar_score(
            technology=result.technology_score,
            tokenomics=result.tokenomics_score,
            adoption=result.adoption_score,
            dev_activity=result.dev_activity_score,
            narrative=result.narrative_score,
        )

    def test_real_dev_data_passes_fundamental_scorer(self) -> None:
        """dev_activity_score from GitHub data must not raise ScoringError."""
        data = _base_data()
        data["commits_30d"] = 500
        data["contributors"] = 200
        data["stars"] = 50_000
        data["forks"] = 20_000

        result = PipelineScorer.score(data)

        FundamentalScorer.sub_pillar_score(
            technology=result.technology_score,
            tokenomics=result.tokenomics_score,
            adoption=result.adoption_score,
            dev_activity=result.dev_activity_score,
            narrative=result.narrative_score,
        )

    def test_real_cmc_data_passes_fundamental_scorer(self) -> None:
        """technology_score from CMC data must not raise ScoringError."""
        data = _base_data()
        data["cmc_rank"] = 1
        data["cmc_tags"] = ["smart-contracts", "layer-1", "defi", "staking", "web3"]
        data["cmc_category"] = "Smart Contract Platform"

        result = PipelineScorer.score(data)

        FundamentalScorer.sub_pillar_score(
            technology=result.technology_score,
            tokenomics=result.tokenomics_score,
            adoption=result.adoption_score,
            dev_activity=result.dev_activity_score,
            narrative=result.narrative_score,
        )

    def test_all_real_data_passes_fundamental_scorer(self) -> None:
        """All real data sources combined must produce [0,1] scores."""
        data = _base_data()
        data["reddit_subscribers"] = 10_000_000
        data["reddit_posts_24h"] = 500
        data["sentiment_score"] = 1.0
        data["commits_30d"] = 500
        data["contributors"] = 200
        data["stars"] = 50_000
        data["forks"] = 20_000
        data["cmc_rank"] = 1
        data["cmc_tags"] = ["smart-contracts", "layer-1", "defi", "staking", "web3"]
        data["cmc_category"] = "Smart Contract Platform"

        result = PipelineScorer.score(data)

        # Every sub-pillar score must be in [0, 1]
        for field_name in (
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
        ):
            value = getattr(result, field_name)
            assert 0.0 <= value <= 1.0, f"{field_name}={value} not in [0, 1]"

        # Must not raise ScoringError
        FundamentalScorer.sub_pillar_score(
            technology=result.technology_score,
            tokenomics=result.tokenomics_score,
            adoption=result.adoption_score,
            dev_activity=result.dev_activity_score,
            narrative=result.narrative_score,
        )
