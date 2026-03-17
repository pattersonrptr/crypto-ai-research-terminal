"""Token category classifier — tags tokens and applies risk multipliers.

Uses CoinGecko categories (when available) and a hardcoded symbol-based
fallback to classify tokens into internal categories. Each category has
an associated risk multiplier that adjusts the final opportunity score.

Memecoins get a 0.70× multiplier — they can still rank highly, but need
to score significantly better on fundamentals to beat a solid L1/L2.
"""

from __future__ import annotations

from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class TokenCategory(Enum):
    """Internal token category for risk-adjusted scoring."""

    MEMECOIN = "memecoin"
    L1 = "l1"
    L2 = "l2"
    DEFI = "defi"
    INFRASTRUCTURE = "infrastructure"
    GAMING = "gaming"
    AI = "ai"
    RWA = "rwa"
    PRIVACY = "privacy"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# CoinGecko category keywords → internal category mapping
# Priority: first match wins (order matters — meme before defi).
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: list[tuple[list[str], TokenCategory]] = [
    # Memecoins (highest priority — a meme defi token is still a meme)
    (
        [
            "meme",
            "meme-token",
            "dog-themed",
            "cat-themed",
            "elon musk-inspired",
            "4chan-themed",
            "political memes",
            "frog-themed",
        ],
        TokenCategory.MEMECOIN,
    ),
    # Layer 2
    (
        [
            "layer 2",
            "layer-2",
            "layer 2 (l2)",
            "optimistic rollup",
            "optimistic rollups",
            "zk-rollup",
            "zero knowledge (zk)",
        ],
        TokenCategory.L2,
    ),
    # Layer 1
    (
        [
            "layer 1",
            "layer-1",
            "layer 1 (l1)",
            "smart contract platform",
            "proof of work",
            "proof of stake",
        ],
        TokenCategory.L1,
    ),
    # Infrastructure / Oracles
    (
        [
            "oracle",
            "oracles",
            "interoperability",
            "cross-chain",
            "data availability",
            "storage",
            "infrastructure",
        ],
        TokenCategory.INFRASTRUCTURE,
    ),
    # AI
    (
        [
            "artificial-intelligence",
            "ai",
            "machine learning",
            "machine-learning",
            "gpu",
        ],
        TokenCategory.AI,
    ),
    # DeFi
    (
        [
            "defi",
            "decentralized-finance",
            "decentralized finance (defi)",
            "lending",
            "lending/borrowing",
            "dex",
            "decentralized exchange (dex)",
            "yield farming",
            "yield aggregator",
            "liquid staking",
        ],
        TokenCategory.DEFI,
    ),
    # Gaming / Metaverse
    (
        [
            "gaming",
            "gamefi",
            "metaverse",
            "play-to-earn",
        ],
        TokenCategory.GAMING,
    ),
    # RWA
    (
        [
            "real world assets",
            "real world assets (rwa)",
            "rwa",
            "tokenized real-world assets",
        ],
        TokenCategory.RWA,
    ),
    # Privacy
    (
        [
            "privacy",
            "privacy coins",
        ],
        TokenCategory.PRIVACY,
    ),
]

# ---------------------------------------------------------------------------
# Known memecoins by symbol (fallback when CoinGecko categories unavailable)
# ---------------------------------------------------------------------------

_KNOWN_MEMECOINS: frozenset[str] = frozenset(
    {
        "DOGE",
        "SHIB",
        "PEPE",
        "FLOKI",
        "BONK",
        "WIF",
        "BRETT",
        "MEME",
        "BABYDOGE",
        "ELON",
        "SAMO",
        "MILO",
        "SNEK",
        "MYRO",
        "TURBO",
        "LADYS",
        "WOJAK",
        "BOB",
        "ANDY",
        "FARTCOIN",
        "TRUMP",
        "MELANIA",
        "BOME",
        "NEIRO",
        "POPCAT",
        "MEW",
        "GOAT",
        "SPX",
        "PNUT",
        "ACT",
    }
)

# ---------------------------------------------------------------------------
# Risk multipliers per category
# ---------------------------------------------------------------------------

_RISK_MULTIPLIERS: dict[TokenCategory, float] = {
    TokenCategory.MEMECOIN: 0.70,
    TokenCategory.L1: 1.00,
    TokenCategory.L2: 1.00,
    TokenCategory.DEFI: 0.95,
    TokenCategory.INFRASTRUCTURE: 1.00,
    TokenCategory.GAMING: 0.90,
    TokenCategory.AI: 0.95,
    TokenCategory.RWA: 0.95,
    TokenCategory.PRIVACY: 0.90,
    TokenCategory.UNKNOWN: 0.90,
}


class TokenCategoryClassifier:
    """Classify tokens and provide risk-adjusted multipliers.

    Usage::

        cat = TokenCategoryClassifier.classify("PEPE", ["Meme", "Ethereum"])
        mult = TokenCategoryClassifier.risk_multiplier(cat)
        adjusted_score = base_score * mult
    """

    @staticmethod
    def classify(
        symbol: str,
        categories: list[str] | None = None,
    ) -> TokenCategory:
        """Classify a token into an internal category.

        Lookup order:
        1. CoinGecko categories (when provided) — first keyword match wins.
        2. Known memecoin symbols (hardcoded fallback).
        3. ``UNKNOWN`` when no match is found.

        Args:
            symbol: Token symbol (e.g. ``"PEPE"``).
            categories: CoinGecko category strings (e.g. ``["Meme"]``).

        Returns:
            The classified :class:`TokenCategory`.
        """
        # 1. Try CoinGecko categories
        if categories:
            lower_cats = {c.lower().strip() for c in categories}
            for keywords, category in _CATEGORY_KEYWORDS:
                if lower_cats & set(keywords):
                    return category

        # 2. Known memecoin symbols
        if symbol.upper() in _KNOWN_MEMECOINS:
            return TokenCategory.MEMECOIN

        return TokenCategory.UNKNOWN

    @staticmethod
    def risk_multiplier(category: TokenCategory) -> float:
        """Return the risk multiplier for a given category.

        Args:
            category: Internal token category.

        Returns:
            Multiplier in (0, 1] to apply to the opportunity score.
        """
        return _RISK_MULTIPLIERS.get(category, _RISK_MULTIPLIERS[TokenCategory.UNKNOWN])
