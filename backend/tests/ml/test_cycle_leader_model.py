"""Tests for ml/cycle_leader_model.py — TDD Red phase.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

import pytest

from app.ml.cycle_leader_model import CycleLeaderModel, TrainingResult
from app.ml.feature_builder import FeatureBuilder, RawTokenData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw(symbol: str, score: float = 0.5) -> RawTokenData:
    """Return a minimal but realistic RawTokenData for training/inference."""
    return RawTokenData(
        symbol=symbol,
        market_cap_usd=1_000_000_000.0 * score,
        volume_24h_usd=50_000_000.0 * score,
        price_usd=10.0 * score,
        ath_usd=20.0,
        commits_30d=int(100 * score),
        contributors=int(30 * score),
        stars=int(5000 * score),
        forks=int(500 * score),
        reddit_subscribers=int(100_000 * score),
        reddit_posts_24h=int(50 * score),
        sentiment_score=score * 0.8,
        fundamental_score=score,
        opportunity_score=score * 0.9,
    )


def _make_training_set(n: int = 30) -> tuple[list[RawTokenData], list[float]]:
    """Return n synthetic training samples with labels in {0.0, 1.0}."""
    builder = FeatureBuilder()
    data: list[RawTokenData] = []
    labels: list[float] = []
    for i in range(n):
        score = (i + 1) / n
        raw = _make_raw(f"TOK{i}", score)
        data.append(raw)
        labels.append(1.0 if score >= 0.5 else 0.0)
    return data, labels


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


class TestCycleLeaderModelInit:
    def test_model_creation_with_defaults_succeeds(self) -> None:
        """CycleLeaderModel() must instantiate without errors."""
        model = CycleLeaderModel()
        assert model is not None

    def test_model_is_not_trained_after_init(self) -> None:
        """A freshly created model must report is_trained == False."""
        model = CycleLeaderModel()
        assert model.is_trained is False


# ---------------------------------------------------------------------------
# predict — before training
# ---------------------------------------------------------------------------


class TestCycleLeaderModelPredictUntrained:
    def test_predict_without_training_raises_runtime_error(self) -> None:
        """predict() on an untrained model must raise RuntimeError."""
        model = CycleLeaderModel()
        raw = _make_raw("SOL")
        fv = FeatureBuilder().build(raw)
        with pytest.raises(RuntimeError, match="not trained"):
            model.predict(fv)


# ---------------------------------------------------------------------------
# train
# ---------------------------------------------------------------------------


class TestCycleLeaderModelTrain:
    def test_train_sets_is_trained_true(self) -> None:
        """After train(), is_trained must be True."""
        model = CycleLeaderModel()
        data, labels = _make_training_set()
        model.train(data, labels)
        assert model.is_trained is True

    def test_train_returns_training_result(self) -> None:
        """train() must return a TrainingResult dataclass."""
        model = CycleLeaderModel()
        data, labels = _make_training_set()
        result = model.train(data, labels)
        assert isinstance(result, TrainingResult)

    def test_train_result_has_accuracy_between_0_and_1(self) -> None:
        """TrainingResult.accuracy must be in [0, 1]."""
        model = CycleLeaderModel()
        data, labels = _make_training_set()
        result = model.train(data, labels)
        assert 0.0 <= result.accuracy <= 1.0

    def test_train_result_has_feature_importances(self) -> None:
        """TrainingResult.feature_importances must be a non-empty dict."""
        model = CycleLeaderModel()
        data, labels = _make_training_set()
        result = model.train(data, labels)
        assert isinstance(result.feature_importances, dict)
        assert len(result.feature_importances) > 0

    def test_train_result_records_n_samples(self) -> None:
        """TrainingResult.n_samples must equal the number of training rows."""
        model = CycleLeaderModel()
        data, labels = _make_training_set(20)
        result = model.train(data, labels)
        assert result.n_samples == 20

    def test_train_with_mismatched_labels_raises_value_error(self) -> None:
        """train() must raise ValueError when len(data) != len(labels)."""
        model = CycleLeaderModel()
        data, labels = _make_training_set(10)
        with pytest.raises(ValueError, match="must have the same length"):
            model.train(data, labels[:5])


# ---------------------------------------------------------------------------
# predict — after training
# ---------------------------------------------------------------------------


class TestCycleLeaderModelPredictTrained:
    @pytest.fixture
    def trained_model(self) -> CycleLeaderModel:
        model = CycleLeaderModel()
        data, labels = _make_training_set()
        model.train(data, labels)
        return model

    def test_predict_returns_float(self, trained_model: CycleLeaderModel) -> None:
        """predict() must return a float."""
        fv = FeatureBuilder().build(_make_raw("ETH", 0.8))
        result = trained_model.predict(fv)
        assert isinstance(result, float)

    def test_predict_result_is_between_0_and_1(self, trained_model: CycleLeaderModel) -> None:
        """predict() must return a probability in [0, 1]."""
        fv = FeatureBuilder().build(_make_raw("ETH", 0.8))
        result = trained_model.predict(fv)
        assert 0.0 <= result <= 1.0

    def test_predict_high_score_token_scores_higher_than_low_score(
        self, trained_model: CycleLeaderModel
    ) -> None:
        """A 'strong' token must score higher than a 'weak' token on average."""
        builder = FeatureBuilder()
        strong = builder.build(_make_raw("STRONG", 0.95))
        weak = builder.build(_make_raw("WEAK", 0.05))
        assert trained_model.predict(strong) >= trained_model.predict(weak)

    def test_predict_batch_returns_list_of_floats(
        self, trained_model: CycleLeaderModel
    ) -> None:
        """predict_batch() must return a list of floats, one per input."""
        builder = FeatureBuilder()
        fvs = builder.build_batch([_make_raw("A", 0.7), _make_raw("B", 0.3)])
        results = trained_model.predict_batch(fvs)
        assert len(results) == 2
        assert all(isinstance(r, float) for r in results)
        assert all(0.0 <= r <= 1.0 for r in results)


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------


class TestCycleLeaderModelPersistence:
    def test_save_and_load_restores_trained_state(self, tmp_path: pytest.TempPathFactory) -> None:
        """A model saved to disk and reloaded must still predict correctly."""
        model = CycleLeaderModel()
        data, labels = _make_training_set()
        model.train(data, labels)

        path = str(tmp_path / "model.pkl")  # type: ignore[operator]
        model.save(path)

        loaded = CycleLeaderModel()
        loaded.load(path)

        assert loaded.is_trained is True
        fv = FeatureBuilder().build(_make_raw("SOL", 0.9))
        assert 0.0 <= loaded.predict(fv) <= 1.0

    def test_load_nonexistent_file_raises_file_not_found(self) -> None:
        """load() with a non-existent path must raise FileNotFoundError."""
        model = CycleLeaderModel()
        with pytest.raises(FileNotFoundError):
            model.load("/tmp/does_not_exist_xyz.pkl")
