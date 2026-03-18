"""Tests for Token.category column (Phase 15).

Verifies the Token model has a `category` column that is:
- VARCHAR(50)
- nullable (tokens without CoinGecko categories get NULL)
- indexed (for efficient category-based filtering)
"""

from sqlalchemy import inspect
from sqlalchemy.types import String

from app.db.base import Base
from app.models.token import Token


class TestTokenCategoryColumn:
    """Token model must have a `category` column for CoinGecko-derived categories."""

    def test_token_model_has_category_column(self) -> None:
        mapper = inspect(Token)
        column_names = {col.key for col in mapper.mapper.column_attrs}
        assert "category" in column_names

    def test_token_category_column_is_string_50(self) -> None:
        mapper = inspect(Token)
        category_col = mapper.mapper.columns["category"]
        assert isinstance(category_col.type, String)
        assert category_col.type.length == 50

    def test_token_category_column_is_nullable(self) -> None:
        mapper = inspect(Token)
        category_col = mapper.mapper.columns["category"]
        assert category_col.nullable is True

    def test_token_category_column_is_indexed(self) -> None:
        table = Token.__table__
        indexed_columns = set()
        for idx in table.indexes:
            for col in idx.columns:
                indexed_columns.add(col.name)
        assert "category" in indexed_columns

    def test_token_category_defaults_to_none(self) -> None:
        token = Token(symbol="TEST", name="Test Token", coingecko_id="test-token")
        assert token.category is None

    def test_token_category_can_be_set(self) -> None:
        token = Token(symbol="BTC", name="Bitcoin", coingecko_id="bitcoin")
        token.category = "l1"
        assert token.category == "l1"

    def test_token_repr_still_works_with_category(self) -> None:
        token = Token(symbol="ETH", name="Ethereum", coingecko_id="ethereum")
        token.category = "l1"
        repr_str = repr(token)
        assert "ETH" in repr_str

    def test_token_model_category_in_base_metadata(self) -> None:
        """category column is registered in Base.metadata for Alembic."""
        tokens_table = Base.metadata.tables["tokens"]
        assert "category" in tokens_table.columns
