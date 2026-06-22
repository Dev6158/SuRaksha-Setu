"""
forensic_engine.py
==================
Production-grade Active Document Fraud Detection Engine.

Algorithms Implemented:
  1. Error Level Analysis (ELA)         — JPEG re-compression residual amplification
  2. FFT Moiré / Screen-Recapture       — Frequency-domain periodicity fingerprinting
  3. Unified FastAPI endpoint            — Concurrent async analysis + Pydantic schemas

Author : Computer Vision Research Scientist
Python : 3.11+
Deps   : fastapi, uvicorn, opencv-python-headless, numpy, pillow, python-multipart
"""

from __future__ import annotations

import asyncio
import io
import logging
import math
import time
import uuid
from typing import Annotated, List, Optional, Tuple

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("forensic_engine")

# ---------------------------------------------------------------------------
# ── CONSTANTS ────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

# ELA
ELA_JPEG_QUALITY: int = 85          # Re-compression quality target (percent)
ELA_AMPLIFICATION_SCALE: float = 15.0  # Multiplicative amplifier for residual map
ELA_ANOMALY_PERCENTILE: float = 95.0   # Residual intensity above which a pixel is "suspicious"
ELA_MIN_CLUSTER_AREA_PX: int = 50      # Minimum blob area (px²) to classify as an anomaly cluster

# FFT Moiré
FFT_RADIAL_BINS: int = 256             # Radial buckets for power-spectrum ring analysis
FFT_DC_EXCLUSION_RADIUS: int = 5       # Pixels around DC (0,0) to zero-out (ignore illumination)
FFT_PERIODICITY_THRESHOLD: float = 3.5 # σ above mean power ring to flag as periodic
FFT_MOIRE_FREQ_BAND_LOW: float = 0.05  # Normalised spatial frequency lower bound  (0–0.5 Nyquist)
FFT_MOIRE_FREQ_BAND_HIGH: float = 0.45 # Normalised spatial frequency upper bound
FFT_PEAK_NEIGHBOURHOOD: int = 7        # Radius (px) around a peak used for local-max suppression

# Supported ingest MIME types
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
}

MAX_UPLOAD_BYTES: int = 30 * 1024 * 1024  # 30 MB hard ceiling


# ---------------------------------------------------------------------------
# ── PYDANTIC SCHEMAS ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class ELAResult(BaseModel):
    """Structured output from the Error Level Analysis pipeline."""

    mean_residual_intensity: float = Field(
        ..., description="Mean absolute pixel-level residual across all channels (0–255)"
    )
    std_residual_intensity: float = Field(
        ..., description="Standard deviation of the residual intensity map"
    )
    max_residual_intensity: float = Field(
        ..., description="Maximum residual value in the amplified map"
    )
    anomaly_pixel_ratio: float = Field(
        ..., description="Fraction of pixels exceeding the anomaly threshold"
    )
    anomaly_cluster_count: int = Field(
        ..., description="Number of spatially contiguous anomaly blobs detected"
    )
    anomaly_cluster_areas_px: List[int] = Field(
        ..., description="Area (px²) of each individual anomaly cluster"
    )
    ela_score: float = Field(
        ...,
        description=(
            "Composite fraud-likelihood score in [0, 1] derived from residual "
            "statistics and cluster density"
        ),
    )
    flagged: bool = Field(..., description="True when ELA score exceeds fraud threshold")


class FFTMoireResult(BaseModel):
    """Structured output from the FFT screen-recapture detection pipeline."""

    dominant_peak_frequency: float = Field(
        ..., description="Normalised spatial frequency of the strongest periodic component"
    )
    dominant_peak_power: float = Field(
        ..., description="Spectral power at the dominant periodic peak"
    )
    periodicity_sigma: float = Field(
        ...,
        description=(
            "How many standard deviations the dominant peak sits above the "
            "background ring mean — higher = stronger periodicity"
        ),
    )
    moire_band_energy_ratio: float = Field(
        ...,
        description=(
            "Fraction of total spectral energy contained within the Moiré "
            "frequency band relative to whole-spectrum energy"
        ),
    )
    detected_peak_frequencies: List[float] = Field(
        ..., description="All periodic frequencies flagged above the σ threshold"
    )
    fft_score: float = Field(
        ...,
        description="Composite screen-recapture likelihood score in [0, 1]",
    )
    flagged: bool = Field(
        ..., description="True when FFT score exceeds screen-recapture threshold"
    )


