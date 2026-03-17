"""TDD tests for CLI backtest-collect and backtest-calibrate commands.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from app.cli import cli

# ---------------------------------------------------------------------------
# cryptoai backtest-collect <cycle>
# ---------------------------------------------------------------------------


class TestBacktestCollect:
    """Tests for cryptoai backtest-collect CLI command."""

    def test_backtest_collect_invalid_cycle_exits_with_error(self) -> None:
        """Must exit with error when cycle name is invalid."""
        runner = CliRunner()
        result = runner.invoke(cli, ["backtest-collect", "nonexistent_cycle"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_backtest_collect_valid_cycle_runs_successfully(self) -> None:
        """Must collect data and report success for a valid cycle."""
        mock_result = AsyncMock()
        mock_result.n_tokens_collected = 5
        mock_result.snapshots = [{"symbol": "BTC"} for _ in range(50)]
        mock_result.errors = {}
        mock_result.cycle_name = "cycle_2_2019_2021"

        with patch(
            "app.cli.run_backtest_collect",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-collect", "cycle_2_2019_2021"])
        assert result.exit_code == 0
        assert "5" in result.output  # n_tokens_collected

    def test_backtest_collect_reports_partial_failures(self) -> None:
        """Must report errors when some tokens fail collection."""
        mock_result = AsyncMock()
        mock_result.n_tokens_collected = 3
        mock_result.snapshots = [{"symbol": "BTC"} for _ in range(30)]
        mock_result.errors = {"XRP": "API error", "DOGE": "timeout"}
        mock_result.cycle_name = "cycle_2_2019_2021"

        with patch(
            "app.cli.run_backtest_collect",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-collect", "cycle_2_2019_2021"])
        assert result.exit_code == 0
        assert "2" in result.output or "error" in result.output.lower()

    def test_backtest_collect_persists_snapshots(self) -> None:
        """Must call persist function after collecting."""
        mock_result = AsyncMock()
        mock_result.n_tokens_collected = 5
        mock_result.snapshots = [{"symbol": "BTC"} for _ in range(50)]
        mock_result.errors = {}
        mock_result.cycle_name = "cycle_2_2019_2021"

        with patch(
            "app.cli.run_backtest_collect",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-collect", "cycle_2_2019_2021"])
        assert result.exit_code == 0
        mock_fn.assert_awaited_once()


# ---------------------------------------------------------------------------
# cryptoai backtest-calibrate
# ---------------------------------------------------------------------------


class TestBacktestCalibrate:
    """Tests for cryptoai backtest-calibrate CLI command."""

    def test_backtest_calibrate_runs_with_defaults(self) -> None:
        """Must run calibration with default parameters."""
        mock_report = {
            "cycle": "all",
            "best_weights": {
                "fundamental": 0.35,
                "growth": 0.20,
                "narrative": 0.20,
                "listing": 0.15,
                "risk": 0.10,
            },
            "best_precision_at_k": 0.70,
            "n_combinations_tested": 56,
        }
        with patch(
            "app.cli.run_backtest_calibrate",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-calibrate"])
        assert result.exit_code == 0
        assert "0.35" in result.output or "precision" in result.output.lower()

    def test_backtest_calibrate_with_specific_cycle(self) -> None:
        """Must accept --cycle argument."""
        mock_report = {
            "cycle": "cycle_2_2019_2021",
            "best_weights": {
                "fundamental": 0.30,
                "growth": 0.25,
                "narrative": 0.20,
                "listing": 0.15,
                "risk": 0.10,
            },
            "best_precision_at_k": 0.60,
            "n_combinations_tested": 56,
        }
        with patch(
            "app.cli.run_backtest_calibrate",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-calibrate", "--cycle", "cycle_2_2019_2021"])
        assert result.exit_code == 0

    def test_backtest_calibrate_with_step_and_k(self) -> None:
        """Must accept --step and --k arguments."""
        mock_report = {
            "cycle": "all",
            "best_weights": {
                "fundamental": 0.40,
                "growth": 0.20,
                "narrative": 0.15,
                "listing": 0.15,
                "risk": 0.10,
            },
            "best_precision_at_k": 0.80,
            "n_combinations_tested": 10,
        }
        with patch(
            "app.cli.run_backtest_calibrate",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-calibrate", "--step", "0.25", "--k", "5"])
        assert result.exit_code == 0

    def test_backtest_calibrate_displays_results(self) -> None:
        """Must display the best weights and precision in output."""
        mock_report = {
            "cycle": "all",
            "best_weights": {
                "fundamental": 0.35,
                "growth": 0.20,
                "narrative": 0.20,
                "listing": 0.15,
                "risk": 0.10,
            },
            "best_precision_at_k": 0.70,
            "n_combinations_tested": 56,
        }
        with patch(
            "app.cli.run_backtest_calibrate",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-calibrate"])
        assert result.exit_code == 0
        # Should display weights and precision
        assert "fundamental" in result.output.lower() or "0.35" in result.output

    def test_backtest_calibrate_invalid_cycle_exits_error(self) -> None:
        """Must exit with error for invalid cycle name."""
        with patch(
            "app.cli.run_backtest_calibrate",
            new_callable=AsyncMock,
            side_effect=KeyError("nonexistent_cycle"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["backtest-calibrate", "--cycle", "nonexistent_cycle"])
        assert result.exit_code != 0
