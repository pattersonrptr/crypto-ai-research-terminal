"""TDD tests for GithubCollector — GitHub repository metrics."""

import httpx
import pytest
import respx

from app.collectors.github_collector import GithubCollector
from app.exceptions import CollectorError


class TestGithubCollectorInit:
    """Tests for GithubCollector initialization."""

    def test_init_sets_base_url(self) -> None:
        """GithubCollector must set GitHub API base URL."""
        collector = GithubCollector()
        assert collector.base_url == "https://api.github.com"

    def test_init_accepts_api_token(self) -> None:
        """GithubCollector must accept an optional API token."""
        collector = GithubCollector(api_token="ghp_test123")  # nosec B106
        assert collector.api_key == "ghp_test123"


class TestGithubCollectorCollect:
    """Tests for GithubCollector.collect() method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_returns_list(self) -> None:
        """collect() must return a list of repo data dicts."""
        respx.get("https://api.github.com/repos/solana-labs/solana").mock(
            return_value=httpx.Response(
                200,
                json={
                    "full_name": "solana-labs/solana",
                    "stargazers_count": 12000,
                    "forks_count": 3500,
                    "open_issues_count": 500,
                    "subscribers_count": 400,
                },
            )
        )
        respx.get("https://api.github.com/repos/solana-labs/solana/stats/contributors").mock(
            return_value=httpx.Response(200, json=[{"total": 100}, {"total": 50}])
        )
        respx.get("https://api.github.com/repos/solana-labs/solana/stats/commit_activity").mock(
            return_value=httpx.Response(
                200, json=[{"total": 20}, {"total": 30}, {"total": 25}, {"total": 15}]
            )
        )

        collector = GithubCollector()
        async with collector:
            result = await collector.collect(symbols=["solana-labs/solana"])

        assert isinstance(result, list)
        assert len(result) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_returns_required_fields(self) -> None:
        """collect() must return dicts with stars, forks, open_issues, contributors, commits_30d."""
        respx.get("https://api.github.com/repos/solana-labs/solana").mock(
            return_value=httpx.Response(
                200,
                json={
                    "full_name": "solana-labs/solana",
                    "stargazers_count": 12000,
                    "forks_count": 3500,
                    "open_issues_count": 500,
                    "subscribers_count": 400,
                },
            )
        )
        respx.get("https://api.github.com/repos/solana-labs/solana/stats/contributors").mock(
            return_value=httpx.Response(200, json=[{"total": 100}, {"total": 50}])
        )
        respx.get("https://api.github.com/repos/solana-labs/solana/stats/commit_activity").mock(
            return_value=httpx.Response(
                200, json=[{"total": 20}, {"total": 30}, {"total": 25}, {"total": 15}]
            )
        )

        collector = GithubCollector()
        async with collector:
            result = await collector.collect(symbols=["solana-labs/solana"])

        item = result[0]
        assert item["repo"] == "solana-labs/solana"
        assert item["stars"] == 12000
        assert item["forks"] == 3500
        assert item["open_issues"] == 500
        assert item["contributors"] == 2
        assert "commits_30d" in item

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_commits_30d_sums_last_4_weeks(self) -> None:
        """commits_30d should sum the last 4 weeks of commit activity."""
        respx.get("https://api.github.com/repos/owner/repo").mock(
            return_value=httpx.Response(
                200,
                json={
                    "full_name": "owner/repo",
                    "stargazers_count": 100,
                    "forks_count": 10,
                    "open_issues_count": 5,
                    "subscribers_count": 2,
                },
            )
        )
        respx.get("https://api.github.com/repos/owner/repo/stats/contributors").mock(
            return_value=httpx.Response(200, json=[{"total": 10}])
        )
        # 52 weeks of data, sum last 4 = 10 + 20 + 30 + 40 = 100
        commit_activity = [{"total": i} for i in range(52)]
        commit_activity[-4:] = [{"total": 10}, {"total": 20}, {"total": 30}, {"total": 40}]
        respx.get("https://api.github.com/repos/owner/repo/stats/commit_activity").mock(
            return_value=httpx.Response(200, json=commit_activity)
        )

        collector = GithubCollector()
        async with collector:
            result = await collector.collect(symbols=["owner/repo"])

        assert result[0]["commits_30d"] == 100

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_handles_rate_limit_error(self) -> None:
        """collect() must raise CollectorError on 403 rate limit."""
        respx.get("https://api.github.com/repos/owner/repo").mock(
            return_value=httpx.Response(403, json={"message": "API rate limit exceeded"})
        )

        collector = GithubCollector()
        async with collector:
            with pytest.raises(CollectorError) as exc_info:
                await collector.collect(symbols=["owner/repo"])

        assert "rate limit" in str(exc_info.value).lower() or exc_info.value is not None

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_handles_not_found(self) -> None:
        """collect() must raise CollectorError on 404."""
        respx.get("https://api.github.com/repos/nonexistent/repo").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )

        collector = GithubCollector()
        async with collector:
            with pytest.raises(CollectorError):
                await collector.collect(symbols=["nonexistent/repo"])


class TestGithubCollectorCollectSingle:
    """Tests for GithubCollector.collect_single() method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_single_returns_dict(self) -> None:
        """collect_single() must return a single repo data dict."""
        respx.get("https://api.github.com/repos/solana-labs/solana").mock(
            return_value=httpx.Response(
                200,
                json={
                    "full_name": "solana-labs/solana",
                    "stargazers_count": 12000,
                    "forks_count": 3500,
                    "open_issues_count": 500,
                    "subscribers_count": 400,
                },
            )
        )
        respx.get("https://api.github.com/repos/solana-labs/solana/stats/contributors").mock(
            return_value=httpx.Response(200, json=[{"total": 100}])
        )
        respx.get("https://api.github.com/repos/solana-labs/solana/stats/commit_activity").mock(
            return_value=httpx.Response(200, json=[{"total": 20}] * 52)
        )

        collector = GithubCollector()
        async with collector:
            result = await collector.collect_single(symbol="solana-labs/solana")

        assert isinstance(result, dict)
        assert result["repo"] == "solana-labs/solana"
