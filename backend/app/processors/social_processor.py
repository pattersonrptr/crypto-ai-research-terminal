"""SocialProcessor — derives social engagement metrics from Reddit data."""

import math
from typing import Any


class SocialProcessor:
    """Computes derived social metrics: mention growth, subscriber growth, engagement score."""

    @staticmethod
    def mention_growth(current_mentions: int, previous_mentions: int) -> float:
        """Calculate percentage growth in mentions/posts between two periods.

        Args:
            current_mentions: Mentions/posts in the current period.
            previous_mentions: Mentions/posts in the previous period.

        Returns:
            Percentage change. Returns 0.0 if previous_mentions is zero.
        """
        if previous_mentions == 0:
            return 0.0
        return (current_mentions - previous_mentions) / previous_mentions * 100.0

    @staticmethod
    def subscriber_growth(current_subscribers: int, previous_subscribers: int) -> float:
        """Calculate percentage growth in subscribers between two periods.

        Args:
            current_subscribers: Subscribers in the current period.
            previous_subscribers: Subscribers in the previous period.

        Returns:
            Percentage change. Returns 0.0 if previous_subscribers is zero.
        """
        if previous_subscribers == 0:
            return 0.0
        return (current_subscribers - previous_subscribers) / previous_subscribers * 100.0

    @staticmethod
    def engagement_score(
        subscribers: int, active_users: int, posts_24h: int, avg_score: float
    ) -> float:
        """Calculate a composite social engagement score (0.0 to 1.0).

        Uses logarithmic scaling to handle wide ranges of engagement levels.
        Weights: subscribers (25%), active users (35%), posts (20%), avg_score (20%).

        Args:
            subscribers: Total subreddit subscribers.
            active_users: Currently active users.
            posts_24h: Number of posts in the last 24 hours.
            avg_score: Average post score.

        Returns:
            Normalized engagement score between 0.0 and 1.0.
        """
        if all(v == 0 for v in [subscribers, active_users, posts_24h]) and avg_score == 0.0:
            return 0.0

        # Use log scaling with reference points for "high engagement"
        # Reference points: 500k subscribers, 5k active, 100 posts/day, 500 avg score
        def normalize_log(value: float, reference: float) -> float:
            if value == 0:
                return 0.0
            return min(1.0, math.log1p(value) / math.log1p(reference))

        subscribers_score = normalize_log(subscribers, 500000)
        active_score = normalize_log(active_users, 5000)
        posts_score = normalize_log(posts_24h, 100)
        avg_score_normalized = normalize_log(avg_score, 500)

        # Weighted average
        return (
            subscribers_score * 0.25
            + active_score * 0.35
            + posts_score * 0.20
            + avg_score_normalized * 0.20
        )

    @classmethod
    def process(cls, raw: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
        """Apply all social-feature computations to a raw Reddit data dict.

        Returns a new dict containing all original fields plus computed
        ``mention_growth_pct``, ``subscriber_growth_pct``, and ``social_engagement_score``.

        Args:
            raw: Dict with keys: subscribers, active_users, posts_24h, avg_score.
            previous: Optional dict with previous period's posts_24h and subscribers.

        Returns:
            New dict with original fields plus computed metrics.
        """
        result = dict(raw)

        prev_posts = previous.get("posts_24h", 0) if previous else 0
        prev_subscribers = previous.get("subscribers", 0) if previous else 0

        result["mention_growth_pct"] = cls.mention_growth(
            current_mentions=raw.get("posts_24h", 0),
            previous_mentions=prev_posts,
        )
        result["subscriber_growth_pct"] = cls.subscriber_growth(
            current_subscribers=raw.get("subscribers", 0),
            previous_subscribers=prev_subscribers,
        )
        result["social_engagement_score"] = cls.engagement_score(
            subscribers=raw.get("subscribers", 0),
            active_users=raw.get("active_users", 0),
            posts_24h=raw.get("posts_24h", 0),
            avg_score=raw.get("avg_score", 0.0),
        )
        return result
