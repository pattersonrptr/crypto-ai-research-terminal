"""Tests for backtesting.cycle_config — multi-cycle token registry.

TDD: RED phase — tests written first.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.backtesting.cycle_config import (
    CYCLES,
    CycleDef,
    CycleTokenEntry,
    get_all_tokens_for_cycle,
    get_coingecko_id,
    get_cycle,
    get_cycle_names,
)


class TestCycleDef:
    """CycleDef dataclass tests."""

    def test_cycle_def_fields_are_set(self) -> None:
        c = CycleDef(
            name="test",
            bottom_date=date(2020, 3, 13),
            top_date=date(2021, 11, 10),
            tokens=[],
        )
        assert c.name == "test"
        assert c.bottom_date == date(2020, 3, 13)
        assert c.top_date == date(2021, 11, 10)
        assert c.tokens == []

    def test_cycle_def_duration_days(self) -> None:
        c = CycleDef(
            name="test",
            bottom_date=date(2020, 1, 1),
            top_date=date(2020, 12, 31),
            tokens=[],
        )
        assert c.duration_days == 365

    def test_cycle_def_requires_top_after_bottom(self) -> None:
        with pytest.raises(ValueError, match="top_date must be after bottom_date"):
            CycleDef(
                name="bad",
                bottom_date=date(2021, 1, 1),
                top_date=date(2020, 1, 1),
                tokens=[],
            )


class TestCycleTokenEntry:
    """CycleTokenEntry dataclass tests."""

    def test_entry_fields_are_set(self) -> None:
        e = CycleTokenEntry(symbol="BTC", coingecko_id="bitcoin")
        assert e.symbol == "BTC"
        assert e.coingecko_id == "bitcoin"


class TestCyclesRegistry:
    """Tests for the CYCLES constant and helper functions."""

    def test_cycles_has_three_entries(self) -> None:
        assert len(CYCLES) == 3

    def test_cycle_names_are_correct(self) -> None:
        names = get_cycle_names()
        assert names == ["cycle_1_2015_2018", "cycle_2_2019_2021", "cycle_3_2022_2025"]

    def test_get_cycle_returns_correct_cycle(self) -> None:
        c = get_cycle("cycle_2_2019_2021")
        assert c.name == "cycle_2_2019_2021"
        assert c.bottom_date.year == 2018  # BTC bottom was Dec 2018

    def test_get_cycle_unknown_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_cycle("cycle_99")

    def test_cycle_1_has_at_least_10_tokens(self) -> None:
        c = get_cycle("cycle_1_2015_2018")
        assert len(c.tokens) >= 10

    def test_cycle_2_has_at_least_25_tokens(self) -> None:
        c = get_cycle("cycle_2_2019_2021")
        assert len(c.tokens) >= 25

    def test_cycle_3_has_at_least_35_tokens(self) -> None:
        c = get_cycle("cycle_3_2022_2025")
        assert len(c.tokens) >= 35

    def test_cycle_2_includes_all_cycle_1_tokens(self) -> None:
        c1_symbols = {t.symbol for t in get_cycle("cycle_1_2015_2018").tokens}
        c2_symbols = {t.symbol for t in get_cycle("cycle_2_2019_2021").tokens}
        assert c1_symbols.issubset(c2_symbols)

    def test_cycle_3_includes_all_cycle_2_tokens(self) -> None:
        c2_symbols = {t.symbol for t in get_cycle("cycle_2_2019_2021").tokens}
        c3_symbols = {t.symbol for t in get_cycle("cycle_3_2022_2025").tokens}
        assert c2_symbols.issubset(c3_symbols)

    def test_all_tokens_have_coingecko_ids(self) -> None:
        for cycle in CYCLES.values():
            for token in cycle.tokens:
                assert token.coingecko_id, f"{token.symbol} missing coingecko_id"

    def test_btc_and_eth_in_all_cycles(self) -> None:
        for cycle in CYCLES.values():
            symbols = {t.symbol for t in cycle.tokens}
            assert "BTC" in symbols, f"BTC missing from {cycle.name}"
            assert "ETH" in symbols, f"ETH missing from {cycle.name}"

    def test_get_all_tokens_for_cycle_returns_entries(self) -> None:
        tokens = get_all_tokens_for_cycle("cycle_1_2015_2018")
        assert len(tokens) >= 10
        assert all(isinstance(t, CycleTokenEntry) for t in tokens)

    def test_get_coingecko_id_known_symbol(self) -> None:
        cg_id = get_coingecko_id("BTC", "cycle_1_2015_2018")
        assert cg_id == "bitcoin"

    def test_get_coingecko_id_unknown_symbol_returns_none(self) -> None:
        result = get_coingecko_id("FAKE_COIN_XYZ", "cycle_1_2015_2018")
        assert result is None

    def test_cycle_bottom_dates_are_realistic(self) -> None:
        """Cycle bottoms should roughly correspond to known BTC cycle bottoms."""
        c1 = get_cycle("cycle_1_2015_2018")
        c2 = get_cycle("cycle_2_2019_2021")
        c3 = get_cycle("cycle_3_2022_2025")
        # Cycle 1 bottom: ~Jan 2015 (BTC ~$200)
        assert c1.bottom_date.year == 2015
        # Cycle 2 bottom: ~Dec 2018 (BTC ~$3200)
        assert c2.bottom_date.year == 2018
        # Cycle 3 bottom: ~Nov 2022 (BTC ~$15500)
        assert c3.bottom_date.year == 2022

    def test_cycle_top_dates_are_realistic(self) -> None:
        """Cycle tops should roughly correspond to known BTC cycle tops."""
        c1 = get_cycle("cycle_1_2015_2018")
        c2 = get_cycle("cycle_2_2019_2021")
        c3 = get_cycle("cycle_3_2022_2025")
        # Cycle 1 top: ~Dec 2017 / Jan 2018
        assert c1.top_date.year in {2017, 2018}
        # Cycle 2 top: ~Nov 2021
        assert c2.top_date.year == 2021
        # Cycle 3 top: ~Jan 2025 (latest known)
        assert c3.top_date.year in {2024, 2025}

    def test_no_duplicate_symbols_within_cycle(self) -> None:
        for cycle in CYCLES.values():
            symbols = [t.symbol for t in cycle.tokens]
            assert len(symbols) == len(set(symbols)), f"Duplicate symbols in {cycle.name}"
