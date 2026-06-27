"""
behavioral_analytics_engine.py
────────────────────────────────────────────────────────────────────────────────
Runtime Behavioral Anomaly Detection Service
Author  : ML Platform Team
Runtime : Python 3.11+
Deps    : fastapi, uvicorn, scikit-learn, numpy, pandas, pydantic, joblib
────────────────────────────────────────────────────────────────────────────────

Architecture Overview
─────────────────────
Two concurrent anomaly detection pipelines run per user session:

  Pipeline A  –  Isolation Forest (IF)
      Tracks real-time spatial telemetry vectors:
        • Swipe velocity (px/ms) on X and Y axes
        • Tapping force (normalised pressure 0.0–1.0)
        • Rotational gyroscope offsets (°/s) on roll, pitch, yaw axes

  Pipeline B  –  One-Class Support Vector Machine (OC-SVM)
      Maps accumulated historical interaction pattern fingerprints:
        • Session-level aggregated behavioural statistics
        • Inter-event timing distributions
        • Gesture rhythm harmonics

  Fallback Profile
      When a user's event log contains fewer than MIN_BASELINE_RECORDS
      observations, both ML pipelines are bypassed.  A rolling statistical
      profile (mean ± k·σ bounds) is computed instead, and each incoming
      event is scored against the Chebyshev / Z-score threshold.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("behavioral_analytics_engine")

# ──────────────────────────────────────────────────────────────────────────────
# Global Hyper-parameters
# ──────────────────────────────────────────────────────────────────────────────

# Minimum number of recorded baseline events before ML models are fitted.
MIN_BASELINE_RECORDS: int = 50

# Isolation Forest parameters
IF_N_ESTIMATORS: int = 200
IF_MAX_SAMPLES: str = "auto"
IF_CONTAMINATION: float = 0.05          # Expected 5 % anomaly rate in training
IF_MAX_FEATURES: float = 1.0
IF_BOOTSTRAP: bool = False
IF_RANDOM_STATE: int = 42

# One-Class SVM parameters
OC_SVM_KERNEL: str = "rbf"
OC_SVM_NU: float = 0.05                 # Upper bound on fraction of outliers
OC_SVM_GAMMA: str = "scale"            # 1 / (n_features * X.var())

# Rolling statistical fallback
ROLLING_WINDOW_SIZE: int = 30          # Events to compute rolling stats over
ZSCORE_ANOMALY_THRESHOLD: float = 3.0 # |z| > threshold → anomaly
CHEBYSHEV_K: float = 3.0              # k in Chebyshev (P(|X-μ|≥kσ) ≤ 1/k²)

# History retention per user (bounded deque to avoid unbounded RAM)
MAX_STORED_EVENTS_PER_USER: int = 5_000

# Confidence blending weights when both ML pipelines are active
IF_BLEND_WEIGHT: float = 0.55
OC_SVM_BLEND_WEIGHT: float = 0.45
assert abs(IF_BLEND_WEIGHT + OC_SVM_BLEND_WEIGHT - 1.0) < 1e-9, (
    "Blend weights must sum to 1.0"
)

# ──────────────────────────────────────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────────────────────────────────────

class AnomalyPipeline(str, Enum):
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM    = "one_class_svm"
    STATISTICAL_FALLBACK = "statistical_fallback"
    BLENDED          = "blended"


class AnomalyVerdict(str, Enum):
    NORMAL  = "normal"
    ANOMALY = "anomaly"
    UNKNOWN = "unknown"          # Returned on the very first event (no history)


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Request / Response Models
# ──────────────────────────────────────────────────────────────────────────────

class SwipeTelemetry(BaseModel):
    """
    Spatial telemetry from a single swipe gesture.

    velocity_x   : horizontal swipe velocity in pixels per millisecond
    velocity_y   : vertical swipe velocity in pixels per millisecond
    duration_ms  : total gesture duration in milliseconds
    distance_px  : Euclidean pixel distance of the swipe arc
    curvature    : normalised arc curvature (arc_length / chord_length - 1)
    """
    velocity_x:  float = Field(..., ge=-50.0, le=50.0,  description="px/ms horizontal")
    velocity_y:  float = Field(..., ge=-50.0, le=50.0,  description="px/ms vertical")
    duration_ms: float = Field(..., gt=0.0,  le=5000.0, description="Gesture duration ms")
    distance_px: float = Field(..., ge=0.0,  le=8000.0, description="Euclidean swipe length px")
    curvature:   float = Field(..., ge=0.0,  le=10.0,   description="Normalised curvature")


class TapTelemetry(BaseModel):
    """
    Force and timing metrics from a discrete tap event.

    force           : normalised pressure (hardware-reported 0.0 – 1.0)
    contact_area_mm2: estimated finger contact area in mm²
    dwell_ms        : duration finger was held on screen in ms
    x_norm          : normalised horizontal position on screen (0.0 – 1.0)
    y_norm          : normalised vertical position on screen (0.0 – 1.0)
    """
    force:            float = Field(..., ge=0.0, le=1.0,    description="Normalised pressure 0-1")
    contact_area_mm2: float = Field(..., ge=0.0, le=500.0,  description="mm²")
    dwell_ms:         float = Field(..., ge=0.0, le=3000.0, description="Hold duration ms")
    x_norm:           float = Field(..., ge=0.0, le=1.0,    description="Normalised X 0-1")
    y_norm:           float = Field(..., ge=0.0, le=1.0,    description="Normalised Y 0-1")


class GyroscopeTelemetry(BaseModel):
    """
    Three-axis gyroscope offsets captured during a gesture window.

    roll_deg_s  : rotation around the longitudinal (Z) axis in °/s
    pitch_deg_s : rotation around the lateral (X) axis in °/s
    yaw_deg_s   : rotation around the vertical (Y) axis in °/s
    magnitude   : vector magnitude √(roll²+pitch²+yaw²) in °/s
    """
    roll_deg_s:  float = Field(..., ge=-2000.0, le=2000.0, description="°/s roll")
    pitch_deg_s: float = Field(..., ge=-2000.0, le=2000.0, description="°/s pitch")
    yaw_deg_s:   float = Field(..., ge=-2000.0, le=2000.0, description="°/s yaw")
    magnitude:   float = Field(..., ge=0.0,     le=3465.0, description="°/s vector magnitude")

    @model_validator(mode="after")
    def validate_magnitude_consistency(self) -> "GyroscopeTelemetry":
        computed = math.sqrt(
            self.roll_deg_s ** 2
            + self.pitch_deg_s ** 2
            + self.yaw_deg_s ** 2
        )
        if abs(computed - self.magnitude) > 5.0:
            raise ValueError(
                f"Gyroscope magnitude {self.magnitude:.3f} deviates from "
                f"computed value {computed:.3f} by more than 5 °/s – "
                "possible sensor corruption."
            )
        return self


class InteractionPatternRecord(BaseModel):
    """
    Session-level aggregated behavioural fingerprint fed to the OC-SVM.

    These are computed server-side from a fixed trailing window of events
    and represent the statistical character of the user's session rhythm.

    avg_inter_event_ms     : mean time between consecutive touch events
    std_inter_event_ms     : standard deviation of inter-event timing
    session_event_rate     : events per second over the session window
    tap_swipe_ratio        : taps / (taps + swipes); 0 if no gestures
    avg_swipe_speed        : mean swipe speed (px/ms) over session window
    dominant_quadrant_freq : fraction of taps in the modal screen quadrant
    typing_rhythm_var      : coefficient of variation of keystroke intervals
    """
    avg_inter_event_ms:     float = Field(..., ge=0.0,   le=60_000.0)
    std_inter_event_ms:     float = Field(..., ge=0.0,   le=60_000.0)
    session_event_rate:     float = Field(..., ge=0.0,   le=200.0)
    tap_swipe_ratio:        float = Field(..., ge=0.0,   le=1.0)
    avg_swipe_speed:        float = Field(..., ge=0.0,   le=50.0)
    dominant_quadrant_freq: float = Field(..., ge=0.0,   le=1.0)
    typing_rhythm_var:      float = Field(..., ge=0.0,   le=10.0)


class BehaviouralEvent(BaseModel):
    """
    The top-level payload for a single scored event.

    user_id           : stable pseudonymous identifier (hashed on ingestion)
    event_id          : caller-supplied idempotency key (UUID v4 recommended)
    client_timestamp  : ISO-8601 UTC timestamp from the client device
    swipe             : optional swipe telemetry (None if event is a tap-only)
    tap               : optional tap telemetry   (None if event is a swipe-only)
    gyroscope         : optional gyroscope frame (None if device lacks sensor)
    interaction_pattern : optional session-level pattern (None on cold-start)
    """
    user_id:             str                              = Field(..., min_length=1, max_length=128)
    event_id:            str                              = Field(default_factory=lambda: str(uuid.uuid4()))
    client_timestamp:    datetime                         = Field(default_factory=lambda: datetime.now(timezone.utc))
    swipe:               Optional[SwipeTelemetry]         = None
    tap:                 Optional[TapTelemetry]           = None
    gyroscope:           Optional[GyroscopeTelemetry]     = None
    interaction_pattern: Optional[InteractionPatternRecord] = None

    @field_validator("client_timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(v)).replace(tzinfo=timezone.utc)


class AnomalyScore(BaseModel):
    """
    Scoring result returned to the caller.

    event_id           : echoed from the request for correlation
    user_id_hash       : SHA-256 of the raw user_id (never logged raw)
    verdict            : normal / anomaly / unknown
    pipeline_used      : which pipeline produced the verdict
    anomaly_score      : continuous risk score [0.0, 1.0]; higher = more anomalous
    if_score           : raw Isolation Forest decision function output (None if not used)
    svm_score          : raw OC-SVM decision function output (None if not used)
    stat_zscore        : max |z-score| across features (None if ML was used)
    baseline_count     : number of historical events used to fit/score
    model_fitted       : True when an ML model is loaded for this user
    processing_time_ms : server-side latency for this scoring call
    scored_at          : server UTC timestamp
    """
    event_id:           str
    user_id_hash:       str
    verdict:            AnomalyVerdict
    pipeline_used:      AnomalyPipeline
    anomaly_score:      float            = Field(..., ge=0.0, le=1.0)
    if_score:           Optional[float]  = None
    svm_score:          Optional[float]  = None
    stat_zscore:        Optional[float]  = None
    baseline_count:     int
    model_fitted:       bool
    processing_time_ms: float
    scored_at:          datetime


class TrainingRequest(BaseModel):
    """Trigger an explicit model (re-)fit for a user from their stored history."""
    user_id: str = Field(..., min_length=1, max_length=128)


class TrainingResponse(BaseModel):
    user_id_hash:        str
    if_fitted:           bool
    svm_fitted:          bool
    training_samples_if: int
    training_samples_svm: int
    fitted_at:           datetime


class HealthResponse(BaseModel):
    status:         str
    registered_users: int
    fitted_users:   int
    uptime_seconds: float


# ──────────────────────────────────────────────────────────────────────────────
# Feature Extraction Utilities
# ──────────────────────────────────────────────────────────────────────────────

# Isolation Forest feature set dimension
#   swipe (5) + tap (5) + gyroscope (4) = 14 raw features
#   We always emit a fixed-length vector; absent sub-vectors are zero-filled.
IF_FEATURE_NAMES: List[str] = [
    # Swipe (indices 0-4)
    "swipe_velocity_x",
    "swipe_velocity_y",
    "swipe_duration_ms",
    "swipe_distance_px",
    "swipe_curvature",
    # Tap (indices 5-9)
    "tap_force",
    "tap_contact_area_mm2",
    "tap_dwell_ms",
    "tap_x_norm",
    "tap_y_norm",
    # Gyroscope (indices 10-13)
    "gyro_roll_deg_s",
    "gyro_pitch_deg_s",
    "gyro_yaw_deg_s",
    "gyro_magnitude",
]

# OC-SVM feature set dimension = 7 (InteractionPatternRecord fields)
SVM_FEATURE_NAMES: List[str] = [
    "avg_inter_event_ms",
    "std_inter_event_ms",
    "session_event_rate",
    "tap_swipe_ratio",
    "avg_swipe_speed",
    "dominant_quadrant_freq",
    "typing_rhythm_var",
]


def extract_if_feature_vector(event: BehaviouralEvent) -> np.ndarray:
    """
    Build the 14-dimensional Isolation Forest input vector from a raw event.

    Missing sub-sensors are zero-padded.  This preserves the fixed feature
    dimensionality required by the fitted sklearn pipeline without introducing
    sentinel values that could bias the anomaly scoring.
    """
    vec = np.zeros(len(IF_FEATURE_NAMES), dtype=np.float64)

    if event.swipe is not None:
        vec[0] = event.swipe.velocity_x
        vec[1] = event.swipe.velocity_y
        vec[2] = event.swipe.duration_ms
        vec[3] = event.swipe.distance_px
        vec[4] = event.swipe.curvature

    if event.tap is not None:
        vec[5] = event.tap.force
        vec[6] = event.tap.contact_area_mm2
        vec[7] = event.tap.dwell_ms
        vec[8] = event.tap.x_norm
        vec[9] = event.tap.y_norm

    if event.gyroscope is not None:
        vec[10] = event.gyroscope.roll_deg_s
        vec[11] = event.gyroscope.pitch_deg_s
        vec[12] = event.gyroscope.yaw_deg_s
        vec[13] = event.gyroscope.magnitude

    return vec


def extract_svm_feature_vector(event: BehaviouralEvent) -> Optional[np.ndarray]:
    """
    Build the 7-dimensional OC-SVM input vector from the interaction pattern.

    Returns None if the event carries no InteractionPatternRecord, allowing
    the caller to gracefully skip OC-SVM scoring.
    """
    if event.interaction_pattern is None:
        return None

    p = event.interaction_pattern
    return np.array(
        [
            p.avg_inter_event_ms,
            p.std_inter_event_ms,
            p.session_event_rate,
            p.tap_swipe_ratio,
            p.avg_swipe_speed,
            p.dominant_quadrant_freq,
            p.typing_rhythm_var,
        ],
        dtype=np.float64,
    )


def _sigmoid_normalise(raw_decision: float) -> float:
    """
    Map an sklearn decision_function output to [0, 1] via a sigmoid transform.

    sklearn's decision_function for IF and OC-SVM returns negative scores for
    outliers and positive for inliers, with 0 as the decision boundary.  We
    negate and sigmoid so that 1.0 means maximally anomalous, 0.0 means
    maximally normal.

        anomaly_score = σ(-raw_decision)
                      = 1 / (1 + exp(raw_decision))
    """
    return float(1.0 / (1.0 + math.exp(raw_decision)))


# ──────────────────────────────────────────────────────────────────────────────
# Per-User Profile State
# ──────────────────────────────────────────────────────────────────────────────

class UserProfile:
    """
    Holds all mutable state that belongs to a single pseudonymous user.

    Thread-safety note: All mutations are protected by asyncio.Lock since
    FastAPI's event loop is single-threaded within each worker process.
    Model fitting is dispatched to a ThreadPoolExecutor via
    asyncio.to_thread() to avoid blocking the event loop during
    potentially long sklearn training calls.
    """

    def __init__(self, user_id_hash: str) -> None:
        self.user_id_hash: str = user_id_hash
        self.lock: asyncio.Lock = asyncio.Lock()

        # Raw event storage (bounded)
        self.if_history:  Deque[np.ndarray] = deque(maxlen=MAX_STORED_EVENTS_PER_USER)
        self.svm_history: Deque[np.ndarray] = deque(maxlen=MAX_STORED_EVENTS_PER_USER)

        # Fitted sklearn pipelines
        self.if_pipeline:  Optional[Pipeline] = None
        self.svm_pipeline: Optional[Pipeline] = None

        # Rolling stats for fallback (updated incrementally)
        self.rolling_if_window:  Deque[np.ndarray] = deque(maxlen=ROLLING_WINDOW_SIZE)

        self.created_at:  datetime = datetime.now(timezone.utc)
        self.last_seen:   datetime = datetime.now(timezone.utc)
        self.fitted_at:   Optional[datetime] = None

    # ── Accessors ──────────────────────────────────────────────────────────────

    @property
    def baseline_count(self) -> int:
        return len(self.if_history)

    @property
    def model_fitted(self) -> bool:
        return self.if_pipeline is not None

    @property
    def has_sufficient_baseline(self) -> bool:
        return len(self.if_history) >= MIN_BASELINE_RECORDS

    # ── History ingestion ──────────────────────────────────────────────────────

    def record_if_vector(self, vec: np.ndarray) -> None:
        self.if_history.append(vec.copy())
        self.rolling_if_window.append(vec.copy())
        self.last_seen = datetime.now(timezone.utc)

    def record_svm_vector(self, vec: np.ndarray) -> None:
        self.svm_history.append(vec.copy())

    # ── Rolling statistical fallback ───────────────────────────────────────────

    def compute_rolling_stats(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Return (mean_vector, std_vector) over the rolling window.

        Returns None if fewer than 2 observations are available (std undefined).

        Mathematical formulation
        ────────────────────────
        Given n observations  x₁, x₂, …, xₙ  where each xᵢ ∈ ℝᵈ :

          μⱼ = (1/n) Σᵢ xᵢⱼ                    (sample mean, feature j)
          σⱼ = √[ (1/(n-1)) Σᵢ (xᵢⱼ - μⱼ)² ]  (Bessel-corrected sample std)
        """
        window = list(self.rolling_if_window)
        n = len(window)
        if n < 2:
            return None

        matrix = np.vstack(window)   # shape (n, d)
        mu     = matrix.mean(axis=0)
        sigma  = matrix.std(axis=0, ddof=1)   # Bessel correction
        return mu, sigma

    def fallback_score(self, vec: np.ndarray) -> Tuple[float, float]:
        """
        Compute a statistical anomaly score for `vec` using rolling μ and σ.

        Returns (anomaly_score, max_z_score).

        Scoring strategy
        ────────────────
        For each feature j compute the z-score:

            zⱼ = (xⱼ - μⱼ) / max(σⱼ, ε)

        where ε = 1e-8 guards against division by zero on constant features.

        The scalar anomaly score is derived from the maximum absolute z-score:

            z_max = max_j |zⱼ|

        We then apply a Chebyshev-inspired soft threshold mapping:

            raw  = clamp( z_max / ZSCORE_ANOMALY_THRESHOLD, 0, 1 )
            score = raw²   (quadratic sharpening near the boundary)

        If no rolling stats are available (fewer than 2 prior events), we
        return (0.5, 0.0) indicating uncertain / unknown risk.
        """
        stats = self.compute_rolling_stats()
        if stats is None:
            return 0.5, 0.0

        mu, sigma = stats
        epsilon = 1e-8

        # Per-feature z-scores
        z_scores = np.abs((vec - mu) / np.maximum(sigma, epsilon))

        # Maximum z-score across all features
        z_max = float(z_scores.max())

        # Normalise to [0, 1] with quadratic sharpening
        ratio = min(z_max / ZSCORE_ANOMALY_THRESHOLD, 1.0)
        anomaly_score = ratio ** 2

        return float(anomaly_score), z_max


