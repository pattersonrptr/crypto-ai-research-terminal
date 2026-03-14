"""Tests for ml/model_trainer.py — TDD Red phase.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ml.cycle_leader_model import CycleLeaderModel
from app.ml.feature_builder import RawTokenData
from app.ml.model_trainer import ModelTrainer, TrainerConfig, TrainerReport

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw(symbol: str, score: float = 0.5) -> RawTokenData:
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


def _make_dataset(n: int = 60) -> tuple[list[RawTokenData], list[float]]:
    data: list[RawTokenData] = []
    labels: list[float] = []
    for i in range(n):
        score = (i + 1) / n
        data.append(_make_raw(f"TOK{i}", score))
        labels.append(1.0 if score >= 0.5 else 0.0)
    return data, labels


# ---------------------------------------------------------------------------
# TrainerConfig
# ---------------------------------------------------------------------------


class TestTrainerConfig:
    def test_default_config_has_valid_split_ratio(self) -> None:
        """Default validation split must be between 0.1 and 0.5."""
        cfg = TrainerConfig()
        assert 0.1 <= cfg.validation_split <= 0.5

    def test_custom_config_is_accepted(self, tmp_path: pytest.TempPathFactory) -> None:
        """TrainerConfig must accept custom validation_split and output_dir."""
        cfg = TrainerConfig(validation_split=0.3, output_dir=str(tmp_path))
        assert cfg.validation_split == 0.3
        assert cfg.output_dir == str(tmp_path)

    def test_invalid_split_below_minimum_raises_value_error(self) -> None:
        """validation_split < 0.1 must raise ValueError."""
        with pytest.raises(ValueError, match="validation_split"):
            TrainerConfig(validation_split=0.05)

    def test_invalid_split_above_maximum_raises_value_error(self) -> None:
        """validation_split > 0.5 must raise ValueError."""
        with pytest.raises(ValueError, match="validation_split"):
            TrainerConfig(validation_split=0.6)


# ---------------------------------------------------------------------------
# ModelTrainer instantiation
# ---------------------------------------------------------------------------


class TestModelTrainerInit:
    def test_trainer_creation_with_defaults_succeeds(self) -> None:
        """ModelTrainer() must instantiate without errors."""
        trainer = ModelTrainer()
        assert trainer is not None

    def test_trainer_creation_with_custom_config_succeeds(self) -> None:
        """ModelTrainer accepts a custom TrainerConfig."""
        cfg = TrainerConfig(validation_split=0.25)
        trainer = ModelTrainer(config=cfg)
        assert trainer is not None


# ---------------------------------------------------------------------------
# run_training
# ---------------------------------------------------------------------------


class TestModelTrainerRunTraining:
    def test_run_training_returns_trainer_report(self) -> None:
        """run_training() must return a TrainerReport."""
        trainer = ModelTrainer()
        data, labels = _make_dataset()
        report = trainer.run_training(data, labels)
        assert isinstance(report, TrainerReport)

    def test_run_training_report_has_train_accuracy(self) -> None:
        """TrainerReport must include train_accuracy in [0, 1]."""
        trainer = ModelTrainer()
        data, labels = _make_dataset()
        report = trainer.run_training(data, labels)
        assert 0.0 <= report.train_accuracy <= 1.0

    def test_run_training_report_has_val_accuracy(self) -> None:
        """TrainerReport must include val_accuracy in [0, 1]."""
        trainer = ModelTrainer()
        data, labels = _make_dataset()
        report = trainer.run_training(data, labels)
        assert 0.0 <= report.val_accuracy <= 1.0

    def test_run_training_report_records_n_train_and_n_val(self) -> None:
        """TrainerReport must record n_train + n_val = total samples."""
        trainer = ModelTrainer()
        data, labels = _make_dataset(50)
        report = trainer.run_training(data, labels)
        assert report.n_train + report.n_val == 50

    def test_run_training_report_has_feature_importances(self) -> None:
        """TrainerReport must include feature_importances dict."""
        trainer = ModelTrainer()
        data, labels = _make_dataset()
        report = trainer.run_training(data, labels)
        assert isinstance(report.feature_importances, dict)
        assert len(report.feature_importances) > 0

    def test_run_training_produces_trained_model(self) -> None:
        """After run_training(), trainer.model must be trained."""
        trainer = ModelTrainer()
        data, labels = _make_dataset()
        trainer.run_training(data, labels)
        assert trainer.model.is_trained is True

    def test_run_training_with_too_few_samples_raises_value_error(self) -> None:
        """run_training() with fewer than 10 samples must raise ValueError."""
        trainer = ModelTrainer()
        data, labels = _make_dataset(5)
        with pytest.raises(ValueError, match="at least"):
            trainer.run_training(data, labels)

    def test_run_training_with_mismatched_lengths_raises_value_error(self) -> None:
        """run_training() with len(data) != len(labels) must raise ValueError."""
        trainer = ModelTrainer()
        data, labels = _make_dataset(20)
        with pytest.raises(ValueError, match="same length"):
            trainer.run_training(data, labels[:10])


# ---------------------------------------------------------------------------
# save_model
# ---------------------------------------------------------------------------


class TestModelTrainerSaveModel:
    def test_save_model_writes_file_to_output_dir(self, tmp_path: Path) -> None:
        """save_model() must create a file at the configured output_dir."""
        cfg = TrainerConfig(output_dir=str(tmp_path))
        trainer = ModelTrainer(config=cfg)
        data, labels = _make_dataset()
        trainer.run_training(data, labels)
        saved_path = trainer.save_model()
        assert Path(saved_path).exists()

    def test_save_model_without_training_raises_runtime_error(self, tmp_path: Path) -> None:
        """save_model() before run_training() must raise RuntimeError."""
        cfg = TrainerConfig(output_dir=str(tmp_path))
        trainer = ModelTrainer(config=cfg)
        with pytest.raises(RuntimeError, match="not trained"):
            trainer.save_model()

    def test_saved_model_can_be_loaded_into_cycle_leader_model(self, tmp_path: Path) -> None:
        """A model saved by the trainer must be loadable by CycleLeaderModel."""
        cfg = TrainerConfig(output_dir=str(tmp_path))
        trainer = ModelTrainer(config=cfg)
        data, labels = _make_dataset()
        trainer.run_training(data, labels)
        path = trainer.save_model()

        fresh = CycleLeaderModel()
        fresh.load(path)
        assert fresh.is_trained is True
