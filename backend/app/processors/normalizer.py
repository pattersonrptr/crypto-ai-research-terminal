"""Normalizer — min-max normalisation helpers used across all scoring modules."""


def clamp(value: float, low: float, high: float) -> float:
    """Restrict *value* to the closed interval [low, high]."""
    return max(low, min(high, value))


def min_max_normalize(value: float, min_val: float, max_val: float) -> float:
    """Map *value* to [0, 1] using min-max scaling.

    Returns 0.0 when ``min_val == max_val`` to avoid division by zero.
    Values outside [min_val, max_val] are clamped to [0, 1].
    """
    if max_val == min_val:
        return 0.0
    raw = (value - min_val) / (max_val - min_val)
    return clamp(raw, 0.0, 1.0)


def normalize_series(values: list[float]) -> list[float]:
    """Apply min-max normalisation to every element of *values*.

    Returns an empty list if *values* is empty.
    All-equal series maps every element to 0.0.
    """
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    return [min_max_normalize(v, min_val, max_val) for v in values]
