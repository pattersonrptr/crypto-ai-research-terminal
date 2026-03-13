"""GitHub repository metrics collector."""

from typing import Any

import httpx
import structlog

from app.collectors.base_collector import BaseCollector
from app.exceptions import CollectorError

logger = structlog.get_logger(__name__)


class GithubCollector(BaseCollector):
    """Collector for GitHub repository metrics.

    Fetches stars, forks, open issues, contributor count, and
    commit activity (last 30 days) from the GitHub REST API.
    """

    def __init__(self, api_token: str = "") -> None:  # nosec B107
        """Initialize the GitHub collector.

        Args:
            api_token: Optional GitHub personal access token for higher rate limits.
        """
        super().__init__(base_url="https://api.github.com", api_key=api_token)

    async def __aenter__(self) -> "GithubCollector":
        """Create HTTP client with auth headers if token provided."""
        headers: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        if self.api_key:
            headers["Authorization"] = f"token {self.api_key}"
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0, headers=headers)
        return self

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Collect metrics for a list of GitHub repositories.

        Args:
            symbols: List of repo identifiers in "owner/repo" format.

        Returns:
            List of dicts with keys: repo, stars, forks, open_issues,
            contributors, commits_30d.

        Raises:
            CollectorError: On rate limit (403) or not found (404).
        """
        results: list[dict[str, Any]] = []
        for repo in symbols:
            data = await self._fetch_repo_data(repo)
            results.append(data)
        return results

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Collect metrics for a single GitHub repository.

        Args:
            symbol: Repository identifier in "owner/repo" format.

        Returns:
            Dict with keys: repo, stars, forks, open_issues,
            contributors, commits_30d.
        """
        result = await self.collect(symbols=[symbol])
        return result[0]

    async def _fetch_repo_data(self, repo: str) -> dict[str, Any]:
        """Fetch all metrics for a single repository.

        Args:
            repo: Repository identifier in "owner/repo" format.

        Returns:
            Dict with repo metrics.

        Raises:
            CollectorError: On HTTP errors.
        """
        log = logger.bind(repo=repo)
        log.debug("github.fetch_repo_start")

        try:
            # Fetch basic repo info
            repo_info = await self._get(f"/repos/{repo}")

            # Fetch contributors (returns list of contributor objects)
            contributors_data = await self._get(f"/repos/{repo}/stats/contributors")
            contributors_count = (
                len(contributors_data) if isinstance(contributors_data, list) else 0
            )

            # Fetch commit activity (52 weeks of data)
            commit_activity = await self._get(f"/repos/{repo}/stats/commit_activity")
            commits_30d = self._sum_last_4_weeks(commit_activity)

            result = {
                "repo": repo_info["full_name"],
                "stars": repo_info["stargazers_count"],
                "forks": repo_info["forks_count"],
                "open_issues": repo_info["open_issues_count"],
                "contributors": contributors_count,
                "commits_30d": commits_30d,
            }

            log.debug("github.fetch_repo_complete", **result)
            return result

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 403:
                log.warning("github.rate_limit", status=status)
                raise CollectorError(f"GitHub rate limit exceeded for {repo}") from e
            if status == 404:
                log.warning("github.not_found", repo=repo)
                raise CollectorError(f"GitHub repository not found: {repo}") from e
            log.error("github.http_error", status=status)
            raise CollectorError(f"GitHub API error {status} for {repo}") from e

    def _sum_last_4_weeks(self, commit_activity: list[dict[str, Any]]) -> int:
        """Sum commit totals from the last 4 weeks.

        Args:
            commit_activity: List of weekly commit data from GitHub API.

        Returns:
            Total commits in the last 4 weeks (~30 days).
        """
        if not commit_activity or not isinstance(commit_activity, list):
            return 0
        last_4 = commit_activity[-4:] if len(commit_activity) >= 4 else commit_activity
        return sum(week.get("total", 0) for week in last_4)
