"""Keyword-based sentiment analyser for social media texts.

Phase 13: simple keyword-counting approach. Phase 15+ can upgrade
to LLM-based sentiment analysis for more accuracy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Keyword lexicons
# ---------------------------------------------------------------------------

_POSITIVE_KEYWORDS: set[str] = {
    "moon", "bullish", "amazing", "great", "pump", "buy", "gem",
    "undervalued", "opportunity", "breakout", "accumulate", "hodl",
    "rally", "surge", "rocket", "profit", "winner", "strong",
    "milestone", "adoption", "growth", "innovative", "promising",
    "upgrade", "partnership", "launch", "mainnet", "airdrop",
}

_NEGATIVE_KEYWORDS: set[str] = {
    "scam", "bearish", "terrible", "crash", "dump", "sell", "rug",
    "overvalued", "fraud", "hack", "exploit", "fear", "panic",
    "bubble", "ponzi", "worst", "dead", "risk", "warning", "collapse",
    "bankrupt", "sec", "lawsuit", "ban", "delisted", "plunge",
}

_WORD_RE = re.compile(r"[a-zA-Z]+")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SentimentResult:
    """Result of sentiment analysis on a batch of texts."""

    score: float  # in [-1.0, 1.0]
    label: str  # "positive" | "negative" | "neutral"
    positive: int  # count of positive texts
    negative: int  # count of negative texts
    neutral: int  # count of neutral texts


# ---------------------------------------------------------------------------
# Analyser
# ---------------------------------------------------------------------------


class SentimentAnalyzer:
    """Keyword-based sentiment analyser.

    Counts positive and negative keyword hits per text, classifies each
    text, and returns an aggregated score in ``[-1.0, 1.0]``.
    """

    @staticmethod
    def _score_text(text: str) -> float:
        """Score a single text. Returns value in roughly [-1, 1]."""
        words = {w.lower() for w in _WORD_RE.findall(text)}
        pos_hits = len(words & _POSITIVE_KEYWORDS)
        neg_hits = len(words & _NEGATIVE_KEYWORDS)
        total = pos_hits + neg_hits
        if total == 0:
            return 0.0
        return (pos_hits - neg_hits) / total

    @classmethod
    def analyse(cls, texts: list[str]) -> SentimentResult:
        """Analyse a batch of texts and return aggregated sentiment.

        Args:
            texts: List of raw text strings (tweets, posts, etc.).

        Returns:
            SentimentResult with score, label, and per-text counts.
        """
        if not texts:
            return SentimentResult(score=0.0, label="neutral", positive=0, negative=0, neutral=0)

        positive = 0
        negative = 0
        neutral = 0
        total_score = 0.0

        for text in texts:
            s = cls._score_text(text)
            total_score += s
            if s > 0.05:
                positive += 1
            elif s < -0.05:
                negative += 1
            else:
                neutral += 1

        avg = total_score / len(texts)
        # Clamp to [-1.0, 1.0]
        avg = max(-1.0, min(1.0, avg))

        if avg > 0.05:
            label = "positive"
        elif avg < -0.05:
            label = "negative"
        else:
            label = "neutral"

        return SentimentResult(
            score=round(avg, 4),
            label=label,
            positive=positive,
            negative=negative,
            neutral=neutral,
        )

    @classmethod
    def analyse_single(cls, text: str) -> SentimentResult:
        """Convenience: analyse a single text.

        Args:
            text: Raw text string.

        Returns:
            SentimentResult.
        """
        return cls.analyse([text])
