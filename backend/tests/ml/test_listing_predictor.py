"""Tests for ListingPredictor.

ML-based prediction of listing probability:
- Feature extraction from token metrics
- Probability estimation using simple heuristic model (Phase 4)
- Will be replaced with trained XGBoost model in later phases
"""

import pytest

from app.ml.listing_predictor import ListingPrediction, ListingPredictor


class TestListingPredictorPredict:
    """ListingPredictor.predict() returns listing probability."""

    def test_listing_predictor_predict_returns_prediction(self) -> None:
        features = {
            "market_cap_usd": 100_000_000.0,
            "volume_24h_usd": 5_000_000.0,
            "exchange_count": 3,
            "github_stars": 500,
            "twitter_followers": 50000,
            "age_days": 180,
        }
        prediction = ListingPredictor.predict(features)
        assert isinstance(prediction, ListingPrediction)

    def test_listing_predictor_predict_returns_probability_in_range(self) -> None:
        features = {
            "market_cap_usd": 100_000_000.0,
            "volume_24h_usd": 5_000_000.0,
            "exchange_count": 3,
            "github_stars": 500,
            "twitter_followers": 50000,
            "age_days": 180,
        }
        prediction = ListingPredictor.predict(features)
        assert 0.0 <= prediction.probability <= 1.0

    def test_listing_predictor_high_quality_token_high_probability(self) -> None:
        """Strong fundamentals = higher listing probability."""
        features = {
            "market_cap_usd": 500_000_000.0,  # High market cap
            "volume_24h_usd": 50_000_000.0,  # High volume
            "exchange_count": 5,  # Already on several exchanges
            "github_stars": 2000,  # Active development
            "twitter_followers": 200000,  # Strong community
            "age_days": 365,  # Established project
        }
        prediction = ListingPredictor.predict(features)
        assert prediction.probability >= 0.6

    def test_listing_predictor_low_quality_token_low_probability(self) -> None:
        """Weak fundamentals = lower listing probability."""
        features = {
            "market_cap_usd": 500_000.0,  # Very low market cap
            "volume_24h_usd": 10_000.0,  # Very low volume
            "exchange_count": 1,  # Only on one exchange
            "github_stars": 5,  # Minimal development
            "twitter_followers": 500,  # Tiny community
            "age_days": 14,  # Very new
        }
        prediction = ListingPredictor.predict(features)
        assert prediction.probability <= 0.4


class TestListingPredictorFeatureImportance:
    """ListingPredictor weights features appropriately."""

    def test_listing_predictor_market_cap_affects_probability(self) -> None:
        base = {
            "market_cap_usd": 10_000_000.0,
            "volume_24h_usd": 1_000_000.0,
            "exchange_count": 2,
            "github_stars": 100,
            "twitter_followers": 10000,
            "age_days": 90,
        }
        high_mcap = {**base, "market_cap_usd": 500_000_000.0}

        base_pred = ListingPredictor.predict(base)
        high_pred = ListingPredictor.predict(high_mcap)
        assert high_pred.probability > base_pred.probability

    def test_listing_predictor_exchange_count_affects_probability(self) -> None:
        base = {
            "market_cap_usd": 50_000_000.0,
            "volume_24h_usd": 1_000_000.0,
            "exchange_count": 1,
            "github_stars": 100,
            "twitter_followers": 10000,
            "age_days": 90,
        }
        more_exchanges = {**base, "exchange_count": 8}

        base_pred = ListingPredictor.predict(base)
        more_pred = ListingPredictor.predict(more_exchanges)
        assert more_pred.probability > base_pred.probability

    def test_listing_predictor_social_following_affects_probability(self) -> None:
        base = {
            "market_cap_usd": 50_000_000.0,
            "volume_24h_usd": 1_000_000.0,
            "exchange_count": 3,
            "github_stars": 100,
            "twitter_followers": 1000,
            "age_days": 90,
        }
        large_following = {**base, "twitter_followers": 500000}

        base_pred = ListingPredictor.predict(base)
        large_pred = ListingPredictor.predict(large_following)
        assert large_pred.probability > base_pred.probability


class TestListingPredictorConfidence:
    """ListingPredictor provides confidence intervals."""

    def test_listing_predictor_provides_confidence(self) -> None:
        features = {
            "market_cap_usd": 100_000_000.0,
            "volume_24h_usd": 5_000_000.0,
            "exchange_count": 3,
            "github_stars": 500,
            "twitter_followers": 50000,
            "age_days": 180,
        }
        prediction = ListingPredictor.predict(features)
        assert hasattr(prediction, "confidence")
        assert 0.0 <= prediction.confidence <= 1.0

    def test_listing_predictor_more_data_higher_confidence(self) -> None:
        """More non-zero features = higher confidence."""
        sparse = {
            "market_cap_usd": 100_000_000.0,
            "volume_24h_usd": 0.0,  # Missing
            "exchange_count": 0,  # Missing
            "github_stars": 0,  # Missing
            "twitter_followers": 0,  # Missing
            "age_days": 90,
        }
        complete = {
            "market_cap_usd": 100_000_000.0,
            "volume_24h_usd": 5_000_000.0,
            "exchange_count": 3,
            "github_stars": 500,
            "twitter_followers": 50000,
            "age_days": 90,
        }

        sparse_pred = ListingPredictor.predict(sparse)
        complete_pred = ListingPredictor.predict(complete)
        assert complete_pred.confidence > sparse_pred.confidence


class TestListingPredictorValidation:
    """ListingPredictor validates input."""

    def test_listing_predictor_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            ListingPredictor.predict({})

    def test_listing_predictor_raises_on_negative_market_cap(self) -> None:
        from app.exceptions import ScoringError

        features = {
            "market_cap_usd": -1000.0,  # Invalid
            "volume_24h_usd": 1_000_000.0,
            "exchange_count": 2,
            "github_stars": 100,
            "twitter_followers": 10000,
            "age_days": 90,
        }
        with pytest.raises(ScoringError):
            ListingPredictor.predict(features)