# ──────────────────────────────────────────────────────────────────────────────
# Model Fitting Functions (CPU-bound, run in thread pool)
# ──────────────────────────────────────────────────────────────────────────────

def _fit_isolation_forest(X: np.ndarray) -> Pipeline:
    """
    Construct and fit a StandardScaler → IsolationForest sklearn Pipeline.

    Pipeline steps
    ──────────────
    Step 1 – StandardScaler
        Standardises each feature to zero mean and unit variance:
            x̂ⱼ = (xⱼ - μⱼ) / σⱼ
        Prevents high-magnitude features (e.g. distance_px ≈ thousands)
        from dominating the partitioning logic of the forest.

    Step 2 – IsolationForest
        Anomaly score derivation (scikit-learn):
          depth(x, T)  = expected depth of x in isolation tree T
          E[depth(x)]  = average over the ensemble of n_estimators trees
          c(n)         = 2·H(n-1) - (2(n-1)/n)   (normalisation constant)
                         where H(k) = Σᵢ₌₁ᵏ 1/i   (harmonic number)
          score(x)     = 2^( −E[depth(x)] / c(n) )

        score ∈ (0, 1] where values near 0 indicate anomalies (shallow depth).
        sklearn's decision_function returns score − offset, negative → anomaly.
    """
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "isolation_forest",
                IsolationForest(
                    n_estimators=IF_N_ESTIMATORS,
                    max_samples=IF_MAX_SAMPLES,
                    contamination=IF_CONTAMINATION,
                    max_features=IF_MAX_FEATURES,
                    bootstrap=IF_BOOTSTRAP,
                    random_state=IF_RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(X)
    logger.info(
        "IF pipeline fitted on %d samples, %d features.",
        X.shape[0], X.shape[1],
    )
    return pipeline


def _fit_one_class_svm(X: np.ndarray) -> Pipeline:
    """
    Construct and fit a StandardScaler → OneClassSVM sklearn Pipeline.

    Pipeline steps
    ──────────────
    Step 1 – StandardScaler  (identical motivation as above)

    Step 2 – OneClassSVM
        Solves the primal optimisation problem:

            min_{w, ξ, ρ}  ½‖w‖² + (1/νn) Σᵢ ξᵢ − ρ
            subject to     ⟨w, φ(xᵢ)⟩ ≥ ρ − ξᵢ,   ξᵢ ≥ 0

        where φ maps inputs to the RKHS induced by the RBF kernel:

            K(x, x') = exp( −γ ‖x − x'‖² )
            γ = 1 / (n_features · Var[X])   (gamma="scale")

        The decision function f(x) = ⟨w, φ(x)⟩ − ρ.
        Positive values → inlier;  negative → outlier.

        ν ∈ (0, 1] is an upper bound on the fraction of training anomalies
        and a lower bound on the support vector fraction.
    """
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "one_class_svm",
                OneClassSVM(
                    kernel=OC_SVM_KERNEL,
                    nu=OC_SVM_NU,
                    gamma=OC_SVM_GAMMA,
                ),
            ),
        ]
    )
    pipeline.fit(X)
    logger.info(
        "OC-SVM pipeline fitted on %d samples, %d features.",
        X.shape[0], X.shape[1],
    )
    return pipeline


