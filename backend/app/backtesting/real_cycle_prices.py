"""Real historical cycle price data for backtesting ground truth.

Provides approximate bottom and top USD prices for tokens tracked in each
BTC market cycle.  Prices are sourced from CoinGecko historical data and
represent approximate cycle-bottom lows and cycle-top highs.

Cycle definitions match ``cycle_config.py``:
- Cycle 1 (2015–2018): BTC ~$170 → ~$19,800
- Cycle 2 (2019–2021): BTC ~$3,200 → ~$69,000
- Cycle 3 (2022–2025): BTC ~$15,500 → ~$109,000

.. note::

   Prices are **approximate** — exact daily lows/highs vary by exchange.
   They are accurate enough for ROI-based ground truth classification
   (5× winner, 10× big winner thresholds).
"""

from __future__ import annotations

from app.backtesting.ground_truth import CycleGroundTruth, build_ground_truth

# -----------------------------------------------------------------------
# Cycle 1: 2015–2018  (BTC bottom ~Jan 2015, top ~Dec 2017)
# -----------------------------------------------------------------------

_CYCLE_1_BOTTOM: dict[str, float] = {
    "BTC": 170.0,
    "ETH": 0.50,  # ETH launched mid-2015, early trading ~$0.50
    "XRP": 0.005,
    "LTC": 1.20,
    "DASH": 1.50,
    "XMR": 0.25,
    "NEM": 0.0001,
    "NEO": 0.08,  # Antshares at the time
    "EOS": 0.50,  # EOS ICO mid-2017, bottom ~$0.50
    "IOTA": 0.15,
    "ADA": 0.02,  # ADA launched late 2017, early trading
    "TRX": 0.001,
    "XLM": 0.001,
    "VET": 0.003,  # VeChain (VEN at the time)
    "BNB": 0.10,  # BNB launched mid-2017
}

_CYCLE_1_TOP: dict[str, float] = {
    "BTC": 19_800.0,
    "ETH": 1_430.0,
    "XRP": 3.40,
    "LTC": 375.0,
    "DASH": 1_500.0,
    "XMR": 495.0,
    "NEM": 1.80,
    "NEO": 196.0,
    "EOS": 18.0,
    "IOTA": 5.60,
    "ADA": 1.30,
    "TRX": 0.30,
    "XLM": 0.93,
    "VET": 0.09,
    "BNB": 25.0,
}

# -----------------------------------------------------------------------
# Cycle 2: 2019–2021  (BTC bottom ~Dec 2018, top ~Nov 2021)
# -----------------------------------------------------------------------

_CYCLE_2_BOTTOM: dict[str, float] = {
    # Inherited from Cycle 1
    "BTC": 3_200.0,
    "ETH": 85.0,
    "XRP": 0.25,
    "LTC": 22.0,
    "DASH": 36.0,
    "XMR": 39.0,
    "NEM": 0.03,
    "NEO": 4.50,
    "EOS": 1.80,
    "IOTA": 0.15,
    "ADA": 0.03,
    "TRX": 0.01,
    "XLM": 0.07,
    "VET": 0.003,
    "BNB": 5.0,
    # New in Cycle 2
    "SOL": 1.50,  # Solana launched Mar 2020
    "AVAX": 3.00,  # Avalanche launched Sep 2020
    "MATIC": 0.01,
    "DOT": 2.80,  # Polkadot launched Aug 2020
    "LINK": 1.60,
    "UNI": 1.00,  # Uniswap launched Sep 2020
    "AAVE": 25.0,  # AAVE launched Oct 2020
    "LUNA": 0.50,
    "FTT": 1.30,
    "ATOM": 1.60,
    "ALGO": 0.10,
    "FIL": 20.0,  # Filecoin launched Oct 2020
    "NEAR": 0.50,
    "FTM": 0.005,
    "SAND": 0.02,
    "MANA": 0.02,
}

_CYCLE_2_TOP: dict[str, float] = {
    "BTC": 69_000.0,
    "ETH": 4_800.0,
    "XRP": 1.85,
    "LTC": 412.0,
    "DASH": 460.0,
    "XMR": 517.0,
    "NEM": 0.85,
    "NEO": 140.0,
    "EOS": 15.0,
    "IOTA": 2.60,
    "ADA": 3.10,
    "TRX": 0.18,
    "XLM": 0.80,
    "VET": 0.28,
    "BNB": 690.0,
    "SOL": 260.0,
    "AVAX": 145.0,
    "MATIC": 2.90,
    "DOT": 55.0,
    "LINK": 52.0,
    "UNI": 45.0,
    "AAVE": 660.0,
    "LUNA": 119.0,
    "FTT": 84.0,
    "ATOM": 44.0,
    "ALGO": 2.40,
    "FIL": 238.0,
    "NEAR": 20.0,
    "FTM": 3.50,
    "SAND": 8.40,
    "MANA": 5.90,
}

