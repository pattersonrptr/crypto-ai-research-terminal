"""Multi-cycle token registry — defines token lists and cycle boundaries.

Each BTC cycle has:
- A **bottom date**: approximate price floor (accumulation start).
- A **top date**: approximate price peak (distribution start).
- A **token list**: tokens that existed and were actively traded during
  that cycle, with their CoinGecko IDs for historical data retrieval.

Cycle boundaries are based on well-known BTC market cycles:
- Cycle 1 (2015–2018): post-Mt. Gox bottom to Dec 2017 ATH
- Cycle 2 (2019–2021): post-2018 bear bottom to Nov 2021 ATH
- Cycle 3 (2022–2025): post-FTX bottom to Jan 2025 ATH

This module is part of Phase 14 — Backtesting Multi-Cycle Validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CycleTokenEntry:
    """A single token tracked within a market cycle.

    Args:
        symbol: Token ticker (e.g. ``"BTC"``).
        coingecko_id: CoinGecko API identifier (e.g. ``"bitcoin"``).
    """

    symbol: str
    coingecko_id: str


@dataclass
class CycleDef:
    """Definition of a BTC market cycle with tracked tokens.

    Args:
        name: Unique cycle identifier (e.g. ``"cycle_2_2019_2021"``).
        bottom_date: Approximate cycle price floor date.
        top_date: Approximate cycle price peak date.
        tokens: Tokens tracked in this cycle.
    """

    name: str
    bottom_date: date
    top_date: date
    tokens: list[CycleTokenEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.top_date <= self.bottom_date:
            raise ValueError(
                f"top_date must be after bottom_date: "
                f"{self.top_date} <= {self.bottom_date}"
            )

    @property
    def duration_days(self) -> int:
        """Number of days from bottom to top."""
        return (self.top_date - self.bottom_date).days


# ---------------------------------------------------------------------------
# Token lists per cycle
# ---------------------------------------------------------------------------

_CYCLE_1_TOKENS: list[CycleTokenEntry] = [
    CycleTokenEntry("BTC", "bitcoin"),
    CycleTokenEntry("ETH", "ethereum"),
    CycleTokenEntry("XRP", "ripple"),
    CycleTokenEntry("LTC", "litecoin"),
    CycleTokenEntry("DASH", "dash"),
    CycleTokenEntry("XMR", "monero"),
    CycleTokenEntry("NEM", "nem"),
    CycleTokenEntry("NEO", "neo"),
    CycleTokenEntry("EOS", "eos"),
    CycleTokenEntry("IOTA", "iota"),
    CycleTokenEntry("ADA", "cardano"),
    CycleTokenEntry("TRX", "tron"),
    CycleTokenEntry("XLM", "stellar"),
    CycleTokenEntry("VET", "vechain"),
    CycleTokenEntry("BNB", "binancecoin"),
]

_CYCLE_2_TOKENS: list[CycleTokenEntry] = [
    *_CYCLE_1_TOKENS,
    CycleTokenEntry("SOL", "solana"),
    CycleTokenEntry("AVAX", "avalanche-2"),
    CycleTokenEntry("MATIC", "matic-network"),
    CycleTokenEntry("DOT", "polkadot"),
    CycleTokenEntry("LINK", "chainlink"),
    CycleTokenEntry("UNI", "uniswap"),
    CycleTokenEntry("AAVE", "aave"),
    CycleTokenEntry("LUNA", "terra-luna"),
    CycleTokenEntry("FTT", "ftx-token"),
    CycleTokenEntry("ATOM", "cosmos"),
    CycleTokenEntry("ALGO", "algorand"),
    CycleTokenEntry("FIL", "filecoin"),
    CycleTokenEntry("NEAR", "near"),
    CycleTokenEntry("FTM", "fantom"),
    CycleTokenEntry("SAND", "the-sandbox"),
    CycleTokenEntry("MANA", "decentraland"),
]

_CYCLE_3_TOKENS: list[CycleTokenEntry] = [
    *_CYCLE_2_TOKENS,
    CycleTokenEntry("ARB", "arbitrum"),
    CycleTokenEntry("OP", "optimism"),
    CycleTokenEntry("TIA", "celestia"),
    CycleTokenEntry("INJ", "injective-protocol"),
    CycleTokenEntry("JUP", "jupiter-exchange-solana"),
    CycleTokenEntry("SUI", "sui"),
    CycleTokenEntry("SEI", "sei-network"),
    CycleTokenEntry("APT", "aptos"),
    CycleTokenEntry("EIGEN", "eigenlayer"),
    CycleTokenEntry("TAO", "bittensor"),
    CycleTokenEntry("RNDR", "render-token"),
    CycleTokenEntry("FET", "fetch-ai"),
    CycleTokenEntry("WLD", "worldcoin-wld"),
    CycleTokenEntry("STX", "blockstack"),
    CycleTokenEntry("IMX", "immutable-x"),
    CycleTokenEntry("PENDLE", "pendle"),
    CycleTokenEntry("PYTH", "pyth-network"),
    CycleTokenEntry("JTO", "jito-governance-token"),
    CycleTokenEntry("STRK", "starknet"),
]


# ---------------------------------------------------------------------------
# Cycle definitions
# ---------------------------------------------------------------------------

CYCLES: dict[str, CycleDef] = {
    "cycle_1_2015_2018": CycleDef(
        name="cycle_1_2015_2018",
        bottom_date=date(2015, 1, 14),   # BTC ~$170
        top_date=date(2017, 12, 17),     # BTC ~$19,800
        tokens=_CYCLE_1_TOKENS,
    ),
    "cycle_2_2019_2021": CycleDef(
        name="cycle_2_2019_2021",
        bottom_date=date(2018, 12, 15),  # BTC ~$3,200
        top_date=date(2021, 11, 10),     # BTC ~$69,000
        tokens=_CYCLE_2_TOKENS,
    ),
    "cycle_3_2022_2025": CycleDef(
        name="cycle_3_2022_2025",
        bottom_date=date(2022, 11, 21),  # BTC ~$15,500 (post-FTX)
        top_date=date(2025, 1, 20),      # BTC ~$109,000
        tokens=_CYCLE_3_TOKENS,
    ),
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_cycle_names() -> list[str]:
    """Return sorted list of all cycle names."""
    return sorted(CYCLES.keys())


def get_cycle(name: str) -> CycleDef:
    """Return a cycle definition by name.

    Raises:
        KeyError: If the cycle name is not found.
    """
    return CYCLES[name]


def get_all_tokens_for_cycle(name: str) -> list[CycleTokenEntry]:
    """Return the token list for a given cycle.

    Raises:
        KeyError: If the cycle name is not found.
    """
    return get_cycle(name).tokens


def get_coingecko_id(symbol: str, cycle_name: str) -> str | None:
    """Look up a CoinGecko ID for *symbol* within *cycle_name*.

    Returns:
        The CoinGecko ID string, or ``None`` if the symbol is not
        tracked in the given cycle.
    """
    for token in get_all_tokens_for_cycle(cycle_name):
        if token.symbol == symbol:
            return token.coingecko_id
    return None
