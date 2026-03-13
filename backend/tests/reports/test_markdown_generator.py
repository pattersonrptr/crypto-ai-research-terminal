"""Tests for MarkdownGenerator — renders Markdown reports using Jinja2.

TDD RED phase: Tests written before implementation.
"""

from datetime import datetime
from pathlib import Path

import pytest

from app.reports.markdown_generator import MarkdownGenerator


class TestMarkdownGeneratorInit:
    """Test MarkdownGenerator initialization."""

    def test_init_creates_instance(self) -> None:
        """MarkdownGenerator can be initialized."""
        generator = MarkdownGenerator()
        assert generator is not None

    def test_init_loads_jinja_environment(self) -> None:
        """MarkdownGenerator loads Jinja2 environment."""
        generator = MarkdownGenerator()
        assert hasattr(generator, "env")

    def test_init_with_custom_template_path(self) -> None:
        """MarkdownGenerator accepts custom template path."""
        custom_path = Path(__file__).parent / "templates"
        generator = MarkdownGenerator(template_path=custom_path)
        assert generator is not None


class TestMarkdownGeneratorMethods:
    """Test MarkdownGenerator has required methods."""

    def test_has_generate_token_report_method(self) -> None:
        """Generator has generate_token_report method."""
        generator = MarkdownGenerator()
        assert hasattr(generator, "generate_token_report")
        assert callable(generator.generate_token_report)

    def test_has_generate_market_report_method(self) -> None:
        """Generator has generate_market_report method."""
        generator = MarkdownGenerator()
        assert hasattr(generator, "generate_market_report")
        assert callable(generator.generate_market_report)


class TestGenerateTokenReport:
    """Test MarkdownGenerator.generate_token_report method."""

    def test_generate_token_report_returns_markdown(self) -> None:
        """generate_token_report returns Markdown string."""
        generator = MarkdownGenerator()
        data = {
            "symbol": "BTC",
            "name": "Bitcoin",
            "price_usd": 45000.50,
            "market_cap_usd": 880_000_000_000,
            "volume_24h_usd": 25_000_000_000,
            "listing_score": 0,  # BTC already listed everywhere
            "risk_score": 0.05,
            "whale_score": 7.5,
            "generated_at": datetime(2024, 1, 15, 12, 0, 0),
        }

        result = generator.generate_token_report(data)

        assert isinstance(result, str)
        assert "# Bitcoin (BTC)" in result or "Bitcoin" in result
        assert "45,000" in result or "45000" in result

    def test_generate_token_report_contains_sections(self) -> None:
        """Token report contains expected sections."""
        generator = MarkdownGenerator()
        data = {
            "symbol": "ETH",
            "name": "Ethereum",
            "price_usd": 2500.00,
            "market_cap_usd": 300_000_000_000,
            "volume_24h_usd": 15_000_000_000,
            "listing_score": 0,
            "risk_score": 0.08,
            "whale_score": 8.0,
            "signals": ["Active development", "Strong community"],
            "risk_factors": [],
            "generated_at": datetime(2024, 1, 15, 12, 0, 0),
        }

        result = generator.generate_token_report(data)

        # Should have main sections
        assert "Market Data" in result or "market" in result.lower()
        assert "Risk" in result or "risk" in result.lower()

    def test_generate_token_report_with_signals(self) -> None:
        """Token report includes signals when provided."""
        generator = MarkdownGenerator()
        data = {
            "symbol": "SOL",
            "name": "Solana",
            "price_usd": 100.00,
            "market_cap_usd": 45_000_000_000,
            "volume_24h_usd": 2_000_000_000,
            "listing_score": 85,
            "risk_score": 0.15,
            "whale_score": 6.5,
            "signals": ["DEX volume up 250%", "Social mentions growing"],
            "generated_at": datetime(2024, 1, 15, 12, 0, 0),
        }

        result = generator.generate_token_report(data)

        assert "DEX volume" in result or "Signal" in result

    def test_generate_token_report_with_risk_factors(self) -> None:
        """Token report includes risk factors when provided."""
        generator = MarkdownGenerator()
        data = {
            "symbol": "SCAM",
            "name": "Scam Token",
            "price_usd": 0.001,
            "market_cap_usd": 1_000_000,
            "volume_24h_usd": 50_000,
            "listing_score": 10,
            "risk_score": 0.85,
            "whale_score": 2.0,
            "signals": [],
            "risk_factors": ["No liquidity lock", "Anonymous team"],
            "generated_at": datetime(2024, 1, 15, 12, 0, 0),
        }

        result = generator.generate_token_report(data)

        assert "liquidity" in result.lower() or "Risk" in result