# -----------------------------------------------------------------------
# Cycle 3: 2022–2025  (BTC bottom ~Nov 2022, top ~Jan 2025)
# -----------------------------------------------------------------------

_CYCLE_3_BOTTOM: dict[str, float] = {
    # Inherited tokens
    "BTC": 15_500.0,
    "ETH": 900.0,
    "XRP": 0.30,
    "LTC": 50.0,
    "DASH": 35.0,
    "XMR": 110.0,
    "NEM": 0.02,
    "NEO": 5.50,
    "EOS": 0.70,
    "IOTA": 0.10,
    "ADA": 0.24,
    "TRX": 0.04,
    "XLM": 0.07,
    "VET": 0.015,
    "BNB": 210.0,
    "SOL": 8.00,
    "AVAX": 10.0,
    "MATIC": 0.75,
    "DOT": 4.00,
    "LINK": 5.50,
    "UNI": 3.50,
    "AAVE": 47.0,
    "LUNA": 0.0001,  # Post-collapse Terra Classic
    "FTT": 1.00,  # Post-FTX collapse
    "ATOM": 7.50,
    "ALGO": 0.10,
    "FIL": 2.80,
    "NEAR": 1.00,
    "FTM": 0.17,
    "SAND": 0.25,
    "MANA": 0.28,
    # New in Cycle 3
    "ARB": 0.80,  # Arbitrum airdrop Mar 2023
    "OP": 0.90,
    "TIA": 2.00,  # Celestia launched Oct 2023
    "INJ": 1.20,
    "JUP": 0.50,  # Jupiter launched Jan 2024
    "SUI": 0.36,
    "SEI": 0.10,
    "APT": 3.00,
    "EIGEN": 2.50,  # EigenLayer launched Oct 2024
    "TAO": 30.0,
    "RNDR": 0.40,
    "FET": 0.05,
    "WLD": 1.10,
    "STX": 0.25,
    "IMX": 0.35,
    "PENDLE": 0.30,
    "PYTH": 0.20,
    "JTO": 1.50,
    "STRK": 0.70,
}

_CYCLE_3_TOP: dict[str, float] = {
    "BTC": 109_000.0,
    "ETH": 4_100.0,
    "XRP": 3.40,
    "LTC": 137.0,
    "DASH": 65.0,
    "XMR": 220.0,
    "NEM": 0.04,
    "NEO": 25.0,
    "EOS": 1.60,
    "IOTA": 0.50,
    "ADA": 1.20,
    "TRX": 0.45,
    "XLM": 0.63,
    "VET": 0.065,
    "BNB": 795.0,
    "SOL": 295.0,
    "AVAX": 65.0,
    "MATIC": 1.30,
    "DOT": 12.0,
    "LINK": 30.0,
    "UNI": 19.5,
    "AAVE": 400.0,
    "LUNA": 0.0002,  # Terra Classic — essentially dead
    "FTT": 3.50,
    "ATOM": 16.0,
    "ALGO": 0.60,
    "FIL": 12.0,
    "NEAR": 9.00,
    "FTM": 1.45,
    "SAND": 0.95,
    "MANA": 0.90,
    "ARB": 2.40,
    "OP": 4.80,
    "TIA": 21.0,
    "INJ": 53.0,
    "JUP": 2.20,
    "SUI": 5.30,
    "SEI": 1.10,
    "APT": 19.0,
    "EIGEN": 5.50,
    "TAO": 730.0,
    "RNDR": 13.5,
    "FET": 3.50,
    "WLD": 12.0,
    "STX": 4.00,
    "IMX": 3.70,
    "PENDLE": 7.50,
    "PYTH": 1.20,
    "JTO": 5.30,
    "STRK": 2.80,
}


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------

CYCLE_BOTTOM_PRICES: dict[str, dict[str, float]] = {
    "cycle_1_2015_2018": _CYCLE_1_BOTTOM,
    "cycle_2_2019_2021": _CYCLE_2_BOTTOM,
    "cycle_3_2022_2025": _CYCLE_3_BOTTOM,
}

CYCLE_TOP_PRICES: dict[str, dict[str, float]] = {
    "cycle_1_2015_2018": _CYCLE_1_TOP,
    "cycle_2_2019_2021": _CYCLE_2_TOP,
    "cycle_3_2022_2025": _CYCLE_3_TOP,
}


def get_real_ground_truth(cycle_name: str) -> CycleGroundTruth:
    """Build ground truth from real historical prices for a cycle.

    Args:
        cycle_name: One of the keys in :data:`CYCLE_BOTTOM_PRICES`.

    Returns:
        :class:`CycleGroundTruth` with entries sorted by ROI descending.

    Raises:
        KeyError: If *cycle_name* is not found in the price data.
    """
    return build_ground_truth(
        cycle_name,
        CYCLE_BOTTOM_PRICES[cycle_name],
        CYCLE_TOP_PRICES[cycle_name],
    )
