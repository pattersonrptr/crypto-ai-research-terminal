"""TDD tests for DevProcessor — development activity metrics processor."""

from app.processors.dev_processor import DevProcessor


class TestDevProcessorCommitGrowth:
    """Tests for DevProcessor.commit_growth() method."""

    def test_commit_growth_positive(self) -> None:
        """commit_growth() returns positive percentage when commits increased."""
        result = DevProcessor.commit_growth(current_commits=120, previous_commits=100)
        assert result == 20.0

    def test_commit_growth_negative(self) -> None:
        """commit_growth() returns negative percentage when commits decreased."""
        result = DevProcessor.commit_growth(current_commits=80, previous_commits=100)
        assert result == -20.0

    def test_commit_growth_zero_previous(self) -> None:
        """commit_growth() returns 0.0 when previous commits is zero."""
        result = DevProcessor.commit_growth(current_commits=50, previous_commits=0)
        assert result == 0.0

    def test_commit_growth_no_change(self) -> None:
        """commit_growth() returns 0.0 when commits are the same."""
        result = DevProcessor.commit_growth(current_commits=100, previous_commits=100)
        assert result == 0.0


class TestDevProcessorContributorGrowth:
    """Tests for DevProcessor.contributor_growth() method."""

    def test_contributor_growth_positive(self) -> None:
        """contributor_growth() returns positive percentage when contributors increased."""
        result = DevProcessor.contributor_growth(current_contributors=50, previous_contributors=40)
        assert result == 25.0

    def test_contributor_growth_negative(self) -> None:
        """contributor_growth() returns negative percentage when contributors decreased."""
        result = DevProcessor.contributor_growth(current_contributors=30, previous_contributors=40)
        assert result == -25.0

    def test_contributor_growth_zero_previous(self) -> None:
        """contributor_growth() returns 0.0 when previous contributors is zero."""
        result = DevProcessor.contributor_growth(current_contributors=10, previous_contributors=0)
        assert result == 0.0


class TestDevProcessorActivityScore:
    """Tests for DevProcessor.activity_score() method."""

    def test_activity_score_range(self) -> None:
        """activity_score() returns a value between 0.0 and 1.0."""
        result = DevProcessor.activity_score(
            commits_30d=100, contributors=20, stars=5000, forks=500
        )
        assert 0.0 <= result <= 1.0

    def test_activity_score_high_activity(self) -> None:
        """activity_score() returns high score for very active projects."""
        result = DevProcessor.activity_score(
            commits_30d=500, contributors=100, stars=50000, forks=10000
        )
        assert result >= 0.7

    def test_activity_score_low_activity(self) -> None:
        """activity_score() returns low score for inactive projects."""
        result = DevProcessor.activity_score(commits_30d=1, contributors=1, stars=10, forks=1)
        assert result <= 0.3

    def test_activity_score_zero_input(self) -> None:
        """activity_score() returns 0.0 for completely inactive projects."""
        result = DevProcessor.activity_score(commits_30d=0, contributors=0, stars=0, forks=0)
        assert result == 0.0


class TestDevProcessorProcess:
    """Tests for DevProcessor.process() method."""

    def test_process_returns_all_fields(self) -> None:
        """process() returns dict with all computed dev metrics."""
        raw = {
            "repo": "solana-labs/solana",
            "commits_30d": 200,
            "contributors": 50,
            "stars": 12000,
            "forks": 3500,
            "open_issues": 500,
        }
        previous = {
            "commits_30d": 180,
            "contributors": 45,
        }
        result = DevProcessor.process(raw, previous)

        assert "commit_growth_pct" in result
        assert "contributor_growth_pct" in result
        assert "dev_activity_score" in result
        # Original fields preserved
        assert result["repo"] == "solana-labs/solana"
        assert result["stars"] == 12000

    def test_process_without_previous(self) -> None:
        """process() handles missing previous data gracefully."""
        raw = {
            "commits_30d": 100,
            "contributors": 20,
            "stars": 5000,
            "forks": 500,
        }
        result = DevProcessor.process(raw, previous=None)

        assert result["commit_growth_pct"] == 0.0
        assert result["contributor_growth_pct"] == 0.0
        assert "dev_activity_score" in result

    def test_process_calculates_correct_growth(self) -> None:
        """process() calculates growth percentages correctly."""
        raw = {"commits_30d": 120, "contributors": 25, "stars": 1000, "forks": 100}
        previous = {"commits_30d": 100, "contributors": 20}
        result = DevProcessor.process(raw, previous)

        assert result["commit_growth_pct"] == 20.0
        assert result["contributor_growth_pct"] == 25.0
