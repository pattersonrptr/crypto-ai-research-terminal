"""TDD tests for real cycle price data seeding.

Item 6 of Ranking Credibility Sprint: provide real bottom/top prices for
each historical cycle so backtesting validates against actual market data
instead of synthetic numbers.
"""

from __future__ import annotations

from app.backtesting.cycle_config import CYCLES
from app.backtesting.ground_truth import build_ground_truth


class TestRealCyclePricesExist:
    """A real_cycle_prices module must provide bottom/top price dicts."""

    def test_module_imports(self) -> None:
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        assert isinstance(CYCLE_BOTTOM_PRICES, dict)
        assert isinstance(CYCLE_TOP_PRICES, dict)

    def test_all_cycles_have_prices(self) -> None:
        """Every cycle in CYCLES must have bottom and top prices."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        for cycle_name in CYCLES:
            assert cycle_name in CYCLE_BOTTOM_PRICES, f"missing bottom prices for {cycle_name}"
            assert cycle_name in CYCLE_TOP_PRICES, f"missing top prices for {cycle_name}"

    def test_cycle_2_has_known_tokens(self) -> None:
        """Cycle 2 must include BTC, ETH, SOL, BNB at minimum."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        bottom = CYCLE_BOTTOM_PRICES["cycle_2_2019_2021"]
        top = CYCLE_TOP_PRICES["cycle_2_2019_2021"]
        for symbol in ("BTC", "ETH", "SOL", "BNB"):
            assert symbol in bottom, f"{symbol} missing from cycle 2 bottom prices"
            assert symbol in top, f"{symbol} missing from cycle 2 top prices"

    def test_prices_are_positive(self) -> None:
        """All prices must be > 0."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        for cycle_name, prices in CYCLE_BOTTOM_PRICES.items():
            for symbol, price in prices.items():
                assert price > 0, f"{cycle_name}/{symbol} bottom price is {price}"
        for cycle_name, prices in CYCLE_TOP_PRICES.items():
            for symbol, price in prices.items():
                assert price > 0, f"{cycle_name}/{symbol} top price is {price}"

    def test_top_prices_greater_than_bottom(self) -> None:
        """In a bull cycle, tops should be > bottoms for most tokens."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        for cycle_name in CYCLE_BOTTOM_PRICES:
            bottom = CYCLE_BOTTOM_PRICES[cycle_name]
            top = CYCLE_TOP_PRICES[cycle_name]
            gains = 0
            total = 0
            for symbol in bottom:
                if symbol in top:
                    total += 1
                    if top[symbol] > bottom[symbol]:
                        gains += 1
            # In a bull market, at least 60% of tokens should gain
            assert gains / total >= 0.60, f"{cycle_name}: only {gains}/{total} tokens gained"


class TestRealCyclePricesProduceValidGroundTruth:
    """Real prices must produce meaningful ground truth via build_ground_truth."""

    def test_cycle_2_has_known_winners(self) -> None:
        """Cycle 2 (2019-2021) must identify SOL and BNB as big winners."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        gt = build_ground_truth(
            "cycle_2_2019_2021",
            CYCLE_BOTTOM_PRICES["cycle_2_2019_2021"],
            CYCLE_TOP_PRICES["cycle_2_2019_2021"],
        )
        winners = gt.winner_symbols
        # SOL went from ~$1.50 to ~$260 (173x) — must be a winner
        assert "SOL" in winners
        # BNB went from ~$5 to ~$690 (138x) — must be a winner
        assert "BNB" in winners

    def test_cycle_2_has_at_least_5_winners(self) -> None:
        """Cycle 2 had many 10x+ tokens — expect at least 5 winners."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        gt = build_ground_truth(
            "cycle_2_2019_2021",
            CYCLE_BOTTOM_PRICES["cycle_2_2019_2021"],
            CYCLE_TOP_PRICES["cycle_2_2019_2021"],
        )
        assert gt.n_winners >= 5

    def test_cycle_3_identifies_winners(self) -> None:
        """Cycle 3 (2022-2025) must identify at least some winners."""
        from app.backtesting.real_cycle_prices import CYCLE_BOTTOM_PRICES, CYCLE_TOP_PRICES

        gt = build_ground_truth(
            "cycle_3_2022_2025",
            CYCLE_BOTTOM_PRICES["cycle_3_2022_2025"],
            CYCLE_TOP_PRICES["cycle_3_2022_2025"],
        )
        # SOL went from ~$8 to ~$295 (36x), SUI from ~$0.36 to ~$5.3 (14x)
        assert gt.n_winners >= 3

    def test_build_ground_truth_helper_available(self) -> None:
        """Convenience function get_real_ground_truth must exist."""
        from app.backtesting.real_cycle_prices import get_real_ground_truth

        gt = get_real_ground_truth("cycle_2_2019_2021")
        assert gt.cycle_name == "cycle_2_2019_2021"
        assert len(gt.entries) > 0
