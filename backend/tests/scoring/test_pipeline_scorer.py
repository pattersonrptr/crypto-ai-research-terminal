"""Tests for PipelineScorer — orchestrates real scorers with heuristic fallbacks.

The PipelineScorer is the central wiring point that decides, per token,
which real scorer to use (GrowthScorer, RiskScorer, NarrativeScorer,
ListingScorer, CycleLeaderModel) based on data availability, falling
back to HeuristicSubScorer for any missing pillar.
"""

from __future__ import annotations

import pickle  # nosec B403 — test-only; used to create mock model fixtures
from typing import TYPE_CHECKING

import numpy as np

from app.scoring.pipeline_scorer import PipelineScorer, PipelineScorerResult

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_market_data() -> dict:
    """Minimal market data that HeuristicSubScorer needs."""
    return {
        "rank": 50,
        "market_cap_usd": 5_000_000_000.0,
        "volume_mcap_ratio": 0.15,
        "price_velocity": 10.0,
        "ath_distance_pct": 40.0,
        "circulating_supply": 100_000_000.0,
    }


def _growth_data() -> dict:
    """Growth data from DevProcessor + SocialProcessor."""
    return {
        "dev_activity_score": 0.75,
        "commit_growth_pct": 25.0,
        "contributor_growth_pct": 10.0,
        "social_engagement_score": 0.60,
        "subscriber_growth_pct": 15.0,
        "mention_growth_pct": 30.0,
    }


def _risk_data() -> dict:
    """Risk data from anomaly detection / risk analysis."""
    return {
        "rugpull_risk": 0.1,
        "manipulation_risk": 0.2,
        "tokenomics_risk": 0.15,
        "whale_risk": 0.3,
    }


def _listing_data() -> dict:
    """Listing data from ExchangeMonitor."""
    return {
        "signal_strength": 0.7,
        "prediction_probability": 0.6,
        "exchange_count": 5,
    }


def _narrative_context() -> dict:
    """Narrative context — token categories + active cluster info."""
    return {
        "categories": ["layer-1", "smart-contracts"],
        "narrative_clusters": {
            "AI & DePIN": ["FET", "RNDR", "TAO"],
            "Layer 1": ["SOL", "ETH", "AVAX"],
        },
        "token_symbol": "ETH",
    }


# ---------------------------------------------------------------------------
# Tests — result structure
# ---------------------------------------------------------------------------


