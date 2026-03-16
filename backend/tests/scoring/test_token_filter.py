"""TDD tests for TokenFilter — excludes stablecoins, wrapped, and dead tokens.

Addresses Item 1 of the Ranking Quality Loop: filter noise so the ranking
answers 'which altcoins could explode during the next ATH?'
"""


from app.scoring.token_filter import TokenFilter

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestTokenFilterInit:
    """TokenFilter can be created with defaults or custom overrides."""

    def test_token_filter_init_has_stablecoin_set(self) -> None:
        tf = TokenFilter()
        assert "USDT" in tf.stablecoins
        assert "USDC" in tf.stablecoins
        assert "DAI" in tf.stablecoins
        assert "BUSD" in tf.stablecoins
        assert "TUSD" in tf.stablecoins
        assert "FRAX" in tf.stablecoins
        assert "FDUSD" in tf.stablecoins
        assert "USD1" in tf.stablecoins

    def test_token_filter_init_has_wrapped_set(self) -> None:
        tf = TokenFilter()
        assert "WBTC" in tf.wrapped
        assert "WETH" in tf.wrapped
        assert "STETH" in tf.wrapped
        assert "CBETH" in tf.wrapped
        assert "RETH" in tf.wrapped
        assert "WBNB" in tf.wrapped

    def test_token_filter_init_default_volume_threshold(self) -> None:
        tf = TokenFilter()
        assert tf.min_volume_24h == 10_000.0

    def test_token_filter_init_custom_volume_threshold(self) -> None:
        tf = TokenFilter(min_volume_24h=50_000.0)
        assert tf.min_volume_24h == 50_000.0

    def test_token_filter_init_extra_exclude_symbols(self) -> None:
        """Users can pass additional symbols to exclude."""
        tf = TokenFilter(extra_exclude={"SCAM", "RUG"})
        assert "SCAM" in tf.extra_exclude
        assert "RUG" in tf.extra_exclude


# ---------------------------------------------------------------------------
# is_excluded — symbol-based checks
# ---------------------------------------------------------------------------


class TestTokenFilterIsExcluded:
    """is_excluded returns True for stablecoins, wrapped, and custom symbols."""

    def test_is_excluded_stablecoin_usdt(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("USDT") is True

    def test_is_excluded_stablecoin_usdc(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("USDC") is True

    def test_is_excluded_stablecoin_fdusd(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("FDUSD") is True

    def test_is_excluded_stablecoin_usd1(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("USD1") is True

    def test_is_excluded_wrapped_wbtc(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("WBTC") is True

    def test_is_excluded_wrapped_steth(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("STETH") is True

    def test_is_excluded_extra_custom_symbol(self) -> None:
        tf = TokenFilter(extra_exclude={"SCAM"})
        assert tf.is_excluded("SCAM") is True

    def test_is_excluded_case_insensitive(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("usdt") is True
        assert tf.is_excluded("Usdt") is True
        assert tf.is_excluded("wbtc") is True

    def test_is_excluded_normal_token_returns_false(self) -> None:
        tf = TokenFilter()
        assert tf.is_excluded("BTC") is False
        assert tf.is_excluded("ETH") is False
        assert tf.is_excluded("SOL") is False
        assert tf.is_excluded("AVAX") is False


# ---------------------------------------------------------------------------
# is_dead — volume-based check
# ---------------------------------------------------------------------------


class TestTokenFilterIsDead:
    """is_dead returns True when 24h volume is below threshold."""

    def test_is_dead_zero_volume(self) -> None:
        tf = TokenFilter()
        assert tf.is_dead(volume_24h=0.0) is True

    def test_is_dead_below_threshold(self) -> None:
        tf = TokenFilter(min_volume_24h=10_000.0)
        assert tf.is_dead(volume_24h=5_000.0) is True

    def test_is_dead_at_threshold(self) -> None:
        tf = TokenFilter(min_volume_24h=10_000.0)
        assert tf.is_dead(volume_24h=10_000.0) is False

    def test_is_dead_above_threshold(self) -> None:
        tf = TokenFilter(min_volume_24h=10_000.0)
        assert tf.is_dead(volume_24h=500_000.0) is False

    def test_is_dead_none_volume_treated_as_dead(self) -> None:
        tf = TokenFilter()
        assert tf.is_dead(volume_24h=None) is True

    def test_is_dead_custom_threshold(self) -> None:
        tf = TokenFilter(min_volume_24h=100_000.0)
        assert tf.is_dead(volume_24h=50_000.0) is True
        assert tf.is_dead(volume_24h=100_000.0) is False


# ---------------------------------------------------------------------------
# should_exclude — combined check (symbol + volume)
# ---------------------------------------------------------------------------


class TestTokenFilterShouldExclude:
    """should_exclude combines symbol + volume checks."""

    def test_should_exclude_stablecoin_regardless_of_volume(self) -> None:
        tf = TokenFilter()
        assert tf.should_exclude(symbol="USDT", volume_24h=1_000_000_000.0) is True

    def test_should_exclude_wrapped_regardless_of_volume(self) -> None:
        tf = TokenFilter()
        assert tf.should_exclude(symbol="WBTC", volume_24h=500_000_000.0) is True

    def test_should_exclude_dead_token(self) -> None:
        tf = TokenFilter()
        assert tf.should_exclude(symbol="OBSCURE", volume_24h=100.0) is True

    def test_should_exclude_healthy_altcoin_returns_false(self) -> None:
        tf = TokenFilter()
        assert tf.should_exclude(symbol="SOL", volume_24h=2_000_000.0) is False

    def test_should_exclude_healthy_altcoin_none_volume_excluded(self) -> None:
        """If volume data is missing we can't trust the token."""
        tf = TokenFilter()
        assert tf.should_exclude(symbol="UNKNOWN", volume_24h=None) is True


# ---------------------------------------------------------------------------
# excluded_symbols — convenience property
# ---------------------------------------------------------------------------


class TestTokenFilterExcludedSymbols:
    """excluded_symbols returns the full frozen set union."""

    def test_excluded_symbols_includes_all_categories(self) -> None:
        tf = TokenFilter(extra_exclude={"SCAM"})
        syms = tf.excluded_symbols
        assert "USDT" in syms  # stablecoin
        assert "WBTC" in syms  # wrapped
        assert "SCAM" in syms  # extra

    def test_excluded_symbols_is_frozen_set(self) -> None:
        tf = TokenFilter()
        assert isinstance(tf.excluded_symbols, frozenset)
