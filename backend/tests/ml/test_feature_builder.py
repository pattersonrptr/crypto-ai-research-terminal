"""Tests for ml/feature_builder.py — TDD Red phase.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

import pytest

from app.ml.feature_builder import FeatureBuilder, FeatureVector, RawTokenData

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def full_data() -> RawTokenData:
    """A complete RawTokenData with all fields populated."""
    return RawTokenData(
        symbol="SOL",
        market_cap_usd=60_000_000_000.0,
        volume_24h_usd=3_000_000_000.0,
        price_usd=150.0,
        ath_usd=260.0,
        circulating_supply=440_000_000.0,
        commits_30d=180,
        contributors=95,
        stars=12_000,
        forks=2_500,
        reddit_subscribers=320_000,
        reddit_posts_24h=140,
        sentiment_score=0.65,
        fundamental_score=0.82,
        opportunity_score=0.77,
    )


@pytest.fixture
def minimal_data() -> RawTokenData:
    """A RawTokenData with only the required price / market-cap fields."""
    return RawTokenData(
        symbol="UNKNOWN",
        market_cap_usd=500_000.0,
        volume_24h_usd=10_000.0,
        price_usd=0.001,
        ath_usd=0.05,
    )


@pytest.fixture
def builder() -> FeatureBuilder:
    return FeatureBuilder()


# ---------------------------------------------------------------------------
# RawTokenData
# ---------------------------------------------------------------------------


class TestRawTokenData:
    def test_raw_token_data_creation_with_full_fields_succeeds(
        self, full_data: RawTokenData
    ) -> None:
        """RawTokenData must accept all optional fields without error."""
        assert full_data.symbol == "SOL"
        assert full_data.market_cap_usd == 60_000_000_000.0

    def test_raw_token_data_creation_with_minimal_fields_succeeds(
        self, minimal_data: RawTokenData
    ) -> None:
        """Optional fields must default to None."""
        assert minimal_data.commits_30d is None
        assert minimal_data.reddit_subscribers is None
        assert minimal_data.fundamental_score is None


# ---------------------------------------------------------------------------
# FeatureVector
# ---------------------------------------------------------------------------


class TestFeatureVector:
    def test_feature_vector_to_list_returns_numeric_values(
        self, full_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """to_list() must return a list of floats with no None values."""
        fv = builder.build(full_data)
        values = fv.to_list()
        assert isinstance(values, list)
        assert all(isinstance(v, float) for v in values)

    def test_feature_vector_to_list_length_is_consistent(
        self, full_data: RawTokenData, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """Full and minimal data must produce vectors of the same length."""
        fv_full = builder.build(full_data)
        fv_minimal = builder.build(minimal_data)
        assert len(fv_full.to_list()) == len(fv_minimal.to_list())

    def test_feature_vector_feature_names_matches_to_list_length(
        self, full_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """feature_names() must have same length as to_list()."""
        fv = builder.build(full_data)
        assert len(fv.feature_names()) == len(fv.to_list())

    def test_feature_vector_symbol_is_preserved(
        self, full_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """FeatureVector must carry the token symbol."""
        fv = builder.build(full_data)
        assert fv.symbol == "SOL"


# ---------------------------------------------------------------------------
# FeatureBuilder.build — market features
# ---------------------------------------------------------------------------


class TestFeatureBuilderMarketFeatures:
    def test_build_volume_to_mcap_ratio_is_correct(
        self, full_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """volume_to_mcap must equal volume_24h / market_cap."""
        fv = builder.build(full_data)
        expected = full_data.volume_24h_usd / full_data.market_cap_usd
        assert abs(fv.volume_to_mcap - expected) < 1e-9

    def test_build_ath_distance_is_between_0_and_1(
        self, full_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """ath_distance must be in [0, 1]."""
        fv = builder.build(full_data)
        assert 0.0 <= fv.ath_distance <= 1.0

    def test_build_ath_distance_at_ath_is_zero(self, builder: FeatureBuilder) -> None:
        """ath_distance must be 0.0 when current price equals ATH."""
        data = RawTokenData(
            symbol="ATH",
            market_cap_usd=1_000_000.0,
            volume_24h_usd=50_000.0,
            price_usd=100.0,
            ath_usd=100.0,
        )
        fv = builder.build(data)
        assert fv.ath_distance == pytest.approx(0.0)

    def test_build_mcap_log_is_positive_for_large_cap(
        self, full_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """mcap_log must be a positive float for any real market cap."""
        fv = builder.build(full_data)
        assert fv.mcap_log > 0.0


# ---------------------------------------------------------------------------
# FeatureBuilder.build — dev / social features with missing data
# ---------------------------------------------------------------------------


class TestFeatureBuilderMissingData:
    def test_build_with_no_dev_data_returns_zero_dev_features(
        self, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """When dev data is absent, dev-related features must default to 0.0."""
        fv = builder.build(minimal_data)
        assert fv.commits_30d_log == 0.0
        assert fv.stars_log == 0.0
        assert fv.contributors_log == 0.0

    def test_build_with_no_social_data_returns_zero_social_features(
        self, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """When social data is absent, social features must default to 0.0."""
        fv = builder.build(minimal_data)
        assert fv.reddit_subscribers_log == 0.0
        assert fv.sentiment_score == 0.0

    def test_build_with_no_scores_returns_zero_score_features(
        self, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """When scores are absent, score features must default to 0.0."""
        fv = builder.build(minimal_data)
        assert fv.fundamental_score == 0.0
        assert fv.opportunity_score == 0.0

    def test_build_never_raises_for_minimal_data(
        self, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """build() must not raise even with only required fields filled."""
        try:
            builder.build(minimal_data)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"build() raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# FeatureBuilder.build_batch
# ---------------------------------------------------------------------------


class TestFeatureBuilderBatch:
    def test_build_batch_returns_list_of_feature_vectors(
        self, full_data: RawTokenData, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """build_batch() must return one FeatureVector per input."""
        result = builder.build_batch([full_data, minimal_data])
        assert len(result) == 2
        assert all(isinstance(fv, FeatureVector) for fv in result)

    def test_build_batch_preserves_order(
        self, full_data: RawTokenData, minimal_data: RawTokenData, builder: FeatureBuilder
    ) -> None:
        """build_batch() must preserve input order."""
        result = builder.build_batch([full_data, minimal_data])
        assert result[0].symbol == "SOL"
        assert result[1].symbol == "UNKNOWN"

    def test_build_batch_empty_input_returns_empty_list(self, builder: FeatureBuilder) -> None:
        """build_batch([]) must return []."""
        assert builder.build_batch([]) == []
