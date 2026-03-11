"""CLI entry point — `cryptoai` command group."""

from __future__ import annotations

from typing import Any

import click
import httpx

_BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Internal helpers — thin HTTP wrappers (patchable in tests)
# ---------------------------------------------------------------------------


def fetch_opportunities(n: int = 10) -> list[Any]:
    """Fetch the top-n opportunity rankings from the API."""
    response = httpx.get(f"{_BASE_URL}/rankings/opportunities", params={"limit": n})
    response.raise_for_status()
    data = response.json()

    results: list[Any] = []
    for item in data:
        obj = _DictObj(item)
        results.append(obj)
    return results


def fetch_token_detail(symbol: str) -> Any | None:
    """Fetch a single token detail from the API; return None if not found."""
    response = httpx.get(f"{_BASE_URL}/tokens/{symbol.upper()}")
    if response.status_code == 404:
        return None
    response.raise_for_status()

    token_data = response.json()

    # Fetch latest score to enrich the detail object
    scores_response = httpx.get(f"{_BASE_URL}/rankings/opportunities", params={"limit": 500})
    scores_response.raise_for_status()
    scores: list[dict[str, Any]] = scores_response.json()
    score_map = {s["symbol"]: s for s in scores}

    merged = {**token_data, **score_map.get(symbol.upper(), {})}
    return _DictObj(merged)


class _DictObj:
    """Wrap a dict as an attribute-accessible object for uniform access."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """Crypto AI Research Terminal — command-line interface."""


# ---------------------------------------------------------------------------
# cryptoai top [--n N]
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--n", default=10, show_default=True, help="Number of top tokens to display.")
def top(n: int) -> None:
    """Display the top-N tokens ranked by opportunity score."""
    items = fetch_opportunities(n=n)
    if not items:
        click.echo("No data available.")
        return

    click.echo(f"\n{'#':<4} {'Symbol':<10} {'Name':<25} {'Opp. Score':>10} {'Fund. Score':>12}")
    click.echo("-" * 65)
    for rank, item in enumerate(items, start=1):
        click.echo(
            f"{rank:<4} {item.symbol:<10} {item.name:<25} "
            f"{item.opportunity_score:>10.2f} {item.fundamental_score:>12.2f}"
        )
    click.echo()


# ---------------------------------------------------------------------------
# cryptoai report <SYMBOL>
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("symbol")
def report(symbol: str) -> None:
    """Display a detailed report for a single token."""
    detail = fetch_token_detail(symbol)
    if detail is None:
        click.echo(f"Token '{symbol.upper()}' not found.", err=True)
        raise SystemExit(1)

    click.echo(f"\n{'=' * 50}")
    click.echo(f"  Token Report: {detail.symbol} — {detail.name}")
    click.echo(f"{'=' * 50}")
    click.echo(f"  CoinGecko ID    : {detail.coingecko_id}")
    click.echo(f"  Fundamental     : {detail.fundamental_score:.2f}")
    click.echo(f"  Opportunity     : {detail.opportunity_score:.2f}")
    click.echo(f"{'=' * 50}\n")
