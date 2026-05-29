"""
generate_training_data.py
─────────────────────────────────────────────────────────────────────────────
Synthesises a 10,000-row offline dataset for behaviour-tracking parameter
calibration.  No real customer data is used at any point.

Schema
──────
session_id          – unique UUID per row
user_id             – one of 50 synthetic test users (U001 … U050)
timestamp           – ISO-8601 datetime spread over a 30-day window
platform            – iOS | Android | Web

Touch / gesture parameters (continuous)
  swipe_rate          – swipes per second          normal: [0.5, 3.5]
  tap_pressure        – normalised pressure        normal: [0.2, 1.0]
  touch_duration_ms   – ms per touch event         normal: [80, 600]
  gesture_speed       – px/s                       normal: [50, 800]
  finger_count_avg    – mean simultaneous fingers  normal: [1.0, 2.5]
  scroll_velocity     – px/s                       normal: [20, 500]

Coordination / behavioural parameters (continuous)
  inter_event_gap_ms  – ms between events          normal: [100, 2000]
  coordination_score  – 0-1 composite              normal: [0.55, 1.0]
  session_duration_s  – total session length       normal: [30, 1800]
  error_rate          – mis-tap / error fraction   normal: [0.0, 0.15]
  rhythm_consistency  – 0-1 temporal regularity    normal: [0.50, 1.0]

Label
  is_anomaly          – bool  (5 % injection → session-hijacking profile)
  anomaly_type        – str   "hijack" | "normal"

Anomaly injection (session-hijacking signature)
  • swipe_rate         ×  U(3, 6)   → rapid, automated swiping
  • coordination_score × U(0.1, 0.4)→ low coordination (bot-like)
  • inter_event_gap_ms × U(0.05, 0.2)→ unnaturally tight timing
  • rhythm_consistency  → near-zero (erratic/mechanical)
  • gesture_speed      ×  U(2, 5)   → hyper-fast gestures
─────────────────────────────────────────────────────────────────────────────
"""

import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ── Reproducibility ────────────────────────────────────────────────────────
RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

# ── Config ─────────────────────────────────────────────────────────────────
N_ROWS        = 10_000
N_USERS       = 50
ANOMALY_RATE  = 0.05          # 5 % session-hijacking anomaly injection
START_DATE    = datetime(2024, 1, 1)
DATE_RANGE_D  = 30            # spread sessions over 30 days

PLATFORMS     = ["iOS", "Android", "Web"]
PLATFORM_PROBS = [0.45, 0.40, 0.15]


# ══════════════════════════════════════════════════════════════════════════
# Helper: clipped normal draw
# ══════════════════════════════════════════════════════════════════════════
def clipped_normal(
    mean: float,
    std: float,
    low: float,
    high: float,
    size: int,
) -> np.ndarray:
    """Draw from N(mean, std) and hard-clip to [low, high]."""
    return np.clip(rng.normal(mean, std, size), low, high)


# ══════════════════════════════════════════════════════════════════════════
# 1. User pool
# ══════════════════════════════════════════════════════════════════════════
user_ids = [f"U{i:03d}" for i in range(1, N_USERS + 1)]

# Per-user baseline offsets so users differ slightly from each other
user_offsets = {
    uid: {
        "swipe_rate":         rng.uniform(-0.3, 0.3),
        "tap_pressure":       rng.uniform(-0.05, 0.05),
        "touch_duration_ms":  rng.uniform(-30, 30),
        "gesture_speed":      rng.uniform(-50, 50),
        "coordination_score": rng.uniform(-0.05, 0.05),
        "rhythm_consistency": rng.uniform(-0.05, 0.05),
    }
    for uid in user_ids
}


