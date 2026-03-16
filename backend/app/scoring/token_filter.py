"""Token filter — excludes stablecoins, wrapped tokens, and dead projects.

Addresses Item 1 of the Ranking Quality Loop: the ranking should answer
'which altcoins could explode during the next ATH?', not 'which stablecoin
has the best peg'.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Default exclusion sets (upper-case symbols)
# ---------------------------------------------------------------------------

_DEFAULT_STABLECOINS: frozenset[str] = frozenset(
    {
        "USDT",
        "USDC",
        "DAI",
        "BUSD",
        "TUSD",
        "FRAX",
        "FDUSD",
        "USD1",
        "USDP",
        "GUSD",
        "LUSD",
        "SUSD",
        "MIM",
        "CRVUSD",
        "GHO",
        "PYUSD",
        "USDD",
        "USDJ",
        "USDN",
        "EURS",
        "EURT",
        "XSGD",
        "BIDR",
        "IDRT",
        "UST",
    }
)

_DEFAULT_WRAPPED: frozenset[str] = frozenset(
    {
        "WBTC",
        "WETH",
        "STETH",
        "CBETH",
        "RETH",
        "WBNB",
        "WMATIC",
        "WAVAX",
        "WFTM",
        "WSOL",
        "WTRX",
        "TBTC",
        "HBTC",
        "RENBTC",
        "SBTC",
        "METH",
        "MSOL",
        "JITOMSOL",
        "BNSOL",
    }
)

_DEFAULT_MIN_VOLUME_24H: float = 10_000.0


class TokenFilter:
    """Filter tokens by category (stablecoin / wrapped) and health (volume).

    Usage::

        tf = TokenFilter()
        if tf.should_exclude(symbol="USDT", volume_24h=1e9):
            # skip this token
            ...
    """

    __slots__ = ("stablecoins", "wrapped", "extra_exclude", "min_volume_24h")

    def __init__(
        self,
        *,
        stablecoins: frozenset[str] | None = None,
        wrapped: frozenset[str] | None = None,
        extra_exclude: set[str] | None = None,
        min_volume_24h: float = _DEFAULT_MIN_VOLUME_24H,
    ) -> None:
        self.stablecoins = stablecoins if stablecoins is not None else _DEFAULT_STABLECOINS
        self.wrapped = wrapped if wrapped is not None else _DEFAULT_WRAPPED
        self.extra_exclude = extra_exclude or set()
        self.min_volume_24h = min_volume_24h

    # ------------------------------------------------------------------
    # Symbol-based check
    # ------------------------------------------------------------------

    def is_excluded(self, symbol: str) -> bool:
        """Return ``True`` if *symbol* belongs to any exclusion category."""
        upper = symbol.upper()
        return (
            upper in self.stablecoins
            or upper in self.wrapped
            or upper in {s.upper() for s in self.extra_exclude}
        )

    # ------------------------------------------------------------------
    # Volume-based check
    # ------------------------------------------------------------------

    def is_dead(self, *, volume_24h: float | None) -> bool:
        """Return ``True`` when 24h volume is below the minimum threshold.

        ``None`` volume is treated as dead (no data available ⇒ untradeable).
        """
        if volume_24h is None:
            return True
        return volume_24h < self.min_volume_24h

    # ------------------------------------------------------------------
    # Combined check
    # ------------------------------------------------------------------

    def should_exclude(self, *, symbol: str, volume_24h: float | None) -> bool:
        """Return ``True`` when the token should be filtered from rankings."""
        return self.is_excluded(symbol) or self.is_dead(volume_24h=volume_24h)

    # ------------------------------------------------------------------
    # Convenience property
    # ------------------------------------------------------------------

    @property
    def excluded_symbols(self) -> frozenset[str]:
        """Union of all symbol-based exclusion sets (upper-case)."""
        return self.stablecoins | self.wrapped | frozenset(s.upper() for s in self.extra_exclude)
