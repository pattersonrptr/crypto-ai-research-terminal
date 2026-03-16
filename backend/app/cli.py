"""CLI entry point — `cryptoai` command group."""

from __future__ import annotations

import asyncio
from typing import Any

import click
import httpx
import structlog

_BASE_URL = "http://localhost:8000"
logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Allowed tables for db-clean / db-truncate
# ---------------------------------------------------------------------------

ALLOWED_TABLES: list[str] = [
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

# Valid seed targets
_SEED_TARGETS = {"rankings", "narratives", "all"}


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


# ---------------------------------------------------------------------------
# cryptoai collect-now  — trigger the collection pipeline immediately
# ---------------------------------------------------------------------------


async def run_collection_job() -> int:
    """Run the full collection → score → persist pipeline once.

    Returns:
        Number of tokens successfully processed and persisted.
    """
    from app.collectors.coingecko_collector import CoinGeckoCollector  # noqa: PLC0415
    from app.config import Settings  # noqa: PLC0415
    from app.processors.market_processor import MarketProcessor  # noqa: PLC0415
    from app.scheduler.jobs import (  # noqa: PLC0415
        _NARRATIVE_CATEGORY_LIMIT,
        _persist_results,
        build_narrative_snapshot_from_categories,
        evaluate_and_persist_alerts,
        persist_narrative_snapshot,
    )
    from app.scoring.fundamental_scorer import FundamentalScorer  # noqa: PLC0415
    from app.scoring.heuristic_sub_scorer import HeuristicSubScorer  # noqa: PLC0415
    from app.scoring.opportunity_engine import OpportunityEngine  # noqa: PLC0415

    settings = Settings()
    api_key = settings.coingecko_api_key

    async with CoinGeckoCollector(api_key=api_key) as collector:
        raw_data = await collector.collect(symbols=[])

    results: list[dict[str, object]] = []
    for raw in raw_data:
        try:
            processed = MarketProcessor.process(raw)
            fundamental = FundamentalScorer.score(processed)
            sub_scores = HeuristicSubScorer.score(processed)
            opportunity = OpportunityEngine.full_composite_score(
                fundamental=fundamental,
                growth=sub_scores.growth_score,
                narrative=sub_scores.narrative_score,
                listing=sub_scores.listing_probability,
                risk=sub_scores.risk_score,
                cycle_leader_prob=sub_scores.cycle_leader_prob,
            )
            results.append(
                {
                    **processed,
                    "fundamental_score": fundamental,
                    "opportunity_score": opportunity,
                    **sub_scores.to_dict(),
                }
            )
        except Exception:
            logger.exception("collect_now.token_error", symbol=raw.get("symbol"))

    await _persist_results(results)

    # Build narratives from token categories
    try:
        top_ids = [r.get("coingecko_id", "") for r in raw_data if r.get("coingecko_id")]
        top_ids = top_ids[:_NARRATIVE_CATEGORY_LIMIT]
        categories_map: dict[str, list[str]] = {}
        if top_ids:
            async with CoinGeckoCollector(api_key=api_key) as cat_collector:
                categories_map = await cat_collector.collect_categories(top_ids)
        narrative_data = [
            {
                "symbol": r.get("symbol", "").upper(),
                "name": r.get("name", ""),
                "categories": categories_map.get(r.get("coingecko_id", ""), []),
            }
            for r in raw_data
            if r.get("coingecko_id", "") in categories_map
        ]
        clusters = build_narrative_snapshot_from_categories(narrative_data)
        await persist_narrative_snapshot(clusters)
        logger.info("collect_now.narratives_persisted", count=len(clusters))
    except Exception:
        logger.exception("collect_now.narrative_error")

    # Evaluate and persist alerts
    try:
        triggered = await evaluate_and_persist_alerts(results)
        logger.info("collect_now.alerts_evaluated", count=len(triggered))
    except Exception:
        logger.exception("collect_now.alert_error")

    return len(results)


@cli.command("collect-now")
def collect_now() -> None:
    """Trigger the data collection pipeline immediately (manual run)."""
    click.echo("Starting collection pipeline...")
    try:
        count = asyncio.run(run_collection_job())
        click.echo(f"Done — {count} tokens collected, scored and persisted.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# Database management helpers (async)
# ---------------------------------------------------------------------------


async def fetch_table_counts() -> dict[str, int]:
    """Return row counts for every table in ALLOWED_TABLES.

    Returns:
        Dict mapping table name → row count.
    """
    from sqlalchemy import text  # noqa: PLC0415

    from app.db.session import _SessionLocal  # noqa: PLC0415

    counts: dict[str, int] = {}
    async with _SessionLocal() as session:
        for table in ALLOWED_TABLES:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
            row = result.scalar_one()
            counts[table] = int(row)
    return counts


async def truncate_all_tables() -> None:
    """Truncate every table in ALLOWED_TABLES (CASCADE)."""
    from sqlalchemy import text  # noqa: PLC0415

    from app.db.session import _SessionLocal  # noqa: PLC0415

    async with _SessionLocal() as session:
        for table in ALLOWED_TABLES:
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))  # noqa: S608
        await session.commit()


