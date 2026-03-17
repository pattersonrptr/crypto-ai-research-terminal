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
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608  # nosec B608
            )
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
        await mod.seed()

    if target in ("narratives", "all"):
        mod_hist = importlib.import_module("scripts.seed_historical_data")
        await mod_hist.seed()


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
            f"Error: '{table}' is not an allowed table.\n" f"Allowed: {', '.join(ALLOWED_TABLES)}",
            err=True,
        )
        raise SystemExit(1)

    if not confirm:
        click.echo(
            f"⚠️  This will delete all data from '{table}'. Pass --confirm to proceed.", err=True
        )
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


# ---------------------------------------------------------------------------
# cryptoai backtest-collect <cycle>
# ---------------------------------------------------------------------------


async def run_backtest_collect(cycle_name: str) -> Any:
    """Collect historical CoinGecko data for a cycle and persist snapshots.

    Args:
        cycle_name: Cycle identifier (e.g. ``"cycle_2_2019_2021"``).

    Returns:
        A :class:`CollectionResult` with snapshots and error info.

    Raises:
        KeyError: If the cycle name is not found.
    """
    from sqlalchemy import text  # noqa: PLC0415

    from app.backtesting.cycle_config import get_cycle  # noqa: PLC0415
    from app.backtesting.multi_cycle_collector import MultiCycleCollector  # noqa: PLC0415
    from app.config import Settings  # noqa: PLC0415
    from app.db.session import _SessionLocal  # noqa: PLC0415

    # Validate cycle exists (raises KeyError if not found)
    get_cycle(cycle_name)

    settings = Settings()
    api_key = settings.coingecko_api_key
    base_url = "https://api.coingecko.com/api/v3"

    class _LiveCollector(MultiCycleCollector):
        """Subclass that uses httpx for real CoinGecko API calls."""

        def __init__(self) -> None:
            super().__init__(delay_between_requests=6.0)

        async def _fetch_market_chart(
            self,
            coingecko_id: str,
            from_ts: int,
            to_ts: int,
        ) -> dict[str, Any]:
            url = f"{base_url}/coins/{coingecko_id}/market_chart/range"
            params: dict[str, str] = {
                "vs_currency": "usd",
                "from": str(from_ts),
                "to": str(to_ts),
            }
            headers: dict[str, str] = {}
            if api_key:
                headers["x-cg-demo-api-key"] = api_key
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers, timeout=30)
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()
                return data

    collector = _LiveCollector()
    result = await collector.collect_cycle(cycle_name)

    # Persist snapshots to historical_snapshots table
    if result.snapshots:
        async with _SessionLocal() as session:
            dialect = session.get_bind().dialect.name
            for snap in result.snapshots:
                if dialect == "sqlite":
                    stmt = text(
                        "INSERT OR IGNORE INTO historical_snapshots "
                        "(symbol, snapshot_date, price_usd, market_cap_usd, "
                        "volume_usd, cycle_tag) "
                        "VALUES (:symbol, :snapshot_date, :price_usd, "
                        ":market_cap_usd, :volume_usd, :cycle_tag)"
                    )
                else:
                    stmt = text(
                        "INSERT INTO historical_snapshots "
                        "(symbol, snapshot_date, price_usd, market_cap_usd, "
                        "volume_usd, cycle_tag) "
                        "VALUES (:symbol, :snapshot_date, :price_usd, "
                        ":market_cap_usd, :volume_usd, :cycle_tag) "
                        "ON CONFLICT (symbol, snapshot_date) DO NOTHING"
                    )
                await session.execute(
                    stmt,
                    {
                        "symbol": snap.get("symbol", ""),
                        "snapshot_date": snap.get("snapshot_date"),
                        "price_usd": snap.get("price_usd", 0),
                        "market_cap_usd": snap.get("market_cap_usd", 0),
                        "volume_usd": snap.get("volume_usd", 0),
                        "cycle_tag": cycle_name,
                    },
                )
            await session.commit()
        logger.info(
            "backtest_collect.persisted",
            cycle=cycle_name,
            n_snapshots=len(result.snapshots),
        )

    return result


