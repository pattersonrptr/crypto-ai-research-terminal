"""TDD tests for SentimentAnalyzer — keyword-based sentiment scoring."""

from __future__ import annotations

from app.processors.sentiment_analyzer import SentimentAnalyzer, SentimentResult


class TestSentimentResult:
    """Tests for the SentimentResult dataclass."""

    def test_sentiment_result_has_score(self) -> None:
        """SentimentResult must have a score float."""
        result = SentimentResult(score=0.5, label="positive", positive=3, negative=1, neutral=2)
        assert result.score == 0.5

    def test_sentiment_result_has_label(self) -> None:
        """SentimentResult must have a label string."""
        result = SentimentResult(score=0.5, label="positive", positive=3, negative=1, neutral=2)
        assert result.label == "positive"

    def test_sentiment_result_has_counts(self) -> None:
        """SentimentResult must have positive, negative, neutral counts."""
        result = SentimentResult(score=0.0, label="neutral", positive=0, negative=0, neutral=5)
        assert result.positive == 0
        assert result.negative == 0
        assert result.neutral == 5


class TestSentimentAnalyzer:
    """Tests for the keyword-based SentimentAnalyzer."""

    def test_empty_texts_returns_neutral(self) -> None:
        """analyse([]) must return neutral with score 0.0."""
        result = SentimentAnalyzer.analyse([])
        assert result.score == 0.0
        assert result.label == "neutral"

    def test_positive_texts_return_positive(self) -> None:
        """Texts with bullish keywords must return positive score > 0."""
        texts = [
            "BTC is going to the moon! Great opportunity!",
            "Super bullish on this project, amazing team!",
        ]
        result = SentimentAnalyzer.analyse(texts)
        assert result.score > 0
        assert result.label == "positive"

    def test_negative_texts_return_negative(self) -> None:
        """Texts with bearish keywords must return negative score < 0."""
        texts = [
            "This is a scam, terrible project!",
            "Crash incoming, dump everything. Worst investment.",
        ]
        result = SentimentAnalyzer.analyse(texts)
        assert result.score < 0
        assert result.label == "negative"

    def test_neutral_texts_return_neutral(self) -> None:
        """Texts without strong keywords must return neutral."""
        texts = [
            "The market traded at $65000 today.",
            "Volume was average this week.",
        ]
        result = SentimentAnalyzer.analyse(texts)
        assert result.label == "neutral"

    def test_mixed_texts_return_balanced_score(self) -> None:
        """Mix of positive and negative texts must average out."""
        texts = [
            "Absolutely amazing, bullish!",  # +positive
            "Terrible scam, sell everything!",  # +negative
        ]
        result = SentimentAnalyzer.analyse(texts)
        # score should be closer to 0 than to extremes
        assert -0.6 < result.score < 0.6

    def test_score_range_bounded(self) -> None:
        """Score must always be in [-1.0, 1.0] range."""
        texts = ["moon moon moon bullish bullish amazing " * 10]
        result = SentimentAnalyzer.analyse(texts)
        assert -1.0 <= result.score <= 1.0

    def test_analyse_single_convenience(self) -> None:
        """analyse_single(text) must work as a convenience wrapper."""
        result = SentimentAnalyzer.analyse_single("BTC to the moon!")
        assert result.score > 0

    def test_counts_are_correct(self) -> None:
        """Positive/negative/neutral counts must sum to total texts."""
        texts = [
            "Bullish!",
            "Terrible!",
            "The market is open.",
        ]
        result = SentimentAnalyzer.analyse(texts)
        assert result.positive + result.negative + result.neutral == 3
