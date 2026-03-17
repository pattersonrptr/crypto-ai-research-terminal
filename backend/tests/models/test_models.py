"""Tests for all SQLAlchemy ORM models.

Each model is tested for:
- correct __tablename__ mapping
- presence of all required columns
- inheritance from the shared declarative Base
"""

from sqlalchemy import inspect

from app.db.base import Base


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------
class TestTokenModel:
    """Token represents a cryptocurrency tracked by the platform."""

    def test_token_model_is_mapped_to_database_table(self) -> None:
        from app.models.token import Token

        assert Token.__tablename__ == "tokens"

    def test_token_model_has_required_columns(self) -> None:
        from app.models.token import Token

        mapper = inspect(Token)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {"id", "symbol", "name", "coingecko_id", "category", "created_at"}.issubset(
            column_names
        )

    def test_token_model_inherits_base(self) -> None:
        from app.models.token import Token

        assert issubclass(Token, Base)


# ---------------------------------------------------------------------------
# MarketData
# ---------------------------------------------------------------------------
class TestMarketDataModel:
    """MarketData stores a point-in-time market snapshot for a token."""

    def test_market_data_model_is_mapped_to_database_table(self) -> None:
        from app.models.market_data import MarketData

        assert MarketData.__tablename__ == "market_data"

    def test_market_data_model_has_required_columns(self) -> None:
        from app.models.market_data import MarketData

        mapper = inspect(MarketData)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {
            "id",
            "token_id",
            "price_usd",
            "market_cap_usd",
            "volume_24h_usd",
            "rank",
            "ath_usd",
            "circulating_supply",
            "collected_at",
        }.issubset(column_names)

    def test_market_data_model_inherits_base(self) -> None:
        from app.models.market_data import MarketData

        assert issubclass(MarketData, Base)


# ---------------------------------------------------------------------------
# DevActivity
# ---------------------------------------------------------------------------
class TestDevActivityModel:
    """DevActivity stores GitHub development metrics for a token."""

    def test_dev_activity_model_is_mapped_to_database_table(self) -> None:
        from app.models.dev_activity import DevActivity

        assert DevActivity.__tablename__ == "dev_activity"

    def test_dev_activity_model_has_required_columns(self) -> None:
        from app.models.dev_activity import DevActivity

        mapper = inspect(DevActivity)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {
            "id",
            "token_id",
            "commits_30d",
            "contributors",
            "stars",
            "forks",
            "open_issues",
            "collected_at",
        }.issubset(column_names)

    def test_dev_activity_model_inherits_base(self) -> None:
        from app.models.dev_activity import DevActivity

        assert issubclass(DevActivity, Base)


# ---------------------------------------------------------------------------
# SocialData
# ---------------------------------------------------------------------------
class TestSocialDataModel:
    """SocialData stores social-media metrics for a token."""

    def test_social_data_model_is_mapped_to_database_table(self) -> None:
        from app.models.social_data import SocialData

        assert SocialData.__tablename__ == "social_data"

    def test_social_data_model_has_required_columns(self) -> None:
        from app.models.social_data import SocialData

        mapper = inspect(SocialData)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {
            "id",
            "token_id",
            "reddit_subscribers",
            "reddit_posts_24h",
            "sentiment_score",
            "twitter_mentions_24h",
            "twitter_engagement",
            "collected_at",
        }.issubset(column_names)

    def test_social_data_model_inherits_base(self) -> None:
        from app.models.social_data import SocialData

        assert issubclass(SocialData, Base)


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------
class TestSignalModel:
    """Signal stores an analytical signal generated for a token."""

    def test_signal_model_is_mapped_to_database_table(self) -> None:
        from app.models.signal import Signal

        assert Signal.__tablename__ == "signals"

    def test_signal_model_has_required_columns(self) -> None:
        from app.models.signal import Signal

        mapper = inspect(Signal)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {"id", "token_id", "signal_type", "value", "generated_at"}.issubset(column_names)

    def test_signal_model_inherits_base(self) -> None:
        from app.models.signal import Signal

        assert issubclass(Signal, Base)


# ---------------------------------------------------------------------------
# TokenScore
# ---------------------------------------------------------------------------
class TestTokenScoreModel:
    """TokenScore stores the composite opportunity score for a token."""

    def test_token_score_model_is_mapped_to_database_table(self) -> None:
        from app.models.score import TokenScore

        assert TokenScore.__tablename__ == "token_scores"

    def test_token_score_model_has_required_columns(self) -> None:
        from app.models.score import TokenScore

        mapper = inspect(TokenScore)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {
            "id",
            "token_id",
            "fundamental_score",
            "opportunity_score",
            "scored_at",
        }.issubset(column_names)

    def test_token_score_model_inherits_base(self) -> None:
        from app.models.score import TokenScore

        assert issubclass(TokenScore, Base)


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------
class TestAlertModel:
    """Alert stores a triggered alert for a token."""

    def test_alert_model_is_mapped_to_database_table(self) -> None:
        from app.models.alert import Alert

        assert Alert.__tablename__ == "alerts"

    def test_alert_model_has_required_columns(self) -> None:
        from app.models.alert import Alert

        mapper = inspect(Alert)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert {"id", "token_id", "alert_type", "message", "triggered_at"}.issubset(column_names)

    def test_alert_model_inherits_base(self) -> None:
        from app.models.alert import Alert

        assert issubclass(Alert, Base)
