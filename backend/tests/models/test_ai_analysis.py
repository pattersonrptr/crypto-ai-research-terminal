"""Tests for AiAnalysis ORM model."""

from __future__ import annotations

from app.models.ai_analysis import AiAnalysis


class TestAiAnalysisModel:
    """AiAnalysis ORM model has the expected fields and tablename."""

    def test_tablename_is_ai_analyses(self) -> None:
        assert AiAnalysis.__tablename__ == "ai_analyses"

    def test_model_has_required_columns(self) -> None:
        analysis = AiAnalysis(
            token_id=1,
            analysis_type="summary",
            content="Bitcoin is a decentralized digital currency.",
            model_used="ollama/llama3",
        )
        assert analysis.token_id == 1
        assert analysis.analysis_type == "summary"
        assert analysis.content == "Bitcoin is a decentralized digital currency."
        assert analysis.model_used == "ollama/llama3"

    def test_repr_contains_class_name_and_type(self) -> None:
        analysis = AiAnalysis(
            id=42,
            token_id=1,
            analysis_type="summary",
            content="text",
            model_used="ollama/llama3",
        )
        r = repr(analysis)
        assert "AiAnalysis" in r
        assert "42" in r
