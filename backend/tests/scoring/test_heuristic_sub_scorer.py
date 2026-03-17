"""Tests for HeuristicSubScorer — derives all sub-scores from CoinGecko market data."""

from typing import Any

from app.scoring.heuristic_sub_scorer import HeuristicSubScorer, SubScoreResult


def _make_market_data(**overrides: Any) -> dict[str, Any]:
    """Build a baseline processed market dict with sensible CoinGecko-like defaults."""
    base: dict[str, Any] = {
        "symbol": "ETH",
        "coingecko_id": "ethereum",
        "name": "Ethereum",
        "price_usd": 3500.0,
        "market_cap_usd": 420_000_000_000.0,
        "volume_24h_usd": 15_000_000_000.0,
        "rank": 2,
        "ath_usd": 4800.0,
        "circulating_supply": 120_000_000.0,
        # MarketProcessor-derived fields
        "volume_mcap_ratio": 0.0357,
        "price_velocity": 2.5,
        "ath_distance_pct": 27.08,
    }
    base.update(overrides)
    return base


class TestSubScoreResultShape:
    """SubScoreResult must expose all 9 sub-score fields in [0, 1]."""

    def test_result_has_all_fields(self) -> None:
        result = SubScoreResult(
            technology_score=0.5,
            tokenomics_score=0.5,
            adoption_score=0.5,
            dev_activity_score=0.5,
            narrative_score=0.5,
            growth_score=0.5,
            risk_score=0.5,
            listing_probability=0.5,
            cycle_leader_prob=0.5,
        )
        assert result.technology_score == 0.5
        assert result.listing_probability == 0.5

    def test_result_to_dict(self) -> None:
        result = SubScoreResult(
            technology_score=0.1,
            tokenomics_score=0.2,
            adoption_score=0.3,
            dev_activity_score=0.4,
            narrative_score=0.5,
            growth_score=0.6,
            risk_score=0.7,
            listing_probability=0.8,
            cycle_leader_prob=0.9,
        )
        d = result.to_dict()
        assert len(d) == 9
        assert d["technology_score"] == 0.1
        assert d["cycle_leader_prob"] == 0.9


class TestHeuristicSubScorerScoresInRange:
    """All sub-scores must be in [0, 1] for valid market data."""

    def test_all_scores_between_0_and_1(self) -> None:
        data = _make_market_data()
        result = HeuristicSubScorer.score(data)
        for field_name in [
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "cycle_leader_prob",
        ]:
            value = getattr(result, field_name)
            assert 0.0 <= value <= 1.0, f"{field_name}={value} out of [0, 1]"


class TestHeuristicAdoptionScore:
    """Adoption score driven by rank and market cap (no volume)."""

    def test_top_rank_gives_high_adoption(self) -> None:
        data = _make_market_data(rank=1, volume_mcap_ratio=0.5)
        result = HeuristicSubScorer.score(data)
        assert result.adoption_score > 0.7

    def test_low_rank_low_mcap_gives_lower_adoption(self) -> None:
        data = _make_market_data(rank=800, market_cap_usd=1_000_000.0, volume_mcap_ratio=0.01)
        result = HeuristicSubScorer.score(data)
        assert result.adoption_score < 0.4


class TestHeuristicTokenomicsScore:
    """Tokenomics driven by circulating supply ratio and market cap tier."""

    def test_high_mcap_gets_reasonable_tokenomics(self) -> None:
        data = _make_market_data(market_cap_usd=100_000_000_000.0)
        result = HeuristicSubScorer.score(data)
        assert result.tokenomics_score > 0.3

    def test_micro_cap_gets_lower_tokenomics(self) -> None:
        data = _make_market_data(market_cap_usd=1_000_000.0, rank=800)
        result = HeuristicSubScorer.score(data)
        assert result.tokenomics_score < 0.5


class TestHeuristicRiskScore:
    """Risk score: higher is *better* (lower risk). Volatile tokens get lower scores."""

    def test_stable_large_cap_has_lower_risk(self) -> None:
        """Large-cap, top-rank, close to ATH → low risk → high risk_score."""
        data = _make_market_data(
            rank=2,
            market_cap_usd=400_000_000_000.0,
            ath_distance_pct=10.0,
            volume_mcap_ratio=0.03,
        )
        result = HeuristicSubScorer.score(data)
        assert result.risk_score > 0.5

    def test_micro_cap_far_from_ath_has_higher_risk(self) -> None:
        """Micro-cap, far from ATH → risky → low risk_score."""
        data = _make_market_data(
            rank=900,
            market_cap_usd=500_000.0,
            ath_distance_pct=95.0,
            volume_mcap_ratio=0.8,
        )
        result = HeuristicSubScorer.score(data)
        assert result.risk_score < 0.4


class TestHeuristicGrowthScore:
    """Growth heuristic: strong momentum tokens get higher growth scores."""

    def test_positive_velocity_good_volume_gives_high_growth(self) -> None:
        data = _make_market_data(price_velocity=50.0, volume_mcap_ratio=0.30)
        result = HeuristicSubScorer.score(data)
        assert result.growth_score > 0.5

    def test_negative_velocity_low_volume_gives_low_growth(self) -> None:
        data = _make_market_data(price_velocity=-20.0, volume_mcap_ratio=0.005)
        result = HeuristicSubScorer.score(data)
        assert result.growth_score < 0.4


class TestHeuristicListingProbability:
    """Listing probability heuristic based on rank and market cap tier."""

    def test_top_10_high_listing_probability(self) -> None:
        data = _make_market_data(rank=5, market_cap_usd=50_000_000_000.0)
        result = HeuristicSubScorer.score(data)
        assert result.listing_probability > 0.7

    def test_low_rank_low_listing_probability(self) -> None:
        data = _make_market_data(rank=900, market_cap_usd=500_000.0)
        result = HeuristicSubScorer.score(data)
        assert result.listing_probability < 0.3


class TestHeuristicMissingData:
    """Scorer handles missing optional fields gracefully."""

    def test_missing_rank_defaults_gracefully(self) -> None:
        data = _make_market_data(rank=None)
        result = HeuristicSubScorer.score(data)
        assert 0.0 <= result.adoption_score <= 1.0

    def test_missing_ath_defaults_gracefully(self) -> None:
        data = _make_market_data(ath_usd=None, ath_distance_pct=0.0)
        result = HeuristicSubScorer.score(data)
        assert 0.0 <= result.risk_score <= 1.0

    def test_zero_market_cap_does_not_crash(self) -> None:
        data = _make_market_data(market_cap_usd=0.0, volume_mcap_ratio=0.0)
        result = HeuristicSubScorer.score(data)
        for field_name in [
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "cycle_leader_prob",
        ]:
            value = getattr(result, field_name)
            assert 0.0 <= value <= 1.0, f"{field_name}={value} out of [0, 1]"
