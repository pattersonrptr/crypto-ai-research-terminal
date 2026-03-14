"""TDD tests for the CLI — `cryptoai top`, `cryptoai report`, `cryptoai collect-now`."""

from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from app.cli import cli

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_opportunity_item(
    symbol: str,
    name: str,
    opportunity_score: float,
    fundamental_score: float,
) -> MagicMock:
    """Return a mock OpportunityRankItem-like object."""
    item = MagicMock()
    item.symbol = symbol
    item.name = name
    item.opportunity_score = opportunity_score
    item.fundamental_score = fundamental_score
    return item


def _make_token_detail(
    symbol: str,
    name: str,
    coingecko_id: str,
    opportunity_score: float,
    fundamental_score: float,
) -> MagicMock:
    """Return a mock token detail object."""
    obj = MagicMock()
    obj.symbol = symbol
    obj.name = name
    obj.coingecko_id = coingecko_id
    obj.opportunity_score = opportunity_score
    obj.fundamental_score = fundamental_score
    return obj


# ---------------------------------------------------------------------------
# cryptoai top
# ---------------------------------------------------------------------------


class TestCliTop:
    """Tests for `cryptoai top` command."""

    def test_top_exits_with_zero(self) -> None:
        """cryptoai top must exit with code 0."""
        items = [_make_opportunity_item("BTC", "Bitcoin", 0.9, 0.85)]
        with patch("app.cli.fetch_opportunities", return_value=items):
            runner = CliRunner()
            result = runner.invoke(cli, ["top"])
        assert result.exit_code == 0

    def test_top_prints_symbol_in_output(self) -> None:
        """cryptoai top must print the token symbol."""
        items = [_make_opportunity_item("BTC", "Bitcoin", 0.9, 0.85)]
        with patch("app.cli.fetch_opportunities", return_value=items):
            runner = CliRunner()
            result = runner.invoke(cli, ["top"])
        assert "BTC" in result.output

    def test_top_prints_opportunity_score(self) -> None:
        """cryptoai top must print the opportunity score."""
        items = [_make_opportunity_item("BTC", "Bitcoin", 0.9, 0.85)]
        with patch("app.cli.fetch_opportunities", return_value=items):
            runner = CliRunner()
            result = runner.invoke(cli, ["top"])
        assert "0.90" in result.output or "0.9" in result.output

    def test_top_n_flag_limits_results(self) -> None:
        """cryptoai top --n 1 must print at most 1 token."""
        items = [
            _make_opportunity_item("BTC", "Bitcoin", 0.9, 0.85),
            _make_opportunity_item("ETH", "Ethereum", 0.7, 0.65),
        ]
        with patch("app.cli.fetch_opportunities", return_value=items[:1]):
            runner = CliRunner()
            result = runner.invoke(cli, ["top", "--n", "1"])
        assert "ETH" not in result.output

    def test_top_default_n_is_10(self) -> None:
        """cryptoai top without --n flag calls fetch_opportunities with n=10."""
        items = [_make_opportunity_item("BTC", "Bitcoin", 0.9, 0.85)]
        with patch("app.cli.fetch_opportunities", return_value=items) as mock_fetch:
            runner = CliRunner()
            runner.invoke(cli, ["top"])
        mock_fetch.assert_called_once_with(n=10)


# ---------------------------------------------------------------------------
# cryptoai report
# ---------------------------------------------------------------------------


class TestCliReport:
    """Tests for `cryptoai report <SYMBOL>` command."""

    def test_report_exits_with_zero(self) -> None:
        """cryptoai report BTC must exit with code 0 when token exists."""
        detail = _make_token_detail("BTC", "Bitcoin", "bitcoin", 0.9, 0.85)
        with patch("app.cli.fetch_token_detail", return_value=detail):
            runner = CliRunner()
            result = runner.invoke(cli, ["report", "BTC"])
        assert result.exit_code == 0

    def test_report_prints_symbol(self) -> None:
        """cryptoai report must print the token symbol."""
        detail = _make_token_detail("BTC", "Bitcoin", "bitcoin", 0.9, 0.85)
        with patch("app.cli.fetch_token_detail", return_value=detail):
            runner = CliRunner()
            result = runner.invoke(cli, ["report", "BTC"])
        assert "BTC" in result.output

    def test_report_prints_scores(self) -> None:
        """cryptoai report must print both fundamental and opportunity scores."""
        detail = _make_token_detail("BTC", "Bitcoin", "bitcoin", 0.9, 0.85)
        with patch("app.cli.fetch_token_detail", return_value=detail):
            runner = CliRunner()
            result = runner.invoke(cli, ["report", "BTC"])
        assert "0.9" in result.output
        assert "0.85" in result.output

    def test_report_not_found_prints_error(self) -> None:
        """cryptoai report must print an error message when token is not found."""
        with patch("app.cli.fetch_token_detail", return_value=None):
            runner = CliRunner()
            result = runner.invoke(cli, ["report", "UNKNOWN"])
        assert "not found" in result.output.lower() or result.exit_code != 0


# ---------------------------------------------------------------------------
# cryptoai collect-now
# ---------------------------------------------------------------------------


class TestCliCollectNow:
    """Tests for `cryptoai collect-now` command."""

    def test_collect_now_exits_with_zero(self) -> None:
        """cryptoai collect-now must exit 0 on success."""
        with patch("app.cli.run_collection_job", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = 5
            runner = CliRunner()
            result = runner.invoke(cli, ["collect-now"])
        assert result.exit_code == 0

    def test_collect_now_calls_run_collection_job(self) -> None:
        """cryptoai collect-now must call run_collection_job()."""
        with patch("app.cli.run_collection_job", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = 3
            runner = CliRunner()
            runner.invoke(cli, ["collect-now"])
        mock_run.assert_awaited_once()

    def test_collect_now_prints_token_count(self) -> None:
        """cryptoai collect-now must print how many tokens were collected."""
        with patch("app.cli.run_collection_job", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = 42
            runner = CliRunner()
            result = runner.invoke(cli, ["collect-now"])
        assert "42" in result.output

    def test_collect_now_prints_error_on_failure(self) -> None:
        """cryptoai collect-now must print error and exit 1 when pipeline fails."""
        with patch(
            "app.cli.run_collection_job",
            new_callable=AsyncMock,
            side_effect=Exception("CoinGecko down"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["collect-now"])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "coingecko" in result.output.lower()
