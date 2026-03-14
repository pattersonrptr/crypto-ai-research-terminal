"""CycleLeaderModel — XGBoost classifier for identifying cycle-leading tokens.

Predicts the probability that a token will outperform the market over the next
Bitcoin cycle, based on feature vectors produced by :class:`FeatureBuilder`.

The model outputs a probability in [0, 1]:
- 1.0  → strong cycle-leader candidate ("next Solana" signal)
- 0.0  → unlikely to lead the next cycle

Usage::

    from app.ml.feature_builder import FeatureBuilder, RawTokenData
    from app.ml.cycle_leader_model import CycleLeaderModel

    builder = FeatureBuilder()
    model   = CycleLeaderModel()

    # Training
    features = [builder.build(d) for d in raw_data_list]
    result   = model.train(raw_data_list, labels)

    # Inference
    score = model.predict(builder.build(new_token))
    model.save("model.pkl")

    # Reloading
    loaded = CycleLeaderModel()
    loaded.load("model.pkl")
    score = loaded.predict(builder.build(new_token))
"""

from __future__ import annotations

import pickle  # nosec B403
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import structlog
from xgboost import XGBClassifier

from app.ml.feature_builder import FeatureBuilder, FeatureVector, RawTokenData

logger = structlog.get_logger(__name__)

# XGBoost hyper-parameters tuned for small tabular datasets.
# Kept conservative to avoid over-fitting on the limited historical data
# available in Phase 7. Phase 8 will add a proper grid-search step.
_DEFAULT_PARAMS: dict[str, object] = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "use_label_encoder": False,
    "eval_metric": "logloss",
    "random_state": 42,
    "n_jobs": -1,
}


@dataclass
class TrainingResult:
    """Summary statistics returned after a training run."""

    accuracy: float
    n_samples: int
    feature_importances: dict[str, float] = field(default_factory=dict)


class CycleLeaderModel:
    """XGBoost binary classifier for cycle-leader probability scoring.

    Labels are binary (1 = cycle leader, 0 = not), but ``predict()`` returns
    the raw probability from ``predict_proba``, so callers get a smooth
    continuous score rather than a hard threshold.
    """

    def __init__(self) -> None:
        self._clf: XGBClassifier | None = None
        self._feature_builder = FeatureBuilder()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_trained(self) -> bool:
        """True if the model has been trained or loaded from disk."""
        return self._clf is not None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, data: list[RawTokenData], labels: list[float]) -> TrainingResult:
        """Train the model on *data* with binary *labels*.

        Args:
            data:   Raw token data for each training sample.
            labels: Binary label per sample (1.0 = cycle leader, 0.0 = not).

        Returns:
            :class:`TrainingResult` with accuracy and feature importances.

        Raises:
            ValueError: If ``len(data) != len(labels)``.
        """
        if len(data) != len(labels):
            raise ValueError(
                f"data and labels must have the same length, " f"got {len(data)} vs {len(labels)}"
            )

        vectors = self._feature_builder.build_batch(data)
        x = np.array([fv.to_list() for fv in vectors], dtype=np.float32)
        y = np.array(labels, dtype=np.float32)

        clf = XGBClassifier(**_DEFAULT_PARAMS)
        clf.fit(x, y)
        self._clf = clf

        # Accuracy on training set (proxy; real eval happens in ModelTrainer)
        preds = clf.predict(x)
        accuracy = float(np.mean(preds == y))

        # Feature importances keyed by name
        names = vectors[0].feature_names()
        importances = {
            name: float(score) for name, score in zip(names, clf.feature_importances_, strict=True)
        }

        logger.info(
            "cycle_leader_model.trained",
            n_samples=len(data),
            accuracy=round(accuracy, 4),
        )
        return TrainingResult(
            accuracy=accuracy,
            n_samples=len(data),
            feature_importances=importances,
        )

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, fv: FeatureVector) -> float:
        """Return the cycle-leader probability for a single token.

        Args:
            fv: Feature vector produced by :class:`FeatureBuilder`.

        Returns:
            Probability in [0, 1] — higher means stronger cycle-leader signal.

        Raises:
            RuntimeError: If the model has not been trained or loaded yet.
        """
        if self._clf is None:
            raise RuntimeError("CycleLeaderModel is not trained. Call train() or load() first.")
        x = np.array([fv.to_list()], dtype=np.float32)
        proba: float = float(self._clf.predict_proba(x)[0, 1])
        return proba

    def predict_batch(self, fvs: list[FeatureVector]) -> list[float]:
        """Return cycle-leader probabilities for a list of feature vectors.

        Args:
            fvs: Feature vectors produced by :class:`FeatureBuilder`.

        Returns:
            List of probabilities in [0, 1], one per input vector.

        Raises:
            RuntimeError: If the model has not been trained or loaded yet.
        """
        if self._clf is None:
            raise RuntimeError("CycleLeaderModel is not trained. Call train() or load() first.")
        if not fvs:
            return []
        x = np.array([fv.to_list() for fv in fvs], dtype=np.float32)
        probas = self._clf.predict_proba(x)[:, 1]
        return [float(p) for p in probas]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Serialise the trained model to *path* using pickle.

        Args:
            path: File path to write (will be created/overwritten).

        Raises:
            RuntimeError: If the model has not been trained yet.
        """
        if self._clf is None:
            raise RuntimeError("Cannot save an untrained model.")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("wb") as f:
            pickle.dump(self._clf, f)
        logger.info("cycle_leader_model.saved", path=path)

    def load(self, path: str) -> None:
        """Restore a previously saved model from *path*.

        Args:
            path: File path to read.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        with p.open("rb") as f:
            self._clf = pickle.load(f)  # noqa: S301  # nosec B301
        logger.info("cycle_leader_model.loaded", path=path)
