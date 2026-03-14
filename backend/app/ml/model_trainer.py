"""ModelTrainer — orchestrates the full ML training pipeline.

Responsibilities:
1. Validate inputs and enforce minimum sample requirements.
2. Split data into train / validation sets (stratified).
3. Delegate training to :class:`CycleLeaderModel`.
4. Evaluate on the held-out validation set.
5. Serialise the trained model to disk.

Usage::

    from app.ml.model_trainer import ModelTrainer, TrainerConfig

    cfg     = TrainerConfig(validation_split=0.2, output_dir="data/models")
    trainer = ModelTrainer(config=cfg)
    report  = trainer.run_training(raw_data_list, labels)
    path    = trainer.save_model()

    print(f"val accuracy: {report.val_accuracy:.2%}")
    print(f"saved to:     {path}")
"""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import structlog
from sklearn.model_selection import train_test_split

from app.ml.cycle_leader_model import CycleLeaderModel
from app.ml.feature_builder import FeatureBuilder, FeatureVector, RawTokenData

logger = structlog.get_logger(__name__)

_MIN_SAMPLES = 10
_DEFAULT_OUTPUT_DIR = "data/models"


@dataclass
class TrainerConfig:
    """Configuration for a ModelTrainer run.

    Attributes:
        validation_split: Fraction of data held out for validation (0.1–0.5).
        output_dir:       Directory where the serialised model is written.
        random_state:     Seed for train/val split reproducibility.
    """

    validation_split: float = 0.2
    output_dir: str = _DEFAULT_OUTPUT_DIR
    random_state: int = 42

    def __post_init__(self) -> None:
        if not 0.1 <= self.validation_split <= 0.5:
            raise ValueError(
                f"validation_split must be in [0.1, 0.5], got {self.validation_split}"
            )


@dataclass
class TrainerReport:
    """Evaluation summary produced after a training run."""

    train_accuracy: float
    val_accuracy: float
    n_train: int
    n_val: int
    feature_importances: dict[str, float] = field(default_factory=dict)


class ModelTrainer:
    """High-level training pipeline for :class:`CycleLeaderModel`.

    Handles data splitting, training, evaluation, and model persistence.
    """

    def __init__(self, config: TrainerConfig | None = None) -> None:
        self._config = config or TrainerConfig()
        self._model = CycleLeaderModel()
        self._feature_builder = FeatureBuilder()
        self._trained = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def model(self) -> CycleLeaderModel:
        """The underlying :class:`CycleLeaderModel` (may be untrained)."""
        return self._model

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def run_training(
        self,
        data: list[RawTokenData],
        labels: list[float],
    ) -> TrainerReport:
        """Run the full training pipeline and return an evaluation report.

        Args:
            data:   Raw token data, one entry per sample.
            labels: Binary label per sample (1.0 = cycle leader, 0.0 = not).

        Returns:
            :class:`TrainerReport` with train + validation accuracy and
            feature importances.

        Raises:
            ValueError: If ``len(data) != len(labels)``.
            ValueError: If there are fewer than 10 samples.
        """
        if len(data) != len(labels):
            raise ValueError(
                f"data and labels must have the same length, "
                f"got {len(data)} vs {len(labels)}"
            )
        if len(data) < _MIN_SAMPLES:
            raise ValueError(
                f"run_training requires at least {_MIN_SAMPLES} samples, "
                f"got {len(data)}"
            )

        # Build feature vectors
        vectors: list[FeatureVector] = self._feature_builder.build_batch(data)
        x = np.array([fv.to_list() for fv in vectors], dtype=np.float32)
        y = np.array(labels, dtype=np.float32)

        # Stratified train / validation split
        x_train, x_val, y_train, y_val, idx_train, idx_val = train_test_split(
            x,
            y,
            np.arange(len(data)),
            test_size=self._config.validation_split,
            stratify=y,
            random_state=self._config.random_state,
        )

        # Reconstruct RawTokenData lists for the split subsets
        train_data = [data[i] for i in idx_train]
        train_labels = [labels[i] for i in idx_train]

        # Train model on training subset
        train_result = self._model.train(train_data, train_labels)

        # Evaluate on validation set using the model's internal classifier
        val_preds = (
            np.array(
                self._model.predict_batch(
                    [vectors[i] for i in idx_val]
                )
            )
            >= 0.5
        ).astype(float)
        val_accuracy = float(np.mean(val_preds == y_val))

        self._trained = True

        logger.info(
            "model_trainer.training_complete",
            n_train=len(idx_train),
            n_val=len(idx_val),
            train_accuracy=round(train_result.accuracy, 4),
            val_accuracy=round(val_accuracy, 4),
        )

        return TrainerReport(
            train_accuracy=train_result.accuracy,
            val_accuracy=val_accuracy,
            n_train=len(idx_train),
            n_val=len(idx_val),
            feature_importances=train_result.feature_importances,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_model(self, filename: str | None = None) -> str:
        """Serialise the trained model to ``output_dir``.

        Args:
            filename: Optional file name.  Defaults to a timestamped name.

        Returns:
            Absolute path to the saved model file.

        Raises:
            RuntimeError: If the model has not been trained yet.
        """
        if not self._trained:
            raise RuntimeError(
                "Cannot save: model is not trained. Call run_training() first."
            )

        output_dir = Path(self._config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"cycle_leader_{ts}.pkl"

        path = str(output_dir / filename)
        self._model.save(path)
        logger.info("model_trainer.model_saved", path=path)
        return path
