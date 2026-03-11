"""Smoke test for BaseCollector."""

from app.collectors.base_collector import BaseCollector


class ConcreteCollector(BaseCollector):
    """Minimal concrete implementation for testing."""

    async def collect(self, symbols: list[str]) -> list[dict]:  # type: ignore[override]
        return []

    async def collect_single(self, symbol: str) -> dict:  # type: ignore[override]
        return {}


def test_base_collector_instantiation() -> None:
    """BaseCollector subclass must be instantiable."""
    collector = ConcreteCollector(base_url="https://example.com")
    assert collector.base_url == "https://example.com"
