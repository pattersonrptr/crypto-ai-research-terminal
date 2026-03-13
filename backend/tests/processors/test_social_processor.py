"""TDD tests for SocialProcessor — social metrics processor."""

from app.processors.social_processor import SocialProcessor


class TestSocialProcessorMentionGrowth:
    """Tests for SocialProcessor.mention_growth() method."""

    def test_mention_growth_positive(self) -> None:
        """mention_growth() returns positive percentage when mentions increased."""
        result = SocialProcessor.mention_growth(current_mentions=150, previous_mentions=100)
        assert result == 50.0

    def test_mention_growth_negative(self) -> None:
        """mention_growth() returns negative percentage when mentions decreased."""
        result = SocialProcessor.mention_growth(current_mentions=50, previous_mentions=100)
        assert result == -50.0

    def test_mention_growth_zero_previous(self) -> None:
        """mention_growth() returns 0.0 when previous mentions is zero."""
        result = SocialProcessor.mention_growth(current_mentions=100, previous_mentions=0)
        assert result == 0.0

    def test_mention_growth_no_change(self) -> None:
        """mention_growth() returns 0.0 when mentions are the same."""
        result = SocialProcessor.mention_growth(current_mentions=100, previous_mentions=100)
        assert result == 0.0


class TestSocialProcessorSubscriberGrowth:
    """Tests for SocialProcessor.subscriber_growth() method."""

    def test_subscriber_growth_positive(self) -> None:
        """subscriber_growth() returns positive percentage when subscribers increased."""
        result = SocialProcessor.subscriber_growth(
            current_subscribers=125000, previous_subscribers=100000
        )
        assert result == 25.0

    def test_subscriber_growth_negative(self) -> None:
        """subscriber_growth() returns negative percentage when subscribers decreased."""
        result = SocialProcessor.subscriber_growth(
            current_subscribers=90000, previous_subscribers=100000
        )
        assert result == -10.0

    def test_subscriber_growth_zero_previous(self) -> None:
        """subscriber_growth() returns 0.0 when previous subscribers is zero."""
        result = SocialProcessor.subscriber_growth(current_subscribers=1000, previous_subscribers=0)
        assert result == 0.0


class TestSocialProcessorEngagementScore:
    """Tests for SocialProcessor.engagement_score() method."""

    def test_engagement_score_range(self) -> None:
        """engagement_score() returns a value between 0.0 and 1.0."""
        result = SocialProcessor.engagement_score(
            subscribers=100000, active_users=1000, posts_24h=50, avg_score=200.0
        )
        assert 0.0 <= result <= 1.0

    def test_engagement_score_high_engagement(self) -> None:
        """engagement_score() returns high score for very engaged communities."""
        result = SocialProcessor.engagement_score(
            subscribers=500000, active_users=10000, posts_24h=200, avg_score=1000.0
        )
        assert result >= 0.6

    def test_engagement_score_low_engagement(self) -> None:
        """engagement_score() returns low score for inactive communities."""
        result = SocialProcessor.engagement_score(
            subscribers=100, active_users=2, posts_24h=1, avg_score=5.0
        )
        assert result <= 0.3

    def test_engagement_score_zero_input(self) -> None:
        """engagement_score() returns 0.0 for completely inactive communities."""
        result = SocialProcessor.engagement_score(
            subscribers=0, active_users=0, posts_24h=0, avg_score=0.0
        )
        assert result == 0.0


class TestSocialProcessorProcess:
    """Tests for SocialProcessor.process() method."""

    def test_process_returns_all_fields(self) -> None:
        """process() returns dict with all computed social metrics."""
        raw = {
            "subreddit": "solana",
            "subscribers": 250000,
            "active_users": 1500,
            "posts_24h": 30,
            "avg_score": 150.0,
        }
        previous = {
            "posts_24h": 25,
            "subscribers": 240000,
        }
        result = SocialProcessor.process(raw, previous)

        assert "mention_growth_pct" in result
        assert "subscriber_growth_pct" in result
        assert "social_engagement_score" in result
        # Original fields preserved
        assert result["subreddit"] == "solana"
        assert result["subscribers"] == 250000

    def test_process_without_previous(self) -> None:
        """process() handles missing previous data gracefully."""
        raw = {
            "subscribers": 100000,
            "active_users": 500,
            "posts_24h": 20,
            "avg_score": 100.0,
        }
        result = SocialProcessor.process(raw, previous=None)

        assert result["mention_growth_pct"] == 0.0
        assert result["subscriber_growth_pct"] == 0.0
        assert "social_engagement_score" in result

    def test_process_calculates_correct_growth(self) -> None:
        """process() calculates growth percentages correctly."""
        raw = {
            "subscribers": 110000,
            "active_users": 1000,
            "posts_24h": 60,
            "avg_score": 200.0,
        }
        previous = {"posts_24h": 50, "subscribers": 100000}
        result = SocialProcessor.process(raw, previous)

        assert result["mention_growth_pct"] == 20.0  # (60-50)/50 * 100
        assert result["subscriber_growth_pct"] == 10.0  # (110k-100k)/100k * 100