class TestGenerateMarketReport:
    """Test MarkdownGenerator.generate_market_report method."""

    def test_generate_market_report_returns_markdown(self) -> None:
        """generate_market_report returns Markdown string."""
        generator = MarkdownGenerator()
        data = {
            "date": datetime(2024, 1, 15),
            "market_sentiment": "bullish",
            "total_market_cap_usd": 1_800_000_000_000,
            "btc_dominance_pct": 52.5,
            "top_opportunities": [
                {"symbol": "SOL", "name": "Solana", "score": 0.85},
                {"symbol": "AVAX", "name": "Avalanche", "score": 0.78},
            ],
            "active_alerts_count": 5,
            "emerging_narratives": ["AI", "RWA"],
        }

        result = generator.generate_market_report(data)

        assert isinstance(result, str)
        assert "2024" in result or "January" in result

    def test_generate_market_report_contains_sections(self) -> None:
        """Market report contains expected sections."""
        generator = MarkdownGenerator()
        data = {
            "date": datetime(2024, 1, 15),
            "market_sentiment": "neutral",
            "total_market_cap_usd": 1_700_000_000_000,
            "btc_dominance_pct": 51.0,
            "top_opportunities": [
                {"symbol": "ETH", "name": "Ethereum", "score": 0.72},
            ],
            "active_alerts_count": 3,
            "emerging_narratives": ["DeFi 2.0"],
        }

        result = generator.generate_market_report(data)

        # Should have market overview
        assert "Market" in result or "market" in result.lower()

    def test_generate_market_report_with_opportunities(self) -> None:
        """Market report lists top opportunities."""
        generator = MarkdownGenerator()
        data = {
            "date": datetime(2024, 1, 15),
            "market_sentiment": "bullish",
            "total_market_cap_usd": 2_000_000_000_000,
            "btc_dominance_pct": 48.5,
            "top_opportunities": [
                {"symbol": "INJ", "name": "Injective", "score": 0.92},
                {"symbol": "TIA", "name": "Celestia", "score": 0.88},
                {"symbol": "SEI", "name": "Sei", "score": 0.82},
            ],
            "active_alerts_count": 8,
            "emerging_narratives": ["Modular blockchains"],
        }

        result = generator.generate_market_report(data)

        assert "INJ" in result or "Injective" in result

    def test_generate_market_report_with_narratives(self) -> None:
        """Market report includes emerging narratives."""
        generator = MarkdownGenerator()
        data = {
            "date": datetime(2024, 1, 15),
            "market_sentiment": "bullish",
            "total_market_cap_usd": 1_900_000_000_000,
            "btc_dominance_pct": 50.0,
            "top_opportunities": [],
            "active_alerts_count": 2,
            "emerging_narratives": ["AI Agents", "DePIN", "RWA Tokenization"],
        }

        result = generator.generate_market_report(data)

        assert "AI" in result or "narrative" in result.lower()


class TestMarkdownGeneratorEdgeCases:
    """Test edge cases in MarkdownGenerator."""

    def test_generate_token_report_with_missing_optional_fields(self) -> None:
        """Token report handles missing optional fields gracefully."""
        generator = MarkdownGenerator()
        data = {
            "symbol": "TEST",
            "name": "Test Token",
            "price_usd": 1.00,
            "market_cap_usd": 1_000_000,
            "volume_24h_usd": 100_000,
            "listing_score": 50,
            "risk_score": 0.3,
            "whale_score": 5.0,
            "generated_at": datetime(2024, 1, 15, 12, 0, 0),
            # No signals or risk_factors
        }

        result = generator.generate_token_report(data)

        assert isinstance(result, str)
        assert "TEST" in result

    def test_generate_market_report_with_empty_opportunities(self) -> None:
        """Market report handles empty opportunities list."""
        generator = MarkdownGenerator()
        data = {
            "date": datetime(2024, 1, 15),
            "market_sentiment": "bearish",
            "total_market_cap_usd": 1_500_000_000_000,
            "btc_dominance_pct": 55.0,
            "top_opportunities": [],
            "active_alerts_count": 0,
            "emerging_narratives": [],
        }

        result = generator.generate_market_report(data)

        assert isinstance(result, str)

    def test_generate_token_report_formats_large_numbers(self) -> None:
        """Token report formats large numbers readably."""
        generator = MarkdownGenerator()
        data = {
            "symbol": "BTC",
            "name": "Bitcoin",
            "price_usd": 67890.12,
            "market_cap_usd": 1_300_000_000_000,
            "volume_24h_usd": 45_000_000_000,
            "listing_score": 0,
            "risk_score": 0.02,
            "whale_score": 9.0,
            "generated_at": datetime(2024, 1, 15, 12, 0, 0),
        }

        result = generator.generate_token_report(data)

        # Should have some readable formatting (commas, abbreviations, etc.)
        assert "1.3" in result or "1,300" in result or "trillion" in result.lower()