async def truncate_table(table_name: str) -> None:
    """Truncate a single table by name (CASCADE).

    Args:
        table_name: Must be in ALLOWED_TABLES (validated by caller).
    """
    from sqlalchemy import text  # noqa: PLC0415

    from app.db.session import _SessionLocal  # noqa: PLC0415

    async with _SessionLocal() as session:
        await session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))  # noqa: S608
        await session.commit()


async def run_seed(target: str) -> None:
    """Run seed scripts for the given target.

    Args:
        target: One of 'rankings', 'narratives', or 'all'.
    """
    import importlib  # noqa: PLC0415

    if target in ("rankings", "all"):
        mod = importlib.import_module("scripts.seed_data")
        await mod.seed()  # type: ignore[attr-defined]

    if target in ("narratives", "all"):
        mod_hist = importlib.import_module("scripts.seed_historical_data")
        await mod_hist.seed()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# cryptoai db-status
# ---------------------------------------------------------------------------


@cli.command("db-status")
def db_status() -> None:
    """Show row counts for every data table."""
    try:
        counts = asyncio.run(fetch_table_counts())
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    click.echo(f"\n{'Table':<25} {'Rows':>10}")
    click.echo("-" * 37)
    total = 0
    for table, count in counts.items():
        click.echo(f"{table:<25} {count:>10}")
        total += count
    click.echo("-" * 37)
    click.echo(f"{'TOTAL':<25} {total:>10}\n")


# ---------------------------------------------------------------------------
# cryptoai db-clean --confirm
# ---------------------------------------------------------------------------


@cli.command("db-clean")
@click.option("--confirm", is_flag=True, default=False, help="Required to actually truncate.")
def db_clean(confirm: bool) -> None:
    """Truncate ALL data tables. Requires --confirm."""
    if not confirm:
        click.echo("⚠️  This will delete all data. Pass --confirm to proceed.", err=True)
        raise SystemExit(1)

    try:
        asyncio.run(truncate_all_tables())
        click.echo("All tables truncated successfully.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# cryptoai db-truncate <table> --confirm
# ---------------------------------------------------------------------------


@cli.command("db-truncate")
@click.argument("table")
@click.option("--confirm", is_flag=True, default=False, help="Required to actually truncate.")
def db_truncate(table: str, confirm: bool) -> None:
    """Truncate a specific data table. Requires --confirm."""
    if table not in ALLOWED_TABLES:
        click.echo(
            f"Error: '{table}' is not an allowed table.\n"
            f"Allowed: {', '.join(ALLOWED_TABLES)}",
            err=True,
        )
        raise SystemExit(1)

    if not confirm:
        click.echo(f"⚠️  This will delete all data from '{table}'. Pass --confirm to proceed.", err=True)
        raise SystemExit(1)

    try:
        asyncio.run(truncate_table(table))
        click.echo(f"Table '{table}' truncated successfully.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# cryptoai seed <target>
# ---------------------------------------------------------------------------


@cli.command("seed")
@click.argument("target")
def seed(target: str) -> None:
    """Run seed scripts. TARGET: rankings, narratives, or all."""
    if target not in _SEED_TARGETS:
        click.echo(
            f"Error: invalid target '{target}'. Must be one of: {', '.join(sorted(_SEED_TARGETS))}",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Seeding '{target}'...")
    try:
        asyncio.run(run_seed(target))
        click.echo(f"Seed '{target}' completed successfully.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    cli()
