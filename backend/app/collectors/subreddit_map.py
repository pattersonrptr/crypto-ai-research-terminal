"""Symbol-to-subreddit mapping for Reddit social data collection.

Maps token symbols to their primary subreddit names. Tokens without
a known subreddit are skipped during Reddit collection.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Mapping: symbol → subreddit name (without r/ prefix)
# ---------------------------------------------------------------------------

SYMBOL_TO_SUBREDDIT: dict[str, str] = {
    "BTC": "Bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "AVAX": "Avax",
    "MATIC": "maticnetwork",
    "LINK": "Chainlink",
    "UNI": "Uniswap",
    "AAVE": "Aave",
    "ARB": "arbitrum",
    "OP": "optimismCollective",
    "DOT": "dot",
    "ADA": "cardano",
    "ATOM": "cosmosnetwork",
    "NEAR": "nearprotocol",
    "FTM": "FantomFoundation",
    "ALGO": "AlgorandOfficial",
    "XRP": "XRP",
    "BNB": "bnbchainofficial",
    "TRX": "Tronix",
    "DOGE": "dogecoin",
    "SHIB": "SHIBArmy",
    "LTC": "litecoin",
    "XMR": "Monero",
    "FIL": "filecoin",
    "INJ": "injective",
    "TIA": "CelestiaNetwork",
    "SUI": "SuiNetwork",
    "APT": "AptosNetwork",
    "SEI": "SeiNetwork",
    "RNDR": "RenderNetwork",
    "FET": "FetchAI_Community",
    "TAO": "bittensor_",
    "JUP": "JupiterExchange",
    "WLD": "worldcoin",
}


def get_subreddit(symbol: str) -> str | None:
    """Return the subreddit name for a token symbol, or None if unknown.

    Args:
        symbol: Uppercase token symbol (e.g. ``"BTC"``).

    Returns:
        Subreddit name (without ``r/`` prefix), or ``None``.
    """
    return SYMBOL_TO_SUBREDDIT.get(symbol.upper())
