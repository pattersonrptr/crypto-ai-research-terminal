#!/usr/bin/env python3
"""Seed the database with sample data for testing the API.

Usage:
    python -m scripts.seed_data
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.token import Token
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.signal import Signal


# Sample tokens data (top cryptos)
SAMPLE_TOKENS = [
    {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum"},
    {"symbol": "SOL", "name": "Solana", "coingecko_id": "solana"},
    {"symbol": "AVAX", "name": "Avalanche", "coingecko_id": "avalanche-2"},
    {"symbol": "MATIC", "name": "Polygon", "coingecko_id": "matic-network"},
    {"symbol": "LINK", "name": "Chainlink", "coingecko_id": "chainlink"},
    {"symbol": "UNI", "name": "Uniswap", "coingecko_id": "uniswap"},
    {"symbol": "AAVE", "name": "Aave", "coingecko_id": "aave"},
    {"symbol": "ARB", "name": "Arbitrum", "coingecko_id": "arbitrum"},
    {"symbol": "OP", "name": "Optimism", "coingecko_id": "optimism"},
]

# Sample market data (realistic-ish prices)
SAMPLE_MARKET_DATA = {
    "BTC": {"price": 67500.0, "market_cap": 1320000000000, "volume_24h": 28500000000, "change_24h": 2.3},
    "ETH": {"price": 3450.0, "market_cap": 415000000000, "volume_24h": 15200000000, "change_24h": 1.8},
    "SOL": {"price": 142.0, "market_cap": 62000000000, "volume_24h": 2800000000, "change_24h": 4.5},
    "AVAX": {"price": 35.50, "market_cap": 13500000000, "volume_24h": 520000000, "change_24h": 3.2},
    "MATIC": {"price": 0.72, "market_cap": 7100000000, "volume_24h": 380000000, "change_24h": -1.2},
    "LINK": {"price": 14.80, "market_cap": 8700000000, "volume_24h": 450000000, "change_24h": 2.8},
    "UNI": {"price": 9.20, "market_cap": 5500000000, "volume_24h": 180000000, "change_24h": 1.5},
    "AAVE": {"price": 92.0, "market_cap": 1350000000, "volume_24h": 120000000, "change_24h": 5.2},
    "ARB": {"price": 1.15, "market_cap": 3800000000, "volume_24h": 420000000, "change_24h": 6.8},
    "OP": {"price": 2.45, "market_cap": 2600000000, "volume_24h": 280000000, "change_24h": 4.1},
}

# Sample scores (opportunity scores)
SAMPLE_SCORES = {
    "BTC": {"fundamental": 0.92, "growth": 0.65, "opportunity": 0.78, "risk": 0.15},
    "ETH": {"fundamental": 0.95, "growth": 0.72, "opportunity": 0.82, "risk": 0.12},
    "SOL": {"fundamental": 0.78, "growth": 0.88, "opportunity": 0.85, "risk": 0.28},
    "AVAX": {"fundamental": 0.72, "growth": 0.75, "opportunity": 0.74, "risk": 0.32},
    "MATIC": {"fundamental": 0.70, "growth": 0.55, "opportunity": 0.62, "risk": 0.35},
    "LINK": {"fundamental": 0.85, "growth": 0.68, "opportunity": 0.76, "risk": 0.22},
    "UNI": {"fundamental": 0.75, "growth": 0.52, "opportunity": 0.64, "risk": 0.30},
    "AAVE": {"fundamental": 0.82, "growth": 0.78, "opportunity": 0.80, "risk": 0.25},
    "ARB": {"fundamental": 0.68, "growth": 0.92, "opportunity": 0.88, "risk": 0.38},
    "OP": {"fundamental": 0.65, "growth": 0.85, "opportunity": 0.82, "risk": 0.40},
}


async def seed_database(database_url: str) -> None:
    """Seed the database with sample data."""
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM tokens"))
        count = result.scalar()
        if count and count > 0:
            print(f"Database already has {count} tokens. Skipping seed.")
            return

        print("Seeding database with sample data...")
        now = datetime.now(timezone.utc)

        # Insert tokens
        tokens = {}
        for token_data in SAMPLE_TOKENS:
            token = Token(**token_data)
            session.add(token)
            tokens[token_data["symbol"]] = token

        await session.flush()  # Get IDs assigned
        print(f"  ✓ Added {len(tokens)} tokens")

        # Insert market data
        for symbol, data in SAMPLE_MARKET_DATA.items():
            if symbol in tokens:
                market = MarketData(
                    token_id=tokens[symbol].id,
                    price_usd=data["price"],
                    market_cap_usd=data["market_cap"],
                    volume_24h_usd=data["volume_24h"],
                    collected_at=now,
                )
                session.add(market)
        print(f"  ✓ Added market data for {len(SAMPLE_MARKET_DATA)} tokens")

        # Insert scores
        for symbol, scores in SAMPLE_SCORES.items():
            if symbol in tokens:
                score = TokenScore(
                    token_id=tokens[symbol].id,
                    fundamental_score=scores["fundamental"],
                    opportunity_score=scores["opportunity"],
                    scored_at=now,
                )
                session.add(score)
        print(f"  ✓ Added scores for {len(SAMPLE_SCORES)} tokens")

        # Insert sample signals
        sample_signals = [
            {"token": "ARB", "type": "listing", "value": 0.85},
            {"token": "SOL", "type": "whale_accumulation", "value": 0.78},
            {"token": "AAVE", "type": "dev_activity", "value": 0.72},
            {"token": "OP", "type": "social_momentum", "value": 0.68},
        ]
        for sig in sample_signals:
            if sig["token"] in tokens:
                signal = Signal(
                    token_id=tokens[sig["token"]].id,
                    signal_type=sig["type"],
                    value=sig["value"],
                    generated_at=now - timedelta(hours=2),
                )
                session.add(signal)
        print(f"  ✓ Added {len(sample_signals)} sample signals")

        await session.commit()
        print("\n✅ Database seeded successfully!")


async def main() -> None:
    """Entry point."""
    # Use the same DATABASE_URL format as the app
    import os
    from dotenv import load_dotenv

    load_dotenv()

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cryptoai:cryptoai@localhost:5433/cryptoai"
    )
    
    # Ensure we're using asyncpg
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Connecting to: {database_url.split('@')[1] if '@' in database_url else database_url}")
    await seed_database(database_url)


if __name__ == "__main__":
    asyncio.run(main())