# ──────────────────────────────────────────────────────────────────────────────
# User Registry (in-process store; swap for Redis in multi-worker deployments)
# ──────────────────────────────────────────────────────────────────────────────

class UserRegistry:
    """
    Thread-safe (asyncio) registry that maps user_id_hash → UserProfile.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, UserProfile] = {}
        self._global_lock: asyncio.Lock = asyncio.Lock()
        self._service_start: float = time.monotonic()

    @staticmethod
    def _hash_user_id(raw_user_id: str) -> str:
        """
        Pseudonymise the caller-supplied user identifier with SHA-256.

        We hash immediately on ingestion so that raw user IDs never persist
        in memory or logs beyond the outermost request handler boundary.
        """
        return hashlib.sha256(raw_user_id.encode("utf-8")).hexdigest()

    async def get_or_create(self, raw_user_id: str) -> UserProfile:
        uid_hash = self._hash_user_id(raw_user_id)
        async with self._global_lock:
            if uid_hash not in self._profiles:
                self._profiles[uid_hash] = UserProfile(uid_hash)
                logger.info("Created new user profile: %s…", uid_hash[:16])
            return self._profiles[uid_hash]

    async def get(self, raw_user_id: str) -> Optional[UserProfile]:
        uid_hash = self._hash_user_id(raw_user_id)
        return self._profiles.get(uid_hash)

    @property
    def registered_users(self) -> int:
        return len(self._profiles)

    @property
    def fitted_users(self) -> int:
        return sum(1 for p in self._profiles.values() if p.model_fitted)

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._service_start


# ──────────────────────────────────────────────────────────────────────────────
# Core Scoring Engine
# ──────────────────────────────────────────────────────────────────────────────

class BehaviouralScoringEngine:
    """
    Stateless scoring logic that operates against a given UserProfile.

    Separating scoring from profile management makes unit testing straightforward
    and keeps the FastAPI handlers thin.
    """

    # ── Isolation Forest scoring ───────────────────────────────────────────────

    @staticmethod
    def _score_isolation_forest(
        profile: UserProfile,
        vec: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Run the fitted IF pipeline against a single feature vector.

        Returns (anomaly_score ∈ [0,1], raw_decision_function_value).

        Raw decision function from sklearn IF:
          positive → inlier  (score < threshold → labelled +1 by predict)
          negative → outlier (score < threshold → labelled -1 by predict)

        We apply _sigmoid_normalise to map to [0, 1] as an anomaly probability.
        """
        assert profile.if_pipeline is not None
        raw = float(profile.if_pipeline.decision_function(vec.reshape(1, -1))[0])
        return _sigmoid_normalise(raw), raw

    # ── OC-SVM scoring ────────────────────────────────────────────────────────

    @staticmethod
    def _score_one_class_svm(
        profile: UserProfile,
        vec: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Run the fitted OC-SVM pipeline against a single feature vector.

        Returns (anomaly_score ∈ [0,1], raw_decision_function_value).

        The OC-SVM decision function is the signed distance from the separating
        hyperplane in the RKHS:

            f(x) = Σᵢ αᵢ K(xᵢ, x) − ρ

        Positive → inlier;  negative → outlier.
        """
        assert profile.svm_pipeline is not None
        raw = float(profile.svm_pipeline.decision_function(vec.reshape(1, -1))[0])
        return _sigmoid_normalise(raw), raw

    # ── Blended scoring ───────────────────────────────────────────────────────

    @staticmethod
    def _blend_scores(if_score: float, svm_score: float) -> float:
        """
        Compute the weighted linear combination of IF and OC-SVM scores.

            blended = IF_BLEND_WEIGHT · score_IF + OC_SVM_BLEND_WEIGHT · score_SVM

        Both weights are compile-time constants that sum to 1.0 (asserted at
        module load time).
        """
        return IF_BLEND_WEIGHT * if_score + OC_SVM_BLEND_WEIGHT * svm_score

    # ── Primary scoring dispatch ───────────────────────────────────────────────

    async def score(
        self,
        profile: UserProfile,
        event: BehaviouralEvent,
    ) -> Dict[str, Any]:
        """
        Produce a complete scoring result dict for one event.

        Decision logic
        ──────────────
        1. Extract feature vectors for IF and (optionally) OC-SVM.
        2. Record vectors in the profile's history buffers.
        3. If the profile has a fitted IF pipeline:
             a. Score via IF.
             b. If the event carries an interaction pattern AND the profile has
                a fitted SVM pipeline, score via OC-SVM and blend.
             c. Otherwise use IF score alone.
           Else if sufficient baseline exists but models not yet fitted:
             Trigger background fitting and use statistical fallback for now.
           Else:
             Use statistical fallback.
        4. Convert continuous anomaly_score to verdict using threshold 0.5.
        """
        t0 = time.monotonic()

        if_vec  = extract_if_feature_vector(event)
        svm_vec = extract_svm_feature_vector(event)

        async with profile.lock:
            profile.record_if_vector(if_vec)
            if svm_vec is not None:
                profile.record_svm_vector(svm_vec)

            # ── Case 1: ML models fitted ──────────────────────────────────────
            if profile.model_fitted:
                if_anomaly_score, if_raw = self._score_isolation_forest(profile, if_vec)

                svm_anomaly_score: Optional[float] = None
                svm_raw:           Optional[float] = None

                if svm_vec is not None and profile.svm_pipeline is not None:
                    svm_anomaly_score, svm_raw = self._score_one_class_svm(profile, svm_vec)
                    blended_score = self._blend_scores(if_anomaly_score, svm_anomaly_score)
                    pipeline_used = AnomalyPipeline.BLENDED
                else:
                    blended_score = if_anomaly_score
                    pipeline_used = AnomalyPipeline.ISOLATION_FOREST

                verdict = (
                    AnomalyVerdict.ANOMALY if blended_score >= 0.5
                    else AnomalyVerdict.NORMAL
                )

                elapsed_ms = (time.monotonic() - t0) * 1000.0
                return {
                    "event_id":           event.event_id,
                    "user_id_hash":       profile.user_id_hash,
                    "verdict":            verdict,
                    "pipeline_used":      pipeline_used,
                    "anomaly_score":      round(blended_score, 6),
                    "if_score":           round(if_raw, 6),
                    "svm_score":          round(svm_raw, 6) if svm_raw is not None else None,
                    "stat_zscore":        None,
                    "baseline_count":     profile.baseline_count,
                    "model_fitted":       True,
                    "processing_time_ms": round(elapsed_ms, 3),
                    "scored_at":          datetime.now(timezone.utc),
                }

            # ── Case 2: Statistical fallback ──────────────────────────────────
            fallback_score, z_max = profile.fallback_score(if_vec)

            # Rolling stats require ≥ 2 observations to compute a valid std.
            # Fewer than 2 events in the rolling window means Bessel-corrected
            # standard deviation is undefined, so we cannot produce a meaningful
            # z-score.  Emit UNKNOWN until the window is populated.
            rolling_stats_available = profile.compute_rolling_stats() is not None
            if not rolling_stats_available:
                verdict = AnomalyVerdict.UNKNOWN
            elif fallback_score >= 0.5:
                verdict = AnomalyVerdict.ANOMALY
            else:
                verdict = AnomalyVerdict.NORMAL

            elapsed_ms = (time.monotonic() - t0) * 1000.0
            return {
                "event_id":           event.event_id,
                "user_id_hash":       profile.user_id_hash,
                "verdict":            verdict,
                "pipeline_used":      AnomalyPipeline.STATISTICAL_FALLBACK,
                "anomaly_score":      round(fallback_score, 6),
                "if_score":           None,
                "svm_score":          None,
                "stat_zscore":        round(z_max, 6),
                "baseline_count":     profile.baseline_count,
                "model_fitted":       False,
                "processing_time_ms": round(elapsed_ms, 3),
                "scored_at":          datetime.now(timezone.utc),
            }


# ──────────────────────────────────────────────────────────────────────────────
# Model Training Manager
# ──────────────────────────────────────────────────────────────────────────────

class ModelTrainer:
    """
    Orchestrates asynchronous model fitting for a single user profile.

    All CPU-bound sklearn work is dispatched with asyncio.to_thread() so the
    FastAPI event loop remains unblocked during potentially long training runs.
    """

    @staticmethod
    async def fit_user_models(profile: UserProfile) -> TrainingResponse:
        """
        Fit (or re-fit) both ML pipelines for a given user profile.

        Returns a TrainingResponse summarising the outcome.

        Raises ValueError if the profile has insufficient history for either
        pipeline.  Callers should catch this and return an appropriate HTTP 422.
        """
        async with profile.lock:
            if_samples = len(profile.if_history)
            if if_samples < MIN_BASELINE_RECORDS:
                raise ValueError(
                    f"Insufficient IF history: {if_samples} events available, "
                    f"minimum required is {MIN_BASELINE_RECORDS}."
                )

            # Materialise numpy arrays *inside* the lock
            if_matrix  = np.vstack(list(profile.if_history))
            svm_matrix = (
                np.vstack(list(profile.svm_history))
                if len(profile.svm_history) >= MIN_BASELINE_RECORDS
                else None
            )

        # ── CPU-bound fitting dispatched off event loop ────────────────────────
        if_pipeline = await asyncio.to_thread(_fit_isolation_forest, if_matrix)

        svm_pipeline: Optional[Pipeline] = None
        svm_fitted = False
        svm_n = 0
        if svm_matrix is not None:
            svm_pipeline = await asyncio.to_thread(_fit_one_class_svm, svm_matrix)
            svm_fitted = True
            svm_n = svm_matrix.shape[0]

        # ── Write fitted pipelines back under lock ─────────────────────────────
        async with profile.lock:
            profile.if_pipeline  = if_pipeline
            profile.svm_pipeline = svm_pipeline
            profile.fitted_at    = datetime.now(timezone.utc)

        logger.info(
            "Models fitted for user %s… (IF=%d smp, SVM=%d smp)",
            profile.user_id_hash[:16],
            if_matrix.shape[0],
            svm_n,
        )

        return TrainingResponse(
            user_id_hash=profile.user_id_hash,
            if_fitted=True,
            svm_fitted=svm_fitted,
            training_samples_if=if_matrix.shape[0],
            training_samples_svm=svm_n,
            fitted_at=profile.fitted_at,
        )

    @staticmethod
    async def background_fit_if_ready(profile: UserProfile) -> None:
        """
        Silently attempt background fitting when a profile crosses the baseline
        threshold.  Any exception is caught and logged (never propagated) because
        this is called from a FastAPI BackgroundTask.
        """
        if not profile.has_sufficient_baseline or profile.model_fitted:
            return
        try:
            await ModelTrainer.fit_user_models(profile)
        except Exception as exc:
            logger.warning(
                "Background fit failed for %s…: %s",
                profile.user_id_hash[:16],
                exc,
            )


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Behavioural Analytics Engine",
    description=(
        "Runtime behavioural anomaly detection service using Isolation Forest "
        "and One-Class SVM, with rolling statistical fallback for cold-start users."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

# ── Singleton dependencies ────────────────────────────────────────────────────
_registry = UserRegistry()
_engine   = BehaviouralScoringEngine()
_trainer  = ModelTrainer()


def get_registry() -> UserRegistry:
    return _registry


def get_engine() -> BehaviouralScoringEngine:
    return _engine


def get_trainer() -> ModelTrainer:
    return _trainer


# ──────────────────────────────────────────────────────────────────────────────
# Middleware: Request Timing
# ──────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    t0 = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - t0) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.3f}"
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Exception Handlers
# ──────────────────────────────────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. See server logs."},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    tags=["Operations"],
)
async def health_check(
    registry: UserRegistry = Depends(get_registry),
) -> HealthResponse:
    """
    Returns basic service health metrics.  Useful as a liveness/readiness probe.
    """
    return HealthResponse(
        status="ok",
        registered_users=registry.registered_users,
        fitted_users=registry.fitted_users,
        uptime_seconds=round(registry.uptime_seconds, 2),
    )


@app.post(
    "/score",
    response_model=AnomalyScore,
    status_code=status.HTTP_200_OK,
    summary="Score a single behavioural event",
    tags=["Scoring"],
)
async def score_event(
    event:            BehaviouralEvent,
    background_tasks: BackgroundTasks,
    registry:         UserRegistry            = Depends(get_registry),
    engine:           BehaviouralScoringEngine = Depends(get_engine),
) -> AnomalyScore:
    """
    Primary scoring endpoint.

    Accepts a BehaviouralEvent payload, scores it against the user's current
    anomaly detection pipeline, and returns an AnomalyScore response.

    If the user's profile has just crossed the minimum baseline threshold and
    models have not yet been fitted, a background fitting task is enqueued
    automatically.  Subsequent calls within the same server process will use
    the newly fitted models.
    """
    profile = await registry.get_or_create(event.user_id)
    result  = await engine.score(profile, event)

    # Trigger background fitting when the user has just reached baseline
    if profile.has_sufficient_baseline and not profile.model_fitted:
        background_tasks.add_task(
            ModelTrainer.background_fit_if_ready,
            profile,
        )

    return AnomalyScore(**result)


@app.post(
    "/train",
    response_model=TrainingResponse,
    status_code=status.HTTP_200_OK,
    summary="Explicitly (re-)fit ML models for a user",
    tags=["Training"],
)
async def train_user_models(
    request:  TrainingRequest,
    registry: UserRegistry = Depends(get_registry),
    trainer:  ModelTrainer  = Depends(get_trainer),
) -> TrainingResponse:
    """
    Trigger a synchronous (awaited) model fit for the specified user.

    Returns HTTP 422 if the user has insufficient baseline history.
    Useful for backfill scenarios or forced model refresh after known
    behavioural regime changes (e.g. account recovery, device upgrade).
    """
    profile = await registry.get_or_create(request.user_id)

    if not profile.has_sufficient_baseline:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"User profile has only {profile.baseline_count} events. "
                f"Minimum required: {MIN_BASELINE_RECORDS}."
            ),
        )

    return await trainer.fit_user_models(profile)


@app.get(
    "/user/{user_id}/status",
    summary="Retrieve profiling status for a user",
    tags=["Scoring"],
)
async def user_status(
    user_id:  str,
    registry: UserRegistry = Depends(get_registry),
) -> JSONResponse:
    """
    Returns profile metadata for a given user without scoring an event.

    Useful for monitoring dashboard integrations and operational tooling.
    """
    profile = await registry.get(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found.  No events have been scored for this user.",
        )

    async with profile.lock:
        rolling_stats = profile.compute_rolling_stats()
        rolling_summary: Optional[Dict[str, Any]] = None
        if rolling_stats is not None:
            mu, sigma = rolling_stats
            rolling_summary = {
                "window_size":    len(profile.rolling_if_window),
                "feature_means":  {
                    name: round(float(mu[i]), 6)
                    for i, name in enumerate(IF_FEATURE_NAMES)
                },
                "feature_stds":   {
                    name: round(float(sigma[i]), 6)
                    for i, name in enumerate(IF_FEATURE_NAMES)
                },
            }

        return JSONResponse(
            content={
                "user_id_hash":         profile.user_id_hash,
                "baseline_count":       profile.baseline_count,
                "min_baseline_records": MIN_BASELINE_RECORDS,
                "model_fitted":         profile.model_fitted,
                "if_pipeline_ready":    profile.if_pipeline is not None,
                "svm_pipeline_ready":   profile.svm_pipeline is not None,
                "rolling_stats":        rolling_summary,
                "created_at":           profile.created_at.isoformat(),
                "last_seen":            profile.last_seen.isoformat(),
                "fitted_at":            profile.fitted_at.isoformat() if profile.fitted_at else None,
            }
        )


@app.get(
    "/config",
    summary="Expose current engine hyper-parameters",
    tags=["Operations"],
)
async def get_config() -> JSONResponse:
    """
    Returns the active hyper-parameter configuration for observability purposes.
    Does not expose fitted model internals.
    """
    return JSONResponse(
        content={
            "min_baseline_records":      MIN_BASELINE_RECORDS,
            "isolation_forest": {
                "n_estimators":  IF_N_ESTIMATORS,
                "max_samples":   IF_MAX_SAMPLES,
                "contamination": IF_CONTAMINATION,
                "max_features":  IF_MAX_FEATURES,
                "bootstrap":     IF_BOOTSTRAP,
                "random_state":  IF_RANDOM_STATE,
            },
            "one_class_svm": {
                "kernel": OC_SVM_KERNEL,
                "nu":     OC_SVM_NU,
                "gamma":  OC_SVM_GAMMA,
            },
            "statistical_fallback": {
                "rolling_window_size":     ROLLING_WINDOW_SIZE,
                "zscore_anomaly_threshold": ZSCORE_ANOMALY_THRESHOLD,
                "chebyshev_k":             CHEBYSHEV_K,
            },
            "blending": {
                "if_weight":      IF_BLEND_WEIGHT,
                "oc_svm_weight":  OC_SVM_BLEND_WEIGHT,
            },
            "feature_names": {
                "isolation_forest": IF_FEATURE_NAMES,
                "one_class_svm":    SVM_FEATURE_NAMES,
            },
        }
    )


# ──────────────────────────────────────────────────────────────────────────────
# Startup / Shutdown Lifecycle
# ──────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Behavioural Analytics Engine starting up. "
        "MIN_BASELINE_RECORDS=%d  IF_N_ESTIMATORS=%d  OC_SVM_NU=%.3f",
        MIN_BASELINE_RECORDS,
        IF_N_ESTIMATORS,
        OC_SVM_NU,
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info(
        "Behavioural Analytics Engine shutting down. "
        "Registered users: %d  Fitted users: %d",
        _registry.registered_users,
        _registry.fitted_users,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "behavioral_analytics_engine:app",
        host="0.0.0.0",
        port=8080,
        workers=1,           # Single worker: all state is in-process
        loop="asyncio",
        log_level="info",
        access_log=True,
        reload=False,
    )