# ══════════════════════════════════════════════════════════════════════════
# 2. Base (normal) feature generation
# ══════════════════════════════════════════════════════════════════════════
def generate_normal_features(n: int) -> dict:
    return {
        "swipe_rate":          clipped_normal(1.8,  0.6,  0.5,   3.5,   n),
        "tap_pressure":        clipped_normal(0.62, 0.12, 0.2,   1.0,   n),
        "touch_duration_ms":   clipped_normal(220,  80,   80,    600,   n),
        "gesture_speed":       clipped_normal(310,  120,  50,    800,   n),
        "finger_count_avg":    clipped_normal(1.3,  0.25, 1.0,   2.5,   n),
        "scroll_velocity":     clipped_normal(200,  90,   20,    500,   n),
        "inter_event_gap_ms":  clipped_normal(600,  250,  100,   2000,  n),
        "coordination_score":  clipped_normal(0.80, 0.10, 0.55,  1.0,   n),
        "session_duration_s":  clipped_normal(420,  300,  30,    1800,  n),
        "error_rate":          clipped_normal(0.04, 0.03, 0.0,   0.15,  n),
        "rhythm_consistency":  clipped_normal(0.78, 0.10, 0.50,  1.0,   n),
    }


# ══════════════════════════════════════════════════════════════════════════
# 3. Anomaly (session-hijacking) mutation
# ══════════════════════════════════════════════════════════════════════════
def inject_hijack_anomaly(feats: dict, idx: np.ndarray) -> dict:
    """
    Mutate the anomaly rows in-place to reflect a session-hijacking profile:
      • swipe_rate         multiplied by a large random factor
      • gesture_speed      multiplied by a large random factor
      • coordination_score multiplied by a small random factor → drops sharply
      • inter_event_gap_ms multiplied by a small random factor → very tight
      • rhythm_consistency → near-zero erratic pattern
    """
    n_anom = len(idx)

    feats["swipe_rate"][idx] = np.clip(
        feats["swipe_rate"][idx] * rng.uniform(3.0, 6.0, n_anom),
        3.5, 25.0,
    )
    feats["gesture_speed"][idx] = np.clip(
        feats["gesture_speed"][idx] * rng.uniform(2.0, 5.0, n_anom),
        800, 4000,
    )
    feats["coordination_score"][idx] = np.clip(
        feats["coordination_score"][idx] * rng.uniform(0.10, 0.40, n_anom),
        0.0, 0.35,
    )
    feats["inter_event_gap_ms"][idx] = np.clip(
        feats["inter_event_gap_ms"][idx] * rng.uniform(0.05, 0.20, n_anom),
        5, 80,
    )
    feats["rhythm_consistency"][idx] = rng.uniform(0.01, 0.18, n_anom)

    # Hijacked sessions tend to be short-lived before detection
    feats["session_duration_s"][idx] = clipped_normal(90, 40, 10, 300, n_anom)

    # Error rate may spike or plummet (automated → 0; confused → high)
    feats["error_rate"][idx] = rng.choice(
        [
            rng.uniform(0.0, 0.02, n_anom),    # bot: nearly zero errors
            rng.uniform(0.25, 0.60, n_anom),   # panic / confused pattern
        ],
        p=[0.55, 0.45],
    )

    return feats