@cli.command("backtest-collect")
@click.argument("cycle")
def backtest_collect(cycle: str) -> None:
    """Collect real CoinGecko historical data for a market cycle."""
    from app.backtesting.cycle_config import get_cycle_names  # noqa: PLC0415

    valid_cycles = get_cycle_names()
    if cycle not in valid_cycles:
        click.echo(
            f"Error: cycle '{cycle}' not found.\n" f"Available cycles: {', '.join(valid_cycles)}",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Collecting historical data for cycle '{cycle}'...")
    try:
        result = asyncio.run(run_backtest_collect(cycle))
        click.echo(
            f"Done — {result.n_tokens_collected} tokens collected, "
            f"{len(result.snapshots)} snapshots persisted."
        )
        if result.errors:
            click.echo(f"⚠️  {len(result.errors)} token(s) failed:")
            for sym, err in result.errors.items():
                click.echo(f"  {sym}: {err}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


# ---------------------------------------------------------------------------
# cryptoai backtest-calibrate [--cycle CYCLE] [--step STEP] [--k K]
# ---------------------------------------------------------------------------


async def run_backtest_calibrate(
    *,
    cycle: str = "all",
    step: float = 0.10,
    k: int = 10,
) -> dict[str, Any]:
    """Run weight calibration against historical snapshot data.

    Args:
        cycle: Cycle name or ``"all"`` for all cycles.
        step: Grid step size for weight generation.
        k: Top-K for Precision@K evaluation.

    Returns:
        Dict with ``cycle``, ``best_weights``, ``best_precision_at_k``,
        ``n_combinations_tested``.

    Raises:
        KeyError: If the cycle name is not found.
    """

    from sqlalchemy import select  # noqa: PLC0415

    from app.backtesting.cycle_config import get_cycle, get_cycle_names  # noqa: PLC0415
    from app.backtesting.ground_truth import build_ground_truth  # noqa: PLC0415
    from app.backtesting.weight_calibrator import calibrate_weights_with_rescoring  # noqa: PLC0415
    from app.db.session import _SessionLocal  # noqa: PLC0415
    from app.models.historical_snapshot import HistoricalSnapshot  # noqa: PLC0415

    cycles_to_run = get_cycle_names() if cycle == "all" else [cycle]

    # Validate cycles exist
    for c in cycles_to_run:
        get_cycle(c)  # raises KeyError if invalid

    best_overall_precision = -1.0
    best_overall_weights: dict[str, float] = {
        "fundamental": 0.30,
        "growth": 0.25,
        "narrative": 0.20,
        "listing": 0.15,
        "risk": 0.10,
    }
    total_combinations = 0

    for cycle_name in cycles_to_run:
        cycle_def = get_cycle(cycle_name)

        # Load snapshots from DB for this cycle's bottom date
        async with _SessionLocal() as session:
            stmt = select(HistoricalSnapshot).where(
                HistoricalSnapshot.cycle_tag == cycle_name,
                HistoricalSnapshot.snapshot_date == cycle_def.bottom_date,
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

        if not rows:
            logger.warning("backtest_calibrate.no_data", cycle=cycle_name)
            continue

        # Build snapshot dicts and ground truth
        snapshots = [
            {
                "symbol": r.symbol,
                "snapshot_date": r.snapshot_date,
                "price_usd": r.price_usd,
                "market_cap_usd": r.market_cap_usd,
                "volume_usd": r.volume_usd,
            }
            for r in rows
        ]

        # Build ground truth: bottom prices from bottom_date, top from top_date
        async with _SessionLocal() as session:
            stmt_top = select(HistoricalSnapshot).where(
                HistoricalSnapshot.cycle_tag == cycle_name,
                HistoricalSnapshot.snapshot_date == cycle_def.top_date,
            )
            result_top = await session.execute(stmt_top)
            top_rows = result_top.scalars().all()

        bottom_prices = {r.symbol: r.price_usd for r in rows}
        top_prices = {r.symbol: r.price_usd for r in top_rows}

        ground_truth = build_ground_truth(
            cycle_name=cycle_name,
            bottom_prices=bottom_prices,
            top_prices=top_prices,
        )

        # Run calibration
        cal_result = calibrate_weights_with_rescoring(
            snapshots=snapshots,
            snapshot_date=cycle_def.bottom_date,
            ground_truth=ground_truth,
            k=k,
            step=step,
        )

        total_combinations += cal_result.n_combinations_tested

        if cal_result.best_precision_at_k > best_overall_precision:
            best_overall_precision = cal_result.best_precision_at_k
            best_overall_weights = {
                "fundamental": cal_result.best_weights.fundamental,
                "growth": cal_result.best_weights.growth,
                "narrative": cal_result.best_weights.narrative,
                "listing": cal_result.best_weights.listing,
                "risk": cal_result.best_weights.risk,
            }

        logger.info(
            "backtest_calibrate.cycle_done",
            cycle=cycle_name,
            precision=cal_result.best_precision_at_k,
            n_tested=cal_result.n_combinations_tested,
        )

    return {
        "cycle": cycle,
        "best_weights": best_overall_weights,
        "best_precision_at_k": max(best_overall_precision, 0.0),
        "n_combinations_tested": total_combinations,
    }


@cli.command("backtest-calibrate")
@click.option("--cycle", default="all", show_default=True, help="Cycle name or 'all'.")
@click.option("--step", default=0.10, show_default=True, help="Grid step size.")
@click.option("--k", default=10, show_default=True, help="Top-K for Precision@K.")
def backtest_calibrate(cycle: str, step: float, k: int) -> None:
    """Run weight calibration against historical data."""
    click.echo(f"Running calibration (cycle={cycle}, step={step}, k={k})...")
    try:
        report = asyncio.run(run_backtest_calibrate(cycle=cycle, step=step, k=k))
    except KeyError as exc:
        click.echo(f"Error: cycle {exc} not found.", err=True)
        raise SystemExit(1) from exc
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    bw = report["best_weights"]
    click.echo(f"\n{'=' * 50}")
    click.echo("  Calibration Results")
    click.echo(f"{'=' * 50}")
    click.echo(f"  Cycle(s)          : {report['cycle']}")
    click.echo(f"  Combinations      : {report['n_combinations_tested']}")
    click.echo(f"  Best Precision@K  : {report['best_precision_at_k']:.4f}")
    click.echo("  Best Weights:")
    click.echo(f"    fundamental     : {bw['fundamental']:.2f}")
    click.echo(f"    growth          : {bw['growth']:.2f}")
    click.echo(f"    narrative       : {bw['narrative']:.2f}")
    click.echo(f"    listing         : {bw['listing']:.2f}")
    click.echo(f"    risk            : {bw['risk']:.2f}")
    click.echo(f"{'=' * 50}")
    click.echo(
        "\nTo apply these weights:\n"
        "  curl -X POST http://localhost:8000/backtesting/apply-weights \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{"
        f'"fundamental": {bw["fundamental"]}, '
        f'"growth": {bw["growth"]}, '
        f'"narrative": {bw["narrative"]}, '
        f'"listing": {bw["listing"]}, '
        f'"risk": {bw["risk"]}'
        f"}}'"
    )


if __name__ == "__main__":
    cli()
