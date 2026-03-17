"""TDD tests for TokenCategoryClassifier — category tagging + risk multiplier.

Classifies tokens into internal categories (memecoin, L1, L2, DeFi, etc.)
and applies a risk multiplier to the final opportunity score.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

import pytest

from app.scoring.token_category import (
    TokenCategory,
    TokenCategoryClassifier,
)


class TestTokenCategoryEnum:
    """TokenCategory enum holds all internal categories."""

    def test_category_has_memecoin(self) -> None:
        assert TokenCategory.MEMECOIN.value == "memecoin"

    def test_category_has_l1(self) -> None:
        assert TokenCategory.L1.value == "l1"

    def test_category_has_l2(self) -> None:
        assert TokenCategory.L2.value == "l2"

    def test_category_has_defi(self) -> None:
        assert TokenCategory.DEFI.value == "defi"

    def test_category_has_infrastructure(self) -> None:
        assert TokenCategory.INFRASTRUCTURE.value == "infrastructure"

    def test_category_has_unknown(self) -> None:
        assert TokenCategory.UNKNOWN.value == "unknown"


class TestTokenCategoryClassifierFromCategories:
    """Classify tokens using CoinGecko category strings."""

    def test_classify_meme_category_returns_memecoin(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="PEPE",
            categories=["Meme", "Ethereum Ecosystem"],
        )
        assert result == TokenCategory.MEMECOIN

    def test_classify_dog_themed_returns_memecoin(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="DOGE",
            categories=["Dog-Themed", "Proof of Work"],
        )
        assert result == TokenCategory.MEMECOIN

    def test_classify_political_memes_returns_memecoin(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="TRUMP",
            categories=["Political Memes", "Solana Ecosystem"],
        )
        assert result == TokenCategory.MEMECOIN

    def test_classify_layer1_returns_l1(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="ETH",
            categories=["Smart Contract Platform", "Layer 1 (L1)"],
        )
        assert result == TokenCategory.L1

    def test_classify_layer2_returns_l2(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="ARB",
            categories=["Layer 2 (L2)", "Ethereum Ecosystem"],
        )
        assert result == TokenCategory.L2

    def test_classify_defi_returns_defi(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="UNI",
            categories=["Decentralized Finance (DeFi)", "Ethereum Ecosystem"],
        )
        assert result == TokenCategory.DEFI

    def test_classify_infrastructure_returns_infrastructure(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="LINK",
            categories=["Oracle", "Ethereum Ecosystem"],
        )
        assert result == TokenCategory.INFRASTRUCTURE

    def test_classify_no_categories_unknown_symbol_returns_unknown(self) -> None:
        result = TokenCategoryClassifier.classify(
            symbol="NEWTOKEN",
            categories=[],
        )
        assert result == TokenCategory.UNKNOWN


class TestTokenCategoryClassifierFromSymbol:
    """Fallback classification by known symbol when no CoinGecko categories exist."""

    def test_classify_known_memecoin_symbol_shib(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="SHIB", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_known_memecoin_symbol_pepe(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="PEPE", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_known_memecoin_symbol_doge(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="DOGE", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_known_memecoin_symbol_fartcoin(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="FARTCOIN", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_known_memecoin_symbol_trump(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="TRUMP", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_known_memecoin_symbol_bonk(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="BONK", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_known_memecoin_symbol_floki(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="FLOKI", categories=[])
        assert result == TokenCategory.MEMECOIN

    def test_classify_symbol_case_insensitive(self) -> None:
        result = TokenCategoryClassifier.classify(symbol="pepe", categories=[])
        assert result == TokenCategory.MEMECOIN


class TestTokenCategoryRiskMultiplier:
    """Risk multiplier per category — adjusts final opportunity score."""

    def test_memecoin_multiplier_below_one(self) -> None:
        mult = TokenCategoryClassifier.risk_multiplier(TokenCategory.MEMECOIN)
        assert mult == pytest.approx(0.70)

    def test_l1_multiplier_is_one(self) -> None:
        mult = TokenCategoryClassifier.risk_multiplier(TokenCategory.L1)
        assert mult == pytest.approx(1.0)

    def test_l2_multiplier_is_one(self) -> None:
        mult = TokenCategoryClassifier.risk_multiplier(TokenCategory.L2)
        assert mult == pytest.approx(1.0)

    def test_defi_multiplier_is_one(self) -> None:
        mult = TokenCategoryClassifier.risk_multiplier(TokenCategory.DEFI)
        assert mult == pytest.approx(0.95)

    def test_infrastructure_multiplier_is_one(self) -> None:
        mult = TokenCategoryClassifier.risk_multiplier(TokenCategory.INFRASTRUCTURE)
        assert mult == pytest.approx(1.0)

    def test_unknown_multiplier_slight_penalty(self) -> None:
        mult = TokenCategoryClassifier.risk_multiplier(TokenCategory.UNKNOWN)
        assert mult == pytest.approx(0.90)

    def test_apply_multiplier_reduces_memecoin_score(self) -> None:
        """A memecoin with score 0.80 should become 0.56 after multiplier."""
        base = 0.80
        adjusted = base * TokenCategoryClassifier.risk_multiplier(TokenCategory.MEMECOIN)
        assert adjusted == pytest.approx(0.56)

    def test_apply_multiplier_l1_score_unchanged(self) -> None:
        """An L1 with score 0.80 should stay 0.80."""
        base = 0.80
        adjusted = base * TokenCategoryClassifier.risk_multiplier(TokenCategory.L1)
        assert adjusted == pytest.approx(0.80)