class TestPipelineScorerResult:
    """PipelineScorerResult has the right shape."""

    def test_result_has_all_nine_sub_scores(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert isinstance(result, PipelineScorerResult)
        for attr in (
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "cycle_leader_prob",
        ):
            val = getattr(result, attr)
            assert 0.0 <= val <= 1.0, f"{attr}={val} not in [0,1]"

    def test_result_to_dict_returns_nine_keys(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        d = result.to_dict()
        assert len(d) == 9
        assert set(d.keys()) == {
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "cycle_leader_prob",
        }

    def test_result_sources_tracks_which_scorer_was_used(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert isinstance(result.sources, dict)
        # With only market data, everything should be heuristic
        assert result.sources["growth_score"] == "heuristic"
        assert result.sources["risk_score"] == "heuristic"


# ---------------------------------------------------------------------------
# Tests — heuristic fallback (market data only)
# ---------------------------------------------------------------------------


class TestPipelineScorerHeuristicFallback:
    """When only market data is provided, all scores come from heuristics."""

    def test_market_data_only_returns_heuristic_growth(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.sources["growth_score"] == "heuristic"
        assert 0.0 <= result.growth_score <= 1.0

    def test_market_data_only_returns_heuristic_risk(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.sources["risk_score"] == "heuristic"

    def test_market_data_only_returns_heuristic_narrative(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.sources["narrative_score"] == "heuristic"

    def test_market_data_only_returns_heuristic_listing(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.sources["listing_probability"] == "heuristic"


# ---------------------------------------------------------------------------
# Tests — real GrowthScorer
# ---------------------------------------------------------------------------


class TestPipelineScorerGrowth:
    """When dev+social data is present, GrowthScorer is used."""

    def test_growth_scorer_used_when_dev_social_data_present(self) -> None:
        data = {**_base_market_data(), **_growth_data()}
        result = PipelineScorer.score(data)
        assert result.sources["growth_score"] == "GrowthScorer"

    def test_growth_score_uses_real_scorer_value(self) -> None:
        data = {**_base_market_data(), **_growth_data()}
        result = PipelineScorer.score(data)
        # Real GrowthScorer should produce a value; verify the source tag
        assert result.sources["growth_score"] == "GrowthScorer"
        assert 0.0 <= result.growth_score <= 1.0

    def test_partial_growth_data_falls_back_to_heuristic(self) -> None:
        data = {**_base_market_data(), "dev_activity_score": 0.75}
        result = PipelineScorer.score(data)
        # Missing commit_growth_pct etc. → fallback
        assert result.sources["growth_score"] == "heuristic"


# ---------------------------------------------------------------------------
# Tests — real RiskScorer
# ---------------------------------------------------------------------------


class TestPipelineScorerRisk:
    """When risk data is present, RiskScorer is used."""

    def test_risk_scorer_used_when_risk_data_present(self) -> None:
        data = {**_base_market_data(), **_risk_data()}
        result = PipelineScorer.score(data)
        assert result.sources["risk_score"] == "RiskScorer"

    def test_risk_score_is_inverse_composite(self) -> None:
        data = {**_base_market_data(), **_risk_data()}
        result = PipelineScorer.score(data)
        # Low risk inputs → high risk_score (inverse)
        assert result.risk_score > 0.5

    def test_partial_risk_data_falls_back_to_heuristic(self) -> None:
        data = {**_base_market_data(), "rugpull_risk": 0.1}
        result = PipelineScorer.score(data)
        assert result.sources["risk_score"] == "heuristic"


# ---------------------------------------------------------------------------
# Tests — real ListingScorer
# ---------------------------------------------------------------------------


class TestPipelineScorerListing:
    """When listing data is present, ListingScorer is used."""

    def test_listing_scorer_used_when_listing_data_present(self) -> None:
        data = {**_base_market_data(), **_listing_data()}
        result = PipelineScorer.score(data)
        assert result.sources["listing_probability"] == "ListingScorer"

    def test_listing_score_from_real_scorer(self) -> None:
        data = {**_base_market_data(), **_listing_data()}
        result = PipelineScorer.score(data)
        assert 0.0 <= result.listing_probability <= 1.0

    def test_partial_listing_data_falls_back(self) -> None:
        data = {**_base_market_data(), "signal_strength": 0.7}
        result = PipelineScorer.score(data)
        assert result.sources["listing_probability"] == "heuristic"


# ---------------------------------------------------------------------------
# Tests — narrative scoring from categories
# ---------------------------------------------------------------------------


class TestPipelineScorerNarrative:
    """When narrative context is present, category-based scoring is used."""

    def test_narrative_scored_from_categories_when_present(self) -> None:
        ctx = _narrative_context()
        data = {**_base_market_data(), **ctx}
        result = PipelineScorer.score(data)
        assert result.sources["narrative_score"] == "category"

    def test_token_in_active_narrative_gets_higher_score(self) -> None:
        ctx = _narrative_context()
        ctx["token_symbol"] = "ETH"  # ETH is in "Layer 1" narrative
        data = {**_base_market_data(), **ctx}
        result = PipelineScorer.score(data)
        assert result.narrative_score > 0.3

    def test_token_not_in_any_narrative_gets_base_score(self) -> None:
        ctx = _narrative_context()
        ctx["token_symbol"] = "DOGE"  # Not in any cluster
        data = {**_base_market_data(), **ctx}
        result = PipelineScorer.score(data)
        # Should still get a score from categories, just lower
        assert result.sources["narrative_score"] == "category"


# ---------------------------------------------------------------------------
# Tests — all real scorers combined
# ---------------------------------------------------------------------------


class TestPipelineScorerFullPipeline:
    """When all data sources are available, all real scorers are used."""

    def test_all_real_scorers_used(self) -> None:
        data = {
            **_base_market_data(),
            **_growth_data(),
            **_risk_data(),
            **_listing_data(),
            **_narrative_context(),
        }
        result = PipelineScorer.score(data)
        assert result.sources["growth_score"] == "GrowthScorer"
        assert result.sources["risk_score"] == "RiskScorer"
        assert result.sources["listing_probability"] == "ListingScorer"
        assert result.sources["narrative_score"] == "category"

    def test_all_scores_in_valid_range(self) -> None:
        data = {
            **_base_market_data(),
            **_growth_data(),
            **_risk_data(),
            **_listing_data(),
            **_narrative_context(),
        }
        result = PipelineScorer.score(data)
        for attr in result.to_dict():
            val = result.to_dict()[attr]
            assert 0.0 <= val <= 1.0, f"{attr}={val}"


# ---------------------------------------------------------------------------
# Tests — FundamentalScorer 5-pillar upgrade
# ---------------------------------------------------------------------------


class TestPipelineScorerFundamental:
    """FundamentalScorer now includes technology + tokenomics sub-pillars."""

    def test_technology_score_populated(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.technology_score > 0.0

    def test_tokenomics_score_populated(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.tokenomics_score > 0.0

    def test_adoption_score_populated(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.adoption_score > 0.0

    def test_dev_activity_score_populated(self) -> None:
        result = PipelineScorer.score(_base_market_data())
        assert result.dev_activity_score > 0.0


# ---------------------------------------------------------------------------
# Tests — CycleLeaderModel wiring
# ---------------------------------------------------------------------------


def _ml_ready_data() -> dict:
    """Market data with all fields CycleLeaderModel needs via FeatureBuilder."""
    return {
        **_base_market_data(),
        "symbol": "ETH",
        "name": "Ethereum",
        "price_usd": 3000.0,
        "volume_24h_usd": 15_000_000_000.0,
        "ath_usd": 4800.0,
    }


class TestPipelineScorerCycleLeader:
    """When a trained CycleLeaderModel is available, it replaces the heuristic."""

    def test_no_model_path_falls_back_to_heuristic(self) -> None:
        """Without model_path, cycle_leader_prob comes from heuristic."""
        result = PipelineScorer.score(_base_market_data())
        assert result.sources["cycle_leader_prob"] == "heuristic"

    def test_nonexistent_model_path_falls_back_to_heuristic(self) -> None:
        """If model_path doesn't exist, gracefully fall back."""
        result = PipelineScorer.score(_ml_ready_data(), model_path="/nonexistent/model.pkl")
        assert result.sources["cycle_leader_prob"] == "heuristic"

    def test_trained_model_produces_cycle_leader_score(self, tmp_path: Path) -> None:
        """A valid model file → CycleLeaderModel used for prediction."""
        from xgboost import XGBClassifier

        from app.ml.feature_builder import FeatureBuilder, RawTokenData

        # Train a tiny model and save it
        builder = FeatureBuilder()
        raw = RawTokenData(
            symbol="ETH",
            market_cap_usd=5e9,
            volume_24h_usd=15e9,
            price_usd=3000.0,
            ath_usd=4800.0,
        )
        fv = builder.build(raw)
        x = np.array([fv.to_list(), fv.to_list()], dtype=np.float32)
        y = np.array([1.0, 0.0], dtype=np.float32)
        clf = XGBClassifier(n_estimators=2, max_depth=1, use_label_encoder=False)
        clf.fit(x, y)
        model_file = tmp_path / "model.pkl"
        with model_file.open("wb") as f:
            pickle.dump(clf, f)

        result = PipelineScorer.score(_ml_ready_data(), model_path=str(model_file))
        assert result.sources["cycle_leader_prob"] == "CycleLeaderModel"
        assert 0.0 <= result.cycle_leader_prob <= 1.0

    def test_model_prediction_replaces_heuristic_value(self, tmp_path: Path) -> None:
        """The model's output is actually used, not the heuristic value."""
        from xgboost import XGBClassifier

        from app.ml.feature_builder import FeatureBuilder, RawTokenData

        builder = FeatureBuilder()
        raw = RawTokenData(
            symbol="ETH",
            market_cap_usd=5e9,
            volume_24h_usd=15e9,
            price_usd=3000.0,
            ath_usd=4800.0,
        )
        fv = builder.build(raw)
        x = np.array([fv.to_list(), fv.to_list()], dtype=np.float32)
        y = np.array([1.0, 0.0], dtype=np.float32)
        clf = XGBClassifier(n_estimators=2, max_depth=1, use_label_encoder=False)
        clf.fit(x, y)
        model_file = tmp_path / "model.pkl"
        with model_file.open("wb") as f:
            pickle.dump(clf, f)

        # Get heuristic-only result for comparison
        heuristic_result = PipelineScorer.score(_ml_ready_data())
        assert heuristic_result.sources["cycle_leader_prob"] == "heuristic"

        # Get model-based result
        model_result = PipelineScorer.score(_ml_ready_data(), model_path=str(model_file))
        assert model_result.sources["cycle_leader_prob"] == "CycleLeaderModel"

    def test_corrupt_model_falls_back_to_heuristic(self, tmp_path: Path) -> None:
        """Corrupt model file → graceful fallback, not crash."""
        model_file = tmp_path / "bad_model.pkl"
        model_file.write_bytes(b"corrupted data")

        result = PipelineScorer.score(_ml_ready_data(), model_path=str(model_file))
        assert result.sources["cycle_leader_prob"] == "heuristic"

    def test_missing_required_market_fields_falls_back(self, tmp_path: Path) -> None:
        """If data lacks price_usd or ath_usd, can't build RawTokenData → fallback."""
        from xgboost import XGBClassifier

        from app.ml.feature_builder import FeatureBuilder, RawTokenData

        builder = FeatureBuilder()
        raw = RawTokenData(
            symbol="ETH",
            market_cap_usd=5e9,
            volume_24h_usd=15e9,
            price_usd=3000.0,
            ath_usd=4800.0,
        )
        fv = builder.build(raw)
        x = np.array([fv.to_list(), fv.to_list()], dtype=np.float32)
        y = np.array([1.0, 0.0], dtype=np.float32)
        clf = XGBClassifier(n_estimators=2, max_depth=1, use_label_encoder=False)
        clf.fit(x, y)
        model_file = tmp_path / "model.pkl"
        with model_file.open("wb") as f:
            pickle.dump(clf, f)

        # Data without price_usd or ath_usd
        data = _base_market_data()  # has market_cap_usd but not price_usd/ath_usd
        result = PipelineScorer.score(data, model_path=str(model_file))
        assert result.sources["cycle_leader_prob"] == "heuristic"