class ForensicsResponse(BaseModel):
    """Top-level API response schema."""

    request_id: str = Field(..., description="UUID4 tracing token for this analysis")
    processing_time_ms: float = Field(..., description="Wall-clock latency in milliseconds")
    image_width_px: int
    image_height_px: int
    image_channels: int
    ela: ELAResult
    fft: FFTMoireResult
    overall_fraud_score: float = Field(
        ...,
        description=(
            "Weighted combination of ELA and FFT scores. "
            "Values ≥ 0.5 indicate probable tampering or screen-recapture."
        ),
    )
    verdict: str = Field(
        ...,
        description="Human-readable verdict: AUTHENTIC | SUSPICIOUS | FRAUDULENT",
    )


# ---------------------------------------------------------------------------
# ── ELA PIPELINE ─────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def run_ela(
    image_bgr: np.ndarray,
    jpeg_quality: int = ELA_JPEG_QUALITY,
    amplification: float = ELA_AMPLIFICATION_SCALE,
    anomaly_percentile: float = ELA_ANOMALY_PERCENTILE,
    min_cluster_area: int = ELA_MIN_CLUSTER_AREA_PX,
) -> Tuple[ELAResult, np.ndarray]:
    """
    Error Level Analysis pipeline.

    Mathematical overview
    ---------------------
    Given an input image I ∈ ℝ^{H×W×C} (uint8, range [0,255]):

    1. Re-encode I at quality q → I_q  (lossy JPEG round-trip)
    2. Residual map:
           R(h,w,c) = |I(h,w,c) − I_q(h,w,c)|          ∈ [0, 255]
    3. Amplified visualisation:
           R_amp(h,w,c) = clip(R(h,w,c) · α, 0, 255)    α = amplification factor
    4. Grayscale collapse:
           G(h,w) = 0.299·R(h,w,0) + 0.587·R(h,w,1) + 0.114·R(h,w,2)
    5. Threshold at percentile p:
           T = percentile_p(G)
           mask(h,w) = G(h,w) > T
    6. Connected-components analysis on `mask` → cluster blobs
    7. ELA score:
           ela_score = sigmoid(
               0.4 · normalise(μ_R) +
               0.3 · normalise(σ_R) +
               0.3 · anomaly_ratio
           )
       where normalise maps [0,255] → [0,1].

    Parameters
    ----------
    image_bgr       : OpenCV BGR uint8 image array of shape (H, W, 3).
    jpeg_quality    : Re-compression quality [1–95]. Lower = more lossy baseline.
    amplification   : Multiplicative scale for the residual map visualisation.
    anomaly_percentile : Percentile of residual intensity used as anomaly threshold.
    min_cluster_area: Minimum connected-component area to count as an anomaly cluster.

    Returns
    -------
    ela_result : ELAResult Pydantic model.
    ela_visual : uint8 BGR array of shape (H, W, 3) — amplified residual heatmap.
    """
    H, W, C = image_bgr.shape
    log.debug("ELA | input shape=(%d,%d,%d) quality=%d", H, W, C, jpeg_quality)

    # ── Step 1 : in-memory JPEG round-trip ───────────────────────────────────
    # Convert BGR → RGB for PIL then encode to an in-memory byte buffer.
    image_rgb: np.ndarray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_original: Image.Image = Image.fromarray(image_rgb, mode="RGB")

    jpeg_buffer = io.BytesIO()
    pil_original.save(jpeg_buffer, format="JPEG", quality=jpeg_quality, subsampling=0)
    jpeg_buffer.seek(0)

    pil_recompressed: Image.Image = Image.open(jpeg_buffer).convert("RGB")
    recompressed_rgb: np.ndarray = np.array(pil_recompressed, dtype=np.float32)

    # ── Step 2 : absolute pixel-by-pixel residual matrix ────────────────────
    # Cast originals to float32 to prevent uint8 wrap-around on subtraction.
    original_f32: np.ndarray = image_rgb.astype(np.float32)   # shape (H, W, 3)

    # R(h,w,c) = |I(h,w,c) − I_q(h,w,c)|
    residual: np.ndarray = np.abs(original_f32 - recompressed_rgb)  # (H, W, 3) float32 ≥0

    # ── Step 3 : amplified visual map ────────────────────────────────────────
    # R_amp(h,w,c) = clip(R(h,w,c) · α, 0, 255)
    residual_amplified: np.ndarray = np.clip(
        residual * amplification, 0.0, 255.0
    )  # (H, W, 3) float32

    ela_visual_rgb: np.ndarray = residual_amplified.astype(np.uint8)
    ela_visual: np.ndarray = cv2.cvtColor(ela_visual_rgb, cv2.COLOR_RGB2BGR)

    # ── Step 4 : luminance collapse of residual (un-amplified) ──────────────
    # G(h,w) = 0.299·R_r + 0.587·R_g + 0.114·R_b  (ITU-R BT.601 luma weights)
    luma_residual: np.ndarray = (
        0.299 * residual[:, :, 0]
        + 0.587 * residual[:, :, 1]
        + 0.114 * residual[:, :, 2]
    )  # (H, W) float32

    # ── Step 5 : thresholding and anomaly mask ────────────────────────────────
    threshold_value: float = float(np.percentile(luma_residual, anomaly_percentile))
    # Guard against degenerate flat images (threshold = 0)
    if threshold_value < 1e-6:
        threshold_value = 1e-6

    # Boolean mask: True where residual exceeds the anomaly percentile
    anomaly_mask: np.ndarray = (luma_residual > threshold_value).astype(np.uint8) * 255

    # ── Step 6 : connected-components labelling ──────────────────────────────
    num_labels: int
    labels: np.ndarray
    stats: np.ndarray          # shape (num_labels, 5): x,y,w,h,area per component
    centroids: np.ndarray      # shape (num_labels, 2)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        anomaly_mask, connectivity=8, ltype=cv2.CV_32S
    )

    # Label 0 is the background — iterate from label 1 onwards.
    cluster_areas: List[int] = []
    for label_idx in range(1, num_labels):
        area: int = int(stats[label_idx, cv2.CC_STAT_AREA])
        if area >= min_cluster_area:
            cluster_areas.append(area)

    # ── Step 7 : aggregate statistics ────────────────────────────────────────
    total_pixels: int = H * W
    mean_residual: float = float(np.mean(luma_residual))
    std_residual: float = float(np.std(luma_residual))
    max_residual: float = float(np.max(residual_amplified))

    anomaly_pixel_count: int = int(np.sum(anomaly_mask > 0))
    anomaly_pixel_ratio: float = anomaly_pixel_count / total_pixels

    # ── Step 8 : composite ELA fraud score ──────────────────────────────────
    # Normalise mean residual from [0,255] → [0,1]
    norm_mean: float = mean_residual / 255.0
    # Normalise std residual from [0,127.5] → [0,1]
    norm_std: float = min(std_residual / 127.5, 1.0)

    # Weighted linear combination before sigmoid squash
    raw_score: float = (
        0.40 * norm_mean
        + 0.30 * norm_std
        + 0.30 * anomaly_pixel_ratio
    )  # ∈ [0, 1] approximately

    # Sigmoid to map to strict (0,1) — σ(x) = 1/(1+e^{-k(x-0.5)})
    # k=8 gives steep transition around 0.5
    k: float = 8.0
    ela_score: float = 1.0 / (1.0 + math.exp(-k * (raw_score - 0.5)))

    ELA_FLAG_THRESHOLD = 0.55
    flagged: bool = ela_score >= ELA_FLAG_THRESHOLD

    log.info(
        "ELA | mean=%.3f std=%.3f anomaly_ratio=%.4f clusters=%d score=%.4f flagged=%s",
        mean_residual, std_residual, anomaly_pixel_ratio,
        len(cluster_areas), ela_score, flagged,
    )

    result = ELAResult(
        mean_residual_intensity=round(mean_residual, 6),
        std_residual_intensity=round(std_residual, 6),
        max_residual_intensity=round(max_residual, 6),
        anomaly_pixel_ratio=round(anomaly_pixel_ratio, 8),
        anomaly_cluster_count=len(cluster_areas),
        anomaly_cluster_areas_px=cluster_areas,
        ela_score=round(ela_score, 8),
        flagged=flagged,
    )
    return result, ela_visual


