"""DevProcessor — derives development activity metrics from GitHub data."""

import math
from typing import Any


class DevProcessor:
    """Computes derived development metrics: commit growth, contributor growth, activity score."""

    @staticmethod
    def commit_growth(current_commits: int, previous_commits: int) -> float:
        """Calculate percentage growth in commits between two periods.

        Args:
            current_commits: Commits in the current period.
            previous_commits: Commits in the previous period.

        Returns:
            Percentage change. Returns 0.0 if previous_commits is zero.
        """
        if previous_commits == 0:
            return 0.0
        return (current_commits - previous_commits) / previous_commits * 100.0

    @staticmethod
    def contributor_growth(current_contributors: int, previous_contributors: int) -> float:
        """Calculate percentage growth in contributors between two periods.

        Args:
            current_contributors: Contributors in the current period.
            previous_contributors: Contributors in the previous period.

        Returns:
            Percentage change. Returns 0.0 if previous_contributors is zero.
        """
        if previous_contributors == 0:
            return 0.0
        return (current_contributors - previous_contributors) / previous_contributors * 100.0

    @staticmethod
    def activity_score(commits_30d: int, contributors: int, stars: int, forks: int) -> float:
        """Calculate a composite development activity score (0.0 to 1.0).

        Uses logarithmic scaling to handle wide ranges of activity levels.
        Weights: commits (40%), contributors (30%), stars (20%), forks (10%).

        Args:
            commits_30d: Number of commits in the last 30 days.
            contributors: Total number of contributors.
            stars: Repository star count.
            forks: Repository fork count.

        Returns:
            Normalized activity score between 0.0 and 1.0.
        """
        if all(v == 0 for v in [commits_30d, contributors, stars, forks]):
            return 0.0

        # Use log scaling with reference points for "high activity"
        # Reference points: 300 commits/month, 50 contributors, 10k stars, 2k forks
        def normalize_log(value: int, reference: int) -> float:
            if value == 0:
                return 0.0
            # log(1 + value) / log(1 + reference), capped at 1.0
            return min(1.0, math.log1p(value) / math.log1p(reference))

        commits_score = normalize_log(commits_30d, 300)
        contributors_score = normalize_log(contributors, 50)
        stars_score = normalize_log(stars, 10000)
        forks_score = normalize_log(forks, 2000)

        # Weighted average
        return (
            commits_score * 0.4 + contributors_score * 0.3 + stars_score * 0.2 + forks_score * 0.1
        )

    @classmethod
    def process(cls, raw: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
        """Apply all development-feature computations to a raw GitHub data dict.

        Returns a new dict containing all original fields plus computed
        ``commit_growth_pct``, ``contributor_growth_pct``, and ``dev_activity_score``.

        Args:
            raw: Dict with keys: commits_30d, contributors, stars, forks.
            previous: Optional dict with previous period's commits_30d and contributors.

        Returns:
            New dict with original fields plus computed metrics.
        """
        result = dict(raw)

        prev_commits = previous.get("commits_30d", 0) if previous else 0
        prev_contributors = previous.get("contributors", 0) if previous else 0

        result["commit_growth_pct"] = cls.commit_growth(
            current_commits=raw.get("commits_30d", 0),
            previous_commits=prev_commits,
        )
        result["contributor_growth_pct"] = cls.contributor_growth(
            current_contributors=raw.get("contributors", 0),
            previous_contributors=prev_contributors,
        )
        result["dev_activity_score"] = cls.activity_score(
            commits_30d=raw.get("commits_30d", 0),
            contributors=raw.get("contributors", 0),
            stars=raw.get("stars", 0),
            forks=raw.get("forks", 0),
        )
        return result