# ══════════════════════════════════════════════════════════════════════════
# 4. Assemble the DataFrame
# ══════════════════════════════════════════════════════════════════════════
def build_dataset() -> pd.DataFrame:
    # ── Identifiers ────────────────────────────────────────────────────
    session_ids = [str(uuid.uuid4()) for _ in range(N_ROWS)]
    assigned_users = rng.choice(user_ids, size=N_ROWS)
    platforms = rng.choice(PLATFORMS, size=N_ROWS, p=PLATFORM_PROBS)

    # ── Timestamps ─────────────────────────────────────────────────────
    seconds_offset = rng.integers(0, DATE_RANGE_D * 86_400, size=N_ROWS)
    timestamps = [
        (START_DATE + timedelta(seconds=int(s))).isoformat()
        for s in seconds_offset
    ]

    # ── Features ───────────────────────────────────────────────────────
    feats = generate_normal_features(N_ROWS)

    # Apply per-user offsets (personalisation)
    for i, uid in enumerate(assigned_users):
        off = user_offsets[uid]
        feats["swipe_rate"][i]         = np.clip(feats["swipe_rate"][i]         + off["swipe_rate"],         0.5,  3.5)
        feats["tap_pressure"][i]       = np.clip(feats["tap_pressure"][i]       + off["tap_pressure"],       0.2,  1.0)
        feats["touch_duration_ms"][i]  = np.clip(feats["touch_duration_ms"][i]  + off["touch_duration_ms"],  80,   600)
        feats["gesture_speed"][i]      = np.clip(feats["gesture_speed"][i]      + off["gesture_speed"],      50,   800)
        feats["coordination_score"][i] = np.clip(feats["coordination_score"][i] + off["coordination_score"], 0.55, 1.0)
        feats["rhythm_consistency"][i] = np.clip(feats["rhythm_consistency"][i] + off["rhythm_consistency"], 0.50, 1.0)

    # ── Anomaly injection ──────────────────────────────────────────────
    n_anomalies  = int(N_ROWS * ANOMALY_RATE)
    anomaly_idx  = rng.choice(N_ROWS, size=n_anomalies, replace=False)
    is_anomaly   = np.zeros(N_ROWS, dtype=bool)
    is_anomaly[anomaly_idx] = True

    feats = inject_hijack_anomaly(feats, anomaly_idx)

    # ── Combine ────────────────────────────────────────────────────────
    df = pd.DataFrame({
        "session_id":         session_ids,
        "user_id":            assigned_users,
        "timestamp":          timestamps,
        "platform":           platforms,
        # touch parameters
        "swipe_rate":         feats["swipe_rate"].round(4),
        "tap_pressure":       feats["tap_pressure"].round(4),
        "touch_duration_ms":  feats["touch_duration_ms"].round(2),
        "gesture_speed":      feats["gesture_speed"].round(2),
        "finger_count_avg":   feats["finger_count_avg"].round(3),
        "scroll_velocity":    feats["scroll_velocity"].round(2),
        # behavioural parameters
        "inter_event_gap_ms": feats["inter_event_gap_ms"].round(2),
        "coordination_score": feats["coordination_score"].round(4),
        "session_duration_s": feats["session_duration_s"].round(1),
        "error_rate":         feats["error_rate"].round(4),
        "rhythm_consistency": feats["rhythm_consistency"].round(4),
        # labels
        "is_anomaly":         is_anomaly,
        "anomaly_type":       np.where(is_anomaly, "hijack", "normal"),
    })

    # Sort by timestamp for a realistic time-series feel
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


# ══════════════════════════════════════════════════════════════════════════
# 5. Validation summary
# ══════════════════════════════════════════════════════════════════════════
def print_summary(df: pd.DataFrame) -> None:
    sep = "─" * 60
    print(sep)
    print("  Synthetic Behaviour Tracking Dataset — Summary")
    print(sep)
    print(f"  Rows            : {len(df):,}")
    print(f"  Unique users    : {df['user_id'].nunique()}")
    print(f"  Date range      : {df['timestamp'].min()}  →  {df['timestamp'].max()}")
    print(f"  Platforms       : {df['platform'].value_counts().to_dict()}")
    print()
    n_anom = df["is_anomaly"].sum()
    print(f"  Anomaly rows    : {n_anom:,}  ({n_anom/len(df)*100:.2f} %)")
    print(f"  Normal rows     : {(~df['is_anomaly']).sum():,}")
    print()

    cont_cols = [
        "swipe_rate", "tap_pressure", "touch_duration_ms", "gesture_speed",
        "finger_count_avg", "scroll_velocity", "inter_event_gap_ms",
        "coordination_score", "session_duration_s", "error_rate",
        "rhythm_consistency",
    ]
    normal_df = df[~df["is_anomaly"]]
    hijack_df = df[df["is_anomaly"]]

    print(f"  {'Feature':<22}  {'Normal mean':>12}  {'Hijack mean':>12}")
    print(f"  {'─'*22}  {'─'*12}  {'─'*12}")
    for col in cont_cols:
        nm = normal_df[col].mean()
        hm = hijack_df[col].mean()
        print(f"  {col:<22}  {nm:>12.4f}  {hm:>12.4f}")
    print(sep)


# ══════════════════════════════════════════════════════════════════════════
# 6. Entry point
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    output_path = "behaviour_tracking_synthetic.csv"

    print("Generating synthetic dataset …")
    df = build_dataset()
    df.to_csv(output_path, index=False)
    print(f"Saved → {output_path}")
    print()
    print_summary(df)
