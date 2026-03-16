"""TDD tests for CLI database management commands.

Commands tested:
- ``cryptoai db-status`` — show row counts per table.
- ``cryptoai db-clean --confirm`` — truncate all data tables.
- ``cryptoai db-truncate <table> --confirm`` — truncate a single table.
- ``cryptoai seed [rankings|narratives|all]`` — run seed scripts selectively.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from app.cli import cli

# ---------------------------------------------------------------------------
# Allowed tables constant — mirrors the production constant in cli.py
# ---------------------------------------------------------------------------

ALLOWED_TABLES = [
    "tokens",
    "token_scores",
    "market_data",
    "narratives",
    "alerts",
    "social_data",
    "dev_activity",
    "signals",
    "ai_analyses",
    "historical_candles",
    "historical_snapshots",
]


# ---------------------------------------------------------------------------
# cryptoai db-status
# ---------------------------------------------------------------------------


class TestCliDbStatus:
    """Tests for ``cryptoai db-status``."""

    def test_db_status_exits_zero(self) -> None:
        """db-status must exit 0 on success."""
        counts = {t: 0 for t in ALLOWED_TABLES}
        with patch("app.cli.fetch_table_counts", new_callable=AsyncMock, return_value=counts):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-status"])
        assert result.exit_code == 0

    def test_db_status_prints_table_names(self) -> None:
        """db-status must print each table name."""
        counts = {t: 0 for t in ALLOWED_TABLES}
        with patch("app.cli.fetch_table_counts", new_callable=AsyncMock, return_value=counts):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-status"])
        for table in ALLOWED_TABLES:
            assert table in result.output

    def test_db_status_prints_row_counts(self) -> None:
        """db-status must print the row count for each table."""
        counts = {"tokens": 42, "token_scores": 100}
        with patch("app.cli.fetch_table_counts", new_callable=AsyncMock, return_value=counts):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-status"])
        assert "42" in result.output
        assert "100" in result.output

    def test_db_status_prints_error_on_failure(self) -> None:
        """db-status must print an error and exit non-zero when DB is unreachable."""
        with patch(
            "app.cli.fetch_table_counts",
            new_callable=AsyncMock,
            side_effect=Exception("connection refused"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-status"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cryptoai db-clean
# ---------------------------------------------------------------------------


class TestCliDbClean:
    """Tests for ``cryptoai db-clean --confirm``."""

    def test_db_clean_requires_confirm_flag(self) -> None:
        """db-clean without --confirm must abort without truncating."""
        with patch("app.cli.truncate_all_tables", new_callable=AsyncMock) as mock_trunc:
            runner = CliRunner()
            result = runner.invoke(cli, ["db-clean"])
        mock_trunc.assert_not_awaited()
        assert "confirm" in result.output.lower() or result.exit_code != 0

    def test_db_clean_with_confirm_exits_zero(self) -> None:
        """db-clean --confirm must exit 0 on success."""
        with patch("app.cli.truncate_all_tables", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-clean", "--confirm"])
        assert result.exit_code == 0

    def test_db_clean_with_confirm_calls_truncate(self) -> None:
        """db-clean --confirm must call truncate_all_tables."""
        with patch("app.cli.truncate_all_tables", new_callable=AsyncMock) as mock_trunc:
            runner = CliRunner()
            runner.invoke(cli, ["db-clean", "--confirm"])
        mock_trunc.assert_awaited_once()

    def test_db_clean_prints_success_message(self) -> None:
        """db-clean --confirm must print a success message."""
        with patch("app.cli.truncate_all_tables", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-clean", "--confirm"])
        assert "truncated" in result.output.lower() or "clean" in result.output.lower()

    def test_db_clean_prints_error_on_failure(self) -> None:
        """db-clean --confirm must print an error on failure."""
        with patch(
            "app.cli.truncate_all_tables",
            new_callable=AsyncMock,
            side_effect=Exception("DB error"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-clean", "--confirm"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cryptoai db-truncate <table>
# ---------------------------------------------------------------------------


class TestCliDbTruncate:
    """Tests for ``cryptoai db-truncate <table> --confirm``."""

    def test_db_truncate_requires_confirm_flag(self) -> None:
        """db-truncate without --confirm must abort."""
        with patch("app.cli.truncate_table", new_callable=AsyncMock) as mock_trunc:
            runner = CliRunner()
            result = runner.invoke(cli, ["db-truncate", "tokens"])
        mock_trunc.assert_not_awaited()
        assert "confirm" in result.output.lower() or result.exit_code != 0

    def test_db_truncate_with_confirm_exits_zero(self) -> None:
        """db-truncate tokens --confirm must exit 0."""
        with patch("app.cli.truncate_table", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-truncate", "tokens", "--confirm"])
        assert result.exit_code == 0

    def test_db_truncate_calls_truncate_table_with_name(self) -> None:
        """db-truncate must pass the table name to truncate_table."""
        with patch("app.cli.truncate_table", new_callable=AsyncMock) as mock_trunc:
            runner = CliRunner()
            runner.invoke(cli, ["db-truncate", "market_data", "--confirm"])
        mock_trunc.assert_awaited_once_with("market_data")

    def test_db_truncate_rejects_invalid_table(self) -> None:
        """db-truncate must reject table names not in the allowed list."""
        with patch("app.cli.truncate_table", new_callable=AsyncMock) as mock_trunc:
            runner = CliRunner()
            result = runner.invoke(cli, ["db-truncate", "users", "--confirm"])
        mock_trunc.assert_not_awaited()
        assert result.exit_code != 0

    def test_db_truncate_prints_success_message(self) -> None:
        """db-truncate must print a success message with the table name."""
        with patch("app.cli.truncate_table", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-truncate", "tokens", "--confirm"])
        assert "tokens" in result.output.lower()

    def test_db_truncate_prints_error_on_failure(self) -> None:
        """db-truncate must print error on failure."""
        with patch(
            "app.cli.truncate_table",
            new_callable=AsyncMock,
            side_effect=Exception("DB error"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["db-truncate", "tokens", "--confirm"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cryptoai seed
# ---------------------------------------------------------------------------


class TestCliSeed:
    """Tests for ``cryptoai seed [rankings|narratives|all]``."""

    def test_seed_all_exits_zero(self) -> None:
        """cryptoai seed all must exit 0 on success."""
        with patch("app.cli.run_seed", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["seed", "all"])
        assert result.exit_code == 0

    def test_seed_rankings_calls_run_seed_with_rankings(self) -> None:
        """cryptoai seed rankings must call run_seed('rankings')."""
        with patch("app.cli.run_seed", new_callable=AsyncMock) as mock_seed:
            runner = CliRunner()
            runner.invoke(cli, ["seed", "rankings"])
        mock_seed.assert_awaited_once_with("rankings")

    def test_seed_narratives_calls_run_seed_with_narratives(self) -> None:
        """cryptoai seed narratives must call run_seed('narratives')."""
        with patch("app.cli.run_seed", new_callable=AsyncMock) as mock_seed:
            runner = CliRunner()
            runner.invoke(cli, ["seed", "narratives"])
        mock_seed.assert_awaited_once_with("narratives")

    def test_seed_all_calls_run_seed_with_all(self) -> None:
        """cryptoai seed all must call run_seed('all')."""
        with patch("app.cli.run_seed", new_callable=AsyncMock) as mock_seed:
            runner = CliRunner()
            runner.invoke(cli, ["seed", "all"])
        mock_seed.assert_awaited_once_with("all")

    def test_seed_invalid_target_fails(self) -> None:
        """cryptoai seed invalid must exit non-zero."""
        with patch("app.cli.run_seed", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["seed", "invalid"])
        assert result.exit_code != 0

    def test_seed_prints_success(self) -> None:
        """cryptoai seed all must print a success message."""
        with patch("app.cli.run_seed", new_callable=AsyncMock):
            runner = CliRunner()
            result = runner.invoke(cli, ["seed", "all"])
        assert "seed" in result.output.lower()

    def test_seed_prints_error_on_failure(self) -> None:
        """cryptoai seed must print error on failure."""
        with patch(
            "app.cli.run_seed",
            new_callable=AsyncMock,
            side_effect=Exception("seed failed"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["seed", "all"])
        assert result.exit_code != 0