# ---------------------------------------------------------------------------
# ── FFT MOIRÉ / SCREEN-RECAPTURE PIPELINE ────────────────────────────────────
# ---------------------------------------------------------------------------

def _build_radial_bin_indices(
    H: int, W: int, num_bins: int
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Pre-compute the normalised radial distance of every frequency-domain
    cell from the DC origin, then map each cell to one of `num_bins` bins.

    Frequency-space coordinates
    ---------------------------
    After a 2-D DFT of an H×W image (with fftshift applied so DC is at centre):
        u ∈ [-W/2, W/2)   horizontal frequency index
        v ∈ [-H/2, H/2)   vertical   frequency index

    Normalised frequency (0 = DC, 0.5 = Nyquist):
        f(u,v) = sqrt((u/W)² + (v/H)²) / sqrt(0.5² + 0.5²)
               ∈ [0, 1]

    Bin index:
        b(u,v) = floor(f(u,v) · num_bins)  clipped to [0, num_bins-1]

    Returns
    -------
    bin_map   : (H, W) int32 array — bin index for each FFT cell.
    freq_map  : (H, W) float32 — normalised frequency for each cell ∈ [0,1].
    max_freq  : float — normalised Nyquist diagonal used for scaling.
    """
    # Frequency axis arrays centred at 0
    u_axis: np.ndarray = np.fft.fftfreq(W).astype(np.float32)  # length W, ∈ [-0.5, 0.5)
    v_axis: np.ndarray = np.fft.fftfreq(H).astype(np.float32)  # length H, ∈ [-0.5, 0.5)

    # Meshgrid: UU[v, u], VV[v, u]
    UU: np.ndarray
    VV: np.ndarray
    UU, VV = np.meshgrid(u_axis, v_axis)  # both (H, W) float32

    # Euclidean distance in frequency space (not normalised yet)
    freq_map_raw: np.ndarray = np.sqrt(UU ** 2 + VV ** 2)  # (H, W) float32  ∈ [0, ~0.707]

    # Maximum possible normalised frequency = diagonal Nyquist = sqrt(0.5²+0.5²) ≈ 0.7071
    max_freq: float = float(math.sqrt(0.5 ** 2 + 0.5 ** 2))

    # Normalise to [0, 1]
    freq_map: np.ndarray = freq_map_raw / max_freq  # (H, W) float32 ∈ [0, 1]

    # Map to discrete bin indices
    bin_map: np.ndarray = np.floor(freq_map * num_bins).astype(np.int32)
    np.clip(bin_map, 0, num_bins - 1, out=bin_map)

    return bin_map, freq_map, max_freq


def _zero_dc_region(
    magnitude_spectrum: np.ndarray,
    exclusion_radius: int,
    H: int,
    W: int,
) -> np.ndarray:
    """
    Zero out a circular region of radius `exclusion_radius` pixels centred on
    the DC component in the shifted magnitude spectrum.

    The DC component at (H//2, W//2) represents the image mean intensity and
    dominates the spectrum; masking it prevents it from inflating ring statistics.

    Operation:
        For every (r, c):
            if (r − H//2)² + (c − W//2)² ≤ exclusion_radius²:
                magnitude_spectrum[r, c] = 0
    """
    cy: int = H // 2
    cx: int = W // 2

    # Build coordinate grids
    row_idx: np.ndarray = np.arange(H, dtype=np.int32)
    col_idx: np.ndarray = np.arange(W, dtype=np.int32)
    RR: np.ndarray
    CC: np.ndarray
    RR, CC = np.meshgrid(row_idx, col_idx, indexing="ij")  # (H, W)

    dist_sq: np.ndarray = (RR - cy) ** 2 + (CC - cx) ** 2   # (H, W) int32
    dc_mask: np.ndarray = dist_sq <= (exclusion_radius ** 2) # (H, W) bool

    result: np.ndarray = magnitude_spectrum.copy()
    result[dc_mask] = 0.0
    return result


def _local_max_suppression(
    spectrum_2d: np.ndarray,
    neighbourhood_radius: int,
) -> np.ndarray:
    """
    Non-maximum suppression in 2-D frequency space.

    For each pixel position (r, c):
        If spectrum_2d[r, c] is NOT the maximum value in the square
        window of side (2·neighbourhood_radius+1) centred on (r,c),
        suppress it to 0.

    This isolates distinct spectral peaks rather than broad lobes.

    Uses morphological dilation to efficiently compute local maxima.
    """
    kernel_size: int = 2 * neighbourhood_radius + 1
    kernel: np.ndarray = np.ones((kernel_size, kernel_size), dtype=np.float32)

    # dilated[r,c] = max value in the (kernel_size×kernel_size) neighbourhood of (r,c)
    dilated: np.ndarray = cv2.dilate(
        spectrum_2d.astype(np.float32), kernel
    )  # (H, W) float32

    # Keep only cells where the local value equals the local maximum
    is_local_max: np.ndarray = (spectrum_2d == dilated)  # (H, W) bool

    suppressed: np.ndarray = spectrum_2d * is_local_max.astype(np.float32)
    return suppressed


def run_fft_moire(
    image_bgr: np.ndarray,
    radial_bins: int = FFT_RADIAL_BINS,
    dc_exclusion_radius: int = FFT_DC_EXCLUSION_RADIUS,
    periodicity_sigma: float = FFT_PERIODICITY_THRESHOLD,
    band_low: float = FFT_MOIRE_FREQ_BAND_LOW,
    band_high: float = FFT_MOIRE_FREQ_BAND_HIGH,
    peak_neighbourhood: int = FFT_PEAK_NEIGHBOURHOOD,
) -> Tuple[FFTMoireResult, np.ndarray]:
    """
    FFT Moiré / Screen-Recapture Detection Pipeline.

    Mathematical overview
    ---------------------
    1. Convert image to float64 luminance Y ∈ [0, 1]:
           Y(h,w) = 0.299·R(h,w)/255 + 0.587·G(h,w)/255 + 0.114·B(h,w)/255

    2. Apply 2-D Hanning window to reduce spectral leakage:
           W(h,w) = w_v(h) · w_u(w)
           where w_v, w_u are 1-D Hanning windows of length H, W respectively.
           Y_w(h,w) = Y(h,w) · W(h,w)

    3. 2-D Discrete Fourier Transform:
           F(u,v) = Σ_{h=0}^{H-1} Σ_{w=0}^{W-1} Y_w(h,w) · e^{-j2π(uh/H + vw/W)}

    4. Shifted log-magnitude power spectrum:
           M(u,v) = log(1 + |fftshift(F)(u,v)|)
           where fftshift recentres DC at (H//2, W//2).

    5. DC exclusion: zero out M within radius dc_exclusion_radius of DC.

    6. Radial power profile (ring averages):
           For each radial bin b (normalised frequency range [b/B, (b+1)/B]):
               ring_power[b] = mean{ M(u,v) : bin_map(u,v) == b }
           This collapses 2-D isotropy; Moiré/screen-recapture grids produce
           localised spikes in the ring_power vector.

    7. Peak detection in ring_power:
           μ_r = mean(ring_power),  σ_r = std(ring_power)
           A bin b is a periodic anomaly if:
               ring_power[b] > μ_r + periodicity_sigma · σ_r
           AND b corresponds to the Moiré frequency band [band_low, band_high].

    8. 2-D peak isolation (in the full shifted spectrum):
           Apply NMS to M. For peaks in the Moiré band, extract their normalised
           frequency and power.

    9. Moiré band energy ratio:
           E_band = Σ_{(u,v): band_low ≤ freq(u,v) ≤ band_high} M(u,v)²
           E_total = Σ_{all (u,v)} M(u,v)²
           ratio = E_band / E_total

    10. FFT score:
           fft_score = sigmoid(
               0.45 · min(periodicity_sigma_dominant / 10, 1) +
               0.35 · ratio +
               0.20 · min(len(flagged_peaks) / 5, 1)
           )

    Parameters
    ----------
    image_bgr         : OpenCV BGR uint8 image array of shape (H, W, 3).
    radial_bins       : Number of concentric rings to divide frequency space into.
    dc_exclusion_radius : Pixels around DC to blank out before ring analysis.
    periodicity_sigma : Anomaly threshold expressed as σ above ring mean.
    band_low/high     : Normalised spatial frequency range for Moiré analysis.
    peak_neighbourhood : NMS neighbourhood radius in the 2-D spectrum.

    Returns
    -------
    fft_result  : FFTMoireResult Pydantic model.
    spectrum_vis: uint8 BGR visualisation of the log-power spectrum (normalised).
    """
    H, W = image_bgr.shape[:2]
    log.debug("FFT | input shape=(%d,%d) bins=%d", H, W, radial_bins)

    # ── Step 1 : luminance conversion to float64 ─────────────────────────────
    # Y = 0.299·R + 0.587·G + 0.114·B, normalised to [0,1]
    image_rgb_f64: np.ndarray = image_bgr[:, :, ::-1].astype(np.float64) / 255.0
    # ::-1 reverses channel axis BGR→RGB in-place view (no copy needed)
    luma: np.ndarray = (
        0.299 * image_rgb_f64[:, :, 0]
        + 0.587 * image_rgb_f64[:, :, 1]
        + 0.114 * image_rgb_f64[:, :, 2]
    )  # (H, W) float64 ∈ [0, 1]

    # ── Step 2 : 2-D Hanning window ───────────────────────────────────────────
    # w_v: (H,) Hanning vector;  w_u: (W,) Hanning vector
    # W_2d(h,w) = w_v(h) · w_u(w)  — outer product
    hann_v: np.ndarray = np.hanning(H).astype(np.float64)  # (H,)
    hann_u: np.ndarray = np.hanning(W).astype(np.float64)  # (W,)
    window_2d: np.ndarray = np.outer(hann_v, hann_u)        # (H, W) float64

    luma_windowed: np.ndarray = luma * window_2d             # (H, W) float64

    # ── Step 3 : 2-D DFT ─────────────────────────────────────────────────────
    # numpy rfft2 returns the positive-frequency half; we use full fft2 for
    # symmetric ring analysis.
    dft_complex: np.ndarray = np.fft.fft2(luma_windowed)    # (H, W) complex128
    dft_shifted: np.ndarray = np.fft.fftshift(dft_complex)  # DC at (H//2, W//2)

    # ── Step 4 : log-magnitude power spectrum ────────────────────────────────
    # M(u,v) = log(1 + |F_shifted(u,v)|)
    magnitude: np.ndarray = np.abs(dft_shifted)              # (H, W) float64 ≥0
    log_magnitude: np.ndarray = np.log1p(magnitude)          # (H, W) float64 ≥0

    # ── Step 5 : DC exclusion ────────────────────────────────────────────────
    log_mag_no_dc: np.ndarray = _zero_dc_region(
        log_magnitude, dc_exclusion_radius, H, W
    )  # (H, W) float64

    # ── Step 6 : radial bin index map ────────────────────────────────────────
    bin_map: np.ndarray
    freq_map: np.ndarray
    max_freq: float
    bin_map, freq_map, max_freq = _build_radial_bin_indices(H, W, radial_bins)
    # bin_map:  (H, W) int32    — which radial bucket each cell belongs to
    # freq_map: (H, W) float32  — normalised frequency ∈ [0, 1]

    # ── Step 7 : ring-averaged power profile ─────────────────────────────────
    ring_power: np.ndarray = np.zeros(radial_bins, dtype=np.float64)
    ring_count: np.ndarray = np.zeros(radial_bins, dtype=np.int64)

    # Vectorised accumulation using np.add.at
    np.add.at(ring_power, bin_map.ravel(), log_mag_no_dc.ravel())
    np.add.at(ring_count, bin_map.ravel(), 1)

    # Safe mean: avoid divide-by-zero for empty bins
    nonzero_bins: np.ndarray = ring_count > 0
    ring_power[nonzero_bins] /= ring_count[nonzero_bins].astype(np.float64)
    ring_power[~nonzero_bins] = 0.0   # keep empty bins at 0

    # Ring statistics
    ring_mean: float = float(np.mean(ring_power))
    ring_std: float = float(np.std(ring_power))
    if ring_std < 1e-10:
        ring_std = 1e-10  # numerical guard

    # ── Step 8 : periodic anomaly detection in ring profile ──────────────────
    # Compute per-ring sigma score: z[b] = (ring_power[b] - μ_r) / σ_r
    ring_z_scores: np.ndarray = (ring_power - ring_mean) / ring_std  # (radial_bins,)

    # Bin normalised frequency:  bin b → freq = (b + 0.5) / radial_bins
    bin_frequencies: np.ndarray = (
        np.arange(radial_bins, dtype=np.float64) + 0.5
    ) / radial_bins   # (radial_bins,) ∈ (0, 1)

    # Moiré band mask: bins whose centre frequency falls in [band_low, band_high]
    in_moire_band: np.ndarray = (
        (bin_frequencies >= band_low) & (bin_frequencies <= band_high)
    )  # (radial_bins,) bool

    # Flag bins exceeding σ threshold AND inside the Moiré band
    flagged_bins: np.ndarray = (
        (ring_z_scores >= periodicity_sigma) & in_moire_band
    )  # (radial_bins,) bool

    flagged_frequencies: List[float] = [
        round(float(bin_frequencies[b]), 6)
        for b in np.where(flagged_bins)[0]
    ]

    # ── Step 9 : dominant 2-D spectral peak (inside Moiré band) ─────────────
    # Create a band-pass mask in 2-D frequency space
    band_mask_2d: np.ndarray = (
        (freq_map >= band_low) & (freq_map <= band_high)
    ).astype(np.float32)  # (H, W)

    log_mag_band: np.ndarray = log_mag_no_dc * band_mask_2d  # (H, W) float64

    # NMS to isolate the sharpest peaks
    suppressed_spectrum: np.ndarray = _local_max_suppression(
        log_mag_band.astype(np.float32), peak_neighbourhood
    )  # (H, W) float32

    # Dominant peak coordinates
    peak_flat_idx: int = int(np.argmax(suppressed_spectrum))
    peak_row: int = peak_flat_idx // W
    peak_col: int = peak_flat_idx % W

    dominant_peak_power: float = float(suppressed_spectrum[peak_row, peak_col])
    dominant_peak_freq: float = float(freq_map[peak_row, peak_col])

    # σ of dominant peak relative to ring background
    # Identify which bin the dominant peak falls in
    dominant_bin: int = int(bin_map[peak_row, peak_col])
    dominant_sigma: float = float(ring_z_scores[dominant_bin]) if ring_std > 1e-10 else 0.0

    # ── Step 10 : Moiré band energy ratio ────────────────────────────────────
    # E_band  = Σ M(u,v)²   for (u,v) in Moiré band
    # E_total = Σ M(u,v)²   for all (u,v)
    spectrum_sq: np.ndarray = log_mag_no_dc ** 2         # (H, W) float64
    E_total: float = float(np.sum(spectrum_sq))
    E_band: float = float(np.sum(spectrum_sq * band_mask_2d))
    moire_ratio: float = E_band / E_total if E_total > 1e-12 else 0.0

    # ── Step 11 : composite FFT fraud score ──────────────────────────────────
    # Three sub-signals, each normalised to [0,1]:
    sig_sigma: float = min(max(dominant_sigma, 0.0) / 10.0, 1.0)
    sig_ratio: float = min(moire_ratio, 1.0)
    sig_peaks: float = min(len(flagged_frequencies) / 5.0, 1.0)

    raw_fft: float = 0.45 * sig_sigma + 0.35 * sig_ratio + 0.20 * sig_peaks

    k: float = 8.0
    fft_score: float = 1.0 / (1.0 + math.exp(-k * (raw_fft - 0.5)))

    FFT_FLAG_THRESHOLD = 0.55
    flagged: bool = fft_score >= FFT_FLAG_THRESHOLD

    log.info(
        "FFT | dominant_freq=%.4f dominant_power=%.4f sigma=%.3f "
        "moire_ratio=%.4f peaks=%d score=%.4f flagged=%s",
        dominant_peak_freq, dominant_peak_power, dominant_sigma,
        moire_ratio, len(flagged_frequencies), fft_score, flagged,
    )

    # ── Visualisation: normalise log-magnitude to uint8 BGR ──────────────────
    vis_norm: np.ndarray = cv2.normalize(
        log_mag_no_dc.astype(np.float32),
        None,                # dst — allocate new array
        alpha=0,
        beta=255,
        norm_type=cv2.NORM_MINMAX,
        dtype=cv2.CV_8U,
    )  # (H, W) uint8
    spectrum_vis: np.ndarray = cv2.applyColorMap(vis_norm, cv2.COLORMAP_INFERNO)  # (H,W,3) BGR

    result = FFTMoireResult(
        dominant_peak_frequency=round(dominant_peak_freq, 8),
        dominant_peak_power=round(dominant_peak_power, 8),
        periodicity_sigma=round(dominant_sigma, 6),
        moire_band_energy_ratio=round(moire_ratio, 8),
        detected_peak_frequencies=flagged_frequencies,
        fft_score=round(fft_score, 8),
        flagged=flagged,
    )
    return result, spectrum_vis


# ---------------------------------------------------------------------------
# ── IMAGE INGEST UTILITY ─────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def decode_image_bytes(raw_bytes: bytes) -> np.ndarray:
    """
    Decode raw image bytes (any format OpenCV supports) into a BGR uint8 ndarray.

    Strategy:
        1. Wrap bytes in a numpy uint8 1-D buffer (zero-copy view).
        2. Pass to cv2.imdecode with IMREAD_COLOR flag → always (H,W,3) BGR.
        3. Raise HTTP 422 if the buffer cannot be decoded.

    Parameters
    ----------
    raw_bytes : Raw file content bytes.

    Returns
    -------
    image_bgr : np.ndarray of shape (H, W, 3), dtype uint8.
    """
    byte_buffer: np.ndarray = np.frombuffer(raw_bytes, dtype=np.uint8)
    image_bgr: Optional[np.ndarray] = cv2.imdecode(byte_buffer, cv2.IMREAD_COLOR)

    if image_bgr is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot decode uploaded file as a valid image. "
                   "Supported formats: JPEG, PNG, BMP, TIFF, WebP.",
        )

    # Ensure contiguous C-order memory layout for downstream numpy operations
    if not image_bgr.flags["C_CONTIGUOUS"]:
        image_bgr = np.ascontiguousarray(image_bgr)

    return image_bgr


def _compute_verdict(score: float) -> str:
    """Map an overall fraud score in [0,1] to a categorical verdict string."""
    if score < 0.40:
        return "AUTHENTIC"
    elif score < 0.65:
        return "SUSPICIOUS"
    else:
        return "FRAUDULENT"


# ---------------------------------------------------------------------------
# ── FASTAPI APPLICATION ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Document Forensics Engine",
    description=(
        "Production-grade active fraud detection API. "
        "Exposes Error Level Analysis (ELA) and FFT Moiré screen-recapture "
        "detection on uploaded document images."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["Ops"])
async def health_check() -> dict:
    """Liveness probe — returns 200 OK when service is ready."""
    return {"status": "ok", "engine": "forensic_engine", "version": "1.0.0"}


@app.post(
    "/api/v1/forensics/analyze",
    response_model=ForensicsResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse a document image for signs of manipulation or screen-recapture",
    tags=["Forensics"],
)
async def analyze_document(
    file: Annotated[
        UploadFile,
        File(description="Document image to analyse (JPEG/PNG/BMP/TIFF/WebP, ≤30 MB)"),
    ],
) -> ForensicsResponse:
    """
    **POST /api/v1/forensics/analyze**

    Accepts a Multipart file upload, runs ELA and FFT Moiré detection
    **concurrently** via asyncio, and returns a structured JSON report.

    ### Algorithm execution
    Both pipelines are CPU-bound; they are dispatched to a thread-pool executor
    via `asyncio.get_event_loop().run_in_executor` so the event loop is not
    blocked and other requests can be served concurrently.

    ### Scoring
    - `overall_fraud_score = 0.55·ela_score + 0.45·fft_score`
    - `verdict`: AUTHENTIC (<0.40) | SUSPICIOUS (0.40–0.65) | FRAUDULENT (≥0.65)
    """
    request_id: str = str(uuid.uuid4())
    t_start: float = time.perf_counter()

    log.info("REQUEST %s | filename=%s content_type=%s",
             request_id, file.filename, file.content_type)

    # ── Guard : MIME type check ───────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported content type '{file.content_type}'. "
                f"Accepted types: {sorted(ALLOWED_CONTENT_TYPES)}"
            ),
        )

    # ── Read file bytes with size guard ──────────────────────────────────────
    raw_bytes: bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Upload size {len(raw_bytes) / 1_048_576:.1f} MB exceeds "
                f"the {MAX_UPLOAD_BYTES // 1_048_576} MB limit."
            ),
        )
    if len(raw_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # ── Decode image ─────────────────────────────────────────────────────────
    image_bgr: np.ndarray = decode_image_bytes(raw_bytes)
    H, W, C = image_bgr.shape

    log.info("REQUEST %s | decoded shape=(%d,%d,%d)", request_id, H, W, C)

    # ── Concurrent pipeline execution ─────────────────────────────────────────
    # Both run_ela and run_fft_moire are pure CPU-bound functions.
    # We submit them to the default ThreadPoolExecutor so FastAPI's async
    # event loop is not blocked.
    loop = asyncio.get_event_loop()

    ela_task = loop.run_in_executor(None, run_ela, image_bgr)
    fft_task = loop.run_in_executor(None, run_fft_moire, image_bgr)

    # Await both concurrently; either exception propagates naturally.
    (ela_result, _ela_vis), (fft_result, _fft_vis) = await asyncio.gather(
        ela_task, fft_task
    )

    # ── Overall composite score ───────────────────────────────────────────────
    # Weighted sum: ELA captures pixel-level manipulation; FFT captures
    # structural periodicity from display grid artefacts.
    # Weights: ELA=0.55, FFT=0.45  (ELA historically more discriminative)
    overall_score: float = round(
        0.55 * ela_result.ela_score + 0.45 * fft_result.fft_score, 8
    )
    verdict: str = _compute_verdict(overall_score)

    t_end: float = time.perf_counter()
    processing_ms: float = round((t_end - t_start) * 1_000.0, 3)

    log.info(
        "REQUEST %s | overall_score=%.4f verdict=%s latency=%.1f ms",
        request_id, overall_score, verdict, processing_ms,
    )

    return ForensicsResponse(
        request_id=request_id,
        processing_time_ms=processing_ms,
        image_width_px=W,
        image_height_px=H,
        image_channels=C,
        ela=ela_result,
        fft=fft_result,
        overall_fraud_score=overall_score,
        verdict=verdict,
    )


# ---------------------------------------------------------------------------
# ── ENTRY POINT ──────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "forensic_engine:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4,          # one worker per CPU core is a sensible default
        log_level="info",
    )
