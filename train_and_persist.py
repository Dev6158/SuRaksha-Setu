"""
train_and_persist.py
====================
Production-grade model serialization routine for a FastAPI anomaly-detection
service.  Orchestrates:

  1. Synthetic behavioural dataset generation  (swap with your real loader)
  2. Scikit-learn preprocessing pipeline        (StandardScaler + feature eng.)
  3. Isolation Forest training                  (user-profile outlier isolation)
  4. Calibration / threshold tuning passes
  5. Joblib serialisation to a deployment-ready .joblib asset

Run directly:
    python train_and_persist.py [--output models/user_profile.joblib]

Imported by FastAPI startup:
    from train_and_persist import load_or_train
    pipeline = load_or_train()
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import IsolationForest
from sklearn.exceptions import NotFittedError
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("train_and_persist")

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------
DEFAULT_MODEL_PATH = Path("models/user_profile.joblib")
RANDOM_STATE = 42

# Isolation Forest hyper-params (tune via grid-search in production)
IF_CONTAMINATION = 0.05   # expected outlier fraction
IF_N_ESTIMATORS  = 200
IF_MAX_SAMPLES   = "auto"
IF_MAX_FEATURES  = 1.0

# Calibration: decision-score percentile used to pin the anomaly threshold
CALIBRATION_PERCENTILE = 95   # top-5 % inlier scores → threshold

# ---------------------------------------------------------------------------
# 1. Synthetic dataset (replace with your real ETL / DB loader)
# ---------------------------------------------------------------------------

def generate_synthetic_dataset(
    n_normal: int = 4_000,
    n_anomaly: int = 200,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Simulate a behavioural user-profile dataset.

    Normal users cluster around realistic usage patterns; anomalies are
    injected as edge-case behaviour (bots, fraud, crawlers, etc.).

    Returns
    -------
    pd.DataFrame with columns:
        session_duration_s, pages_per_session, click_rate_per_min,
        error_rate, night_hour_ratio, device_type_encoded,
        geo_distance_km, requests_per_day, label  (0=normal, 1=anomaly)
    """
    rng = np.random.default_rng(random_state)
    log.info("Generating synthetic dataset  (normal=%d  anomaly=%d)", n_normal, n_anomaly)

    def _normal_users(n: int) -> dict[str, np.ndarray]:
        return {
            "session_duration_s":  rng.normal(420,  120, n).clip(30, 3_600),
            "pages_per_session":   rng.normal(6,    2,   n).clip(1,  40),
            "click_rate_per_min":  rng.normal(4,    1.5, n).clip(0.1, 30),
            "error_rate":          rng.beta(1.5, 20, n),
            "night_hour_ratio":    rng.beta(2,   8,  n),
            "device_type_encoded": rng.choice([0, 1, 2], n, p=[0.55, 0.35, 0.10]),
            "geo_distance_km":     rng.exponential(150, n).clip(0, 15_000),
            "requests_per_day":    rng.normal(80,  30,  n).clip(1, 1_000),
        }

    def _anomaly_users(n: int) -> dict[str, np.ndarray]:
        return {
            "session_duration_s":  rng.choice(
                [rng.uniform(0, 5, n), rng.uniform(3_500, 3_600, n)],
                axis=0,
            ).diagonal(),
            "pages_per_session":   rng.uniform(100, 500, n),
            "click_rate_per_min":  rng.choice([rng.uniform(0, 0.05, n),
                                               rng.uniform(50, 200, n)],
                                              axis=0).diagonal(),
            "error_rate":          rng.uniform(0.5, 1.0, n),
            "night_hour_ratio":    rng.uniform(0.8, 1.0, n),
            "device_type_encoded": rng.choice([0, 1, 2], n),
            "geo_distance_km":     rng.uniform(12_000, 20_000, n),
            "requests_per_day":    rng.uniform(5_000, 50_000, n),
        }

    df_normal  = pd.DataFrame(_normal_users(n_normal));  df_normal["label"]  = 0
    df_anomaly = pd.DataFrame(_anomaly_users(n_anomaly)); df_anomaly["label"] = 1
    df = (pd.concat([df_normal, df_anomaly], ignore_index=True)
            .sample(frac=1, random_state=random_state)
            .reset_index(drop=True))

    log.info("Dataset shape: %s  |  anomaly rate: %.2f%%",
             df.shape, df["label"].mean() * 100)
    return df


# ---------------------------------------------------------------------------
# 2. Custom transformer — domain feature engineering
# ---------------------------------------------------------------------------

class BehaviourFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Derives ratio / interaction features that improve Isolation Forest
    separability without leaking label information.
    """

    FEATURE_NAMES_IN = [
        "session_duration_s", "pages_per_session", "click_rate_per_min",
        "error_rate", "night_hour_ratio", "device_type_encoded",
        "geo_distance_km", "requests_per_day",
    ]

    def fit(self, X: pd.DataFrame, y=None) -> "BehaviourFeatureEngineer":
        # stateless — nothing to learn
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        eps = 1e-9

        # Interaction ratios
        X["pages_per_second"]     = X["pages_per_session"] / (X["session_duration_s"] + eps)
        X["requests_per_session"] = X["requests_per_day"]  / (X["pages_per_session"]  + eps)
        X["click_error_ratio"]    = X["click_rate_per_min"] / (X["error_rate"]        + eps)

        # Log-scale heavy-tailed features
        X["log_geo_distance"]     = np.log1p(X["geo_distance_km"])
        X["log_requests_per_day"] = np.log1p(X["requests_per_day"])

        return X

    def get_feature_names_out(self, input_features=None) -> list[str]:
        return (self.FEATURE_NAMES_IN +
                ["pages_per_second", "requests_per_session",
                 "click_error_ratio", "log_geo_distance", "log_requests_per_day"])


# ---------------------------------------------------------------------------
# 3. Pipeline factory
# ---------------------------------------------------------------------------

def build_pipeline() -> Pipeline:
    """
    Constructs the full sklearn Pipeline:
        BehaviourFeatureEngineer → StandardScaler → IsolationForest
    """
    return Pipeline([
        ("feature_engineer", BehaviourFeatureEngineer()),
        ("scaler",           StandardScaler()),
        ("isolation_forest", IsolationForest(
            n_estimators=IF_N_ESTIMATORS,
            max_samples=IF_MAX_SAMPLES,
            max_features=IF_MAX_FEATURES,
            contamination=IF_CONTAMINATION,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            warm_start=False,
        )),
    ])


# ---------------------------------------------------------------------------
# 4. Calibration pass
# ---------------------------------------------------------------------------

class CalibratedIFPipeline:
    """
    Thin wrapper that holds the fitted sklearn Pipeline plus a calibrated
    decision threshold derived from held-out inlier score percentiles.

    Exposes:
        .predict(X)        → np.ndarray of int  {1=normal, -1=anomaly}
        .score_samples(X)  → raw anomaly scores  (higher = more normal)
        .threshold         → float, the calibrated cut-point
    """

    def __init__(self, pipeline: Pipeline, threshold: float):
        self._pipeline  = pipeline
        self.threshold  = threshold

    # ------------------------------------------------------------------
    # Public API used by FastAPI endpoints
    # ------------------------------------------------------------------

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        scores = self.score_samples(X)
        return np.where(scores >= self.threshold, 1, -1)

    def score_samples(self, X: pd.DataFrame) -> np.ndarray:
        try:
            return self._pipeline.score_samples(X)
        except NotFittedError as exc:
            raise RuntimeError("Pipeline is not fitted. Run train_and_persist.py") from exc

    # Expose underlying pipeline for sklearn utilities (GridSearch, etc.)
    @property
    def named_steps(self):
        return self._pipeline.named_steps

    # Persist / restore
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pipeline":  self._pipeline,
            "threshold": self.threshold,
            "schema_version": "1.0",
        }
        joblib.dump(payload, path, compress=("lz4", 3), protocol=5)
        size_kb = path.stat().st_size / 1_024
        log.info("Model serialised → %s  (%.1f KB)", path, size_kb)

    @classmethod
    def load(cls, path: Path) -> "CalibratedIFPipeline":
        payload = joblib.load(path)
        log.info("Model loaded ← %s  (schema v%s)", path, payload.get("schema_version"))
        return cls(pipeline=payload["pipeline"], threshold=payload["threshold"])


def calibrate_threshold(
    pipeline: Pipeline,
    X_cal: pd.DataFrame,
    percentile: int = CALIBRATION_PERCENTILE,
) -> float:
    """
    Pin the anomaly threshold at the `percentile`-th percentile of
    inlier decision scores from the calibration split.

    A score below this cut-point will be flagged as anomalous.
    """
    scores = pipeline.score_samples(X_cal)
    threshold = float(np.percentile(scores, 100 - percentile))
    log.info(
        "Calibration pass — score percentile p%d = %.6f  "
        "(scores: min=%.4f  mean=%.4f  max=%.4f)",
        percentile, threshold, scores.min(), scores.mean(), scores.max(),
    )
    return threshold


# ---------------------------------------------------------------------------
# 5. Evaluation helpers
# ---------------------------------------------------------------------------

def evaluate(
    model: CalibratedIFPipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, Any]:
    """
    Compute test-set metrics.  Labels: 0=normal → mapped to 1, 1=anomaly → -1.
    """
    preds  = model.predict(X_test)           # {1, -1}
    scores = model.score_samples(X_test)

    # Convert ground-truth: normal(0)→+1, anomaly(1)→-1
    gt_if  = np.where(y_test == 0, 1, -1)

    tp = int(((preds == -1) & (gt_if == -1)).sum())
    fp = int(((preds == -1) & (gt_if ==  1)).sum())
    fn = int(((preds ==  1) & (gt_if == -1)).sum())
    tn = int(((preds ==  1) & (gt_if ==  1)).sum())

    precision = tp / (tp + fp + 1e-9)
    recall    = tp / (tp + fn + 1e-9)
    f1        = 2 * precision * recall / (precision + recall + 1e-9)

    # ROC-AUC: higher score = more normal → negate for standard convention
    try:
        auc = roc_auc_score(y_test, -scores)
    except ValueError:
        auc = float("nan")

    metrics = dict(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        roc_auc=round(auc, 4),
        tp=tp, fp=fp, fn=fn, tn=tn,
        threshold=round(model.threshold, 6),
        n_test=len(y_test),
    )
    log.info(
        "Evaluation — precision=%.4f  recall=%.4f  F1=%.4f  AUC=%.4f",
        precision, recall, f1, auc,
    )
    return metrics


# ---------------------------------------------------------------------------
# 6. Main orchestration
# ---------------------------------------------------------------------------

def train(
    output_path: Path = DEFAULT_MODEL_PATH,
    n_normal: int = 4_000,
    n_anomaly: int = 200,
) -> CalibratedIFPipeline:
    """
    Full training run:
        load → split → fit → calibrate → evaluate → serialise

    Returns the fitted CalibratedIFPipeline.
    """
    t0 = time.perf_counter()
    log.info("=" * 60)
    log.info("train_and_persist  —  starting training run")
    log.info("=" * 60)

    # ── 1. Load data ────────────────────────────────────────────────
    df = generate_synthetic_dataset(n_normal=n_normal, n_anomaly=n_anomaly)

    feature_cols = BehaviourFeatureEngineer.FEATURE_NAMES_IN
    X = df[feature_cols]
    y = df["label"]

    # ── 2. Stratified split: 70% train | 15% calibration | 15% test ─
    sss_outer = StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=RANDOM_STATE)
    train_idx, holdout_idx = next(sss_outer.split(X, y))

    sss_inner = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=RANDOM_STATE)
    cal_idx_rel, test_idx_rel = next(sss_inner.split(X.iloc[holdout_idx], y.iloc[holdout_idx]))

    X_train = X.iloc[train_idx]
    X_cal   = X.iloc[holdout_idx].iloc[cal_idx_rel]
    X_test  = X.iloc[holdout_idx].iloc[test_idx_rel]
    y_train = y.iloc[train_idx]
    y_cal   = y.iloc[holdout_idx].iloc[cal_idx_rel]
    y_test  = y.iloc[holdout_idx].iloc[test_idx_rel]

    log.info(
        "Split sizes — train=%d  calibration=%d  test=%d",
        len(X_train), len(X_cal), len(X_test),
    )

    # ── 3. Fit pipeline (train on *normal* records only — unsupervised) ─
    X_train_normal = X_train[y_train == 0]
    log.info("Fitting pipeline on %d normal-class records …", len(X_train_normal))
    pipeline = build_pipeline()
    pipeline.fit(X_train_normal)
    log.info("Pipeline fitted.")

    # ── 4. Calibration pass ─────────────────────────────────────────
    X_cal_normal = X_cal[y_cal == 0]
    threshold = calibrate_threshold(pipeline, X_cal_normal)

    model = CalibratedIFPipeline(pipeline=pipeline, threshold=threshold)

    # ── 5. Evaluation ───────────────────────────────────────────────
    metrics = evaluate(model, X_test, y_test)
    log.info("Test metrics: %s", metrics)

    # ── 6. Serialise ────────────────────────────────────────────────
    model.save(output_path)

    elapsed = time.perf_counter() - t0
    log.info("Training run complete in %.2f s  →  %s", elapsed, output_path)
    return model


# ---------------------------------------------------------------------------
# 7. FastAPI helper  (imported at startup)
# ---------------------------------------------------------------------------

def load_or_train(
    model_path: Path = DEFAULT_MODEL_PATH,
    force_retrain: bool = False,
) -> CalibratedIFPipeline:
    """
    Load a pre-serialised model if it exists, otherwise trigger training.

    Usage in FastAPI lifespan:
        from train_and_persist import load_or_train, CalibratedIFPipeline
        app.state.model: CalibratedIFPipeline = load_or_train()
    """
    if not force_retrain and model_path.exists():
        log.info("Loading existing model from %s", model_path)
        return CalibratedIFPipeline.load(model_path)

    log.info("No model found at %s — initiating training …", model_path)
    return train(output_path=model_path)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Train and persist the user-profile Isolation Forest pipeline.",
    )
    p.add_argument(
        "--output", type=Path, default=DEFAULT_MODEL_PATH,
        metavar="PATH",
        help=f"Destination .joblib path  (default: {DEFAULT_MODEL_PATH})",
    )
    p.add_argument(
        "--n-normal",  type=int, default=4_000,
        help="Normal-class samples to generate (default: 4000)",
    )
    p.add_argument(
        "--n-anomaly", type=int, default=200,
        help="Anomalous samples to generate (default: 200)",
    )
    p.add_argument(
        "--force-retrain", action="store_true",
        help="Ignore existing model file and retrain from scratch",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    load_or_train(
        model_path=args.output,
        force_retrain=args.force_retrain,
    )
