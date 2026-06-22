"""
utils.py — Image sanitization helpers for ML pipelines.

Functions
---------
normalize_image       : Decode raw bytes → resized, channel-normalised ndarray.
extract_exif_metadata : Pull EXIF tags from a JPEG/TIFF byte buffer; flag
                        editing traces (software tags, GPS strips, etc.).
load_model_weights    : Load a joblib-serialised model/weights file with
                        configurable retry logic and basic integrity checks.
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import joblib
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
BytesLike = Union[bytes, bytearray, memoryview]


# ---------------------------------------------------------------------------
# 1. normalize_image
# ---------------------------------------------------------------------------
def normalize_image(
    raw_bytes: BytesLike,
    target_size: Tuple[int, int] = (224, 224),
    *,
    color_mode: str = "rgb",
    interpolation: int = cv2.INTER_LINEAR,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
    dtype: np.dtype = np.float32,
) -> np.ndarray:
    """Decode *raw_bytes* and return a normalised image array.

    Parameters
    ----------
    raw_bytes:
        Raw image file content (JPEG, PNG, BMP, …).
    target_size:
        ``(width, height)`` in pixels.  Passed directly to ``cv2.resize``.
    color_mode:
        ``"rgb"`` (default), ``"bgr"``, or ``"grayscale"``.
    interpolation:
        cv2 interpolation flag used during resize.
    mean, std:
        Per-channel ImageNet-style statistics for z-score normalisation.
        Ignored when *color_mode* is ``"grayscale"``.
    dtype:
        Output array dtype.  Defaults to ``np.float32``.

    Returns
    -------
    np.ndarray
        Shape ``(H, W, C)`` for colour modes or ``(H, W)`` for grayscale,
        values normalised to the ``[0, 1]`` range and then z-scored.

    Raises
    ------
    ValueError
        If *raw_bytes* cannot be decoded as an image.
    """
    # --- decode ----------------------------------------------------------------
    buf = np.frombuffer(bytes(raw_bytes), dtype=np.uint8)
    img_bgr = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    if img_bgr is None:
        raise ValueError(
            "cv2.imdecode returned None — byte buffer is not a recognised image format."
        )

    # --- handle alpha channel --------------------------------------------------
    if img_bgr.ndim == 3 and img_bgr.shape[2] == 4:
        # Flatten alpha onto white background
        alpha = img_bgr[:, :, 3:4].astype(np.float32) / 255.0
        rgb   = img_bgr[:, :, :3].astype(np.float32)
        white = np.ones_like(rgb) * 255.0
        img_bgr = (alpha * rgb + (1.0 - alpha) * white).astype(np.uint8)

    # --- resize ----------------------------------------------------------------
    w, h = target_size
    img_resized = cv2.resize(img_bgr, (w, h), interpolation=interpolation)

    # --- colour conversion -----------------------------------------------------
    mode = color_mode.lower()
    if mode == "rgb":
        img_out = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    elif mode == "bgr":
        img_out = img_resized
    elif mode == "grayscale":
        img_out = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError(f"Unsupported color_mode '{color_mode}'. Use 'rgb', 'bgr', or 'grayscale'.")

    # --- cast & normalise to [0, 1] -------------------------------------------
    img_float = img_out.astype(dtype) / 255.0

    # --- z-score (channel-wise) -----------------------------------------------
    if mode != "grayscale":
        mean_arr = np.array(mean, dtype=dtype)
        std_arr  = np.array(std,  dtype=dtype)
        img_float = (img_float - mean_arr) / (std_arr + 1e-7)

    logger.debug(
        "normalize_image: decoded → resized to %s → mode=%s → shape=%s",
        target_size, color_mode, img_float.shape,
    )
    return img_float


# ---------------------------------------------------------------------------
# 2. extract_exif_metadata
# ---------------------------------------------------------------------------

# Tags whose presence strongly suggests post-capture editing
_EDITING_SOFTWARE_TAGS: frozenset[str] = frozenset(
    {
        "Software",
        "ProcessingSoftware",
        "OriginalRawFileName",
        "HostComputer",
    }
)

_EDITING_SOFTWARE_KEYWORDS: Tuple[str, ...] = (
    "photoshop", "lightroom", "gimp", "affinity", "capture one",
    "darktable", "rawtherapee", "luminar", "snapseed", "pixelmator",
    "adobe", "acr", "camera raw",
)


def extract_exif_metadata(
    raw_bytes: BytesLike,
    *,
    detect_editing: bool = True,
) -> Dict[str, Any]:
    """Extract EXIF metadata from an image byte buffer.

    Uses Pillow's ``_getexif`` for broad tag coverage, with graceful
    fallback for images that carry no EXIF block.

    Parameters
    ----------
    raw_bytes:
        Raw image file content (must be JPEG or TIFF for EXIF support;
        PNG/WebP EXIF is attempted but may return an empty dict).
    detect_editing:
        When ``True`` (default), analyse the extracted tags and populate
        ``result["editing_traces"]`` with a list of human-readable findings.

    Returns
    -------
    dict with keys:

    ``"tags"``
        ``{tag_name: value}`` mapping of all decoded EXIF tags.
    ``"editing_traces"``  *(only when detect_editing=True)*
        List of strings describing suspicious editing indicators found.
    ``"has_gps"``
        ``True`` if GPS sub-IFD was present.
    ``"raw_exif_present"``
        ``True`` if any EXIF data was found at all.
    """
    result: Dict[str, Any] = {
        "tags": {},
        "has_gps": False,
        "raw_exif_present": False,
    }
    if detect_editing:
        result["editing_traces"] = []

    try:
        pil_img = Image.open(io.BytesIO(bytes(raw_bytes)))
    except Exception as exc:
        logger.warning("extract_exif_metadata: cannot open image — %s", exc)
        return result

    # --- low-level EXIF extraction --------------------------------------------
    try:
        raw_exif = pil_img._getexif()  # type: ignore[attr-defined]
    except AttributeError:
        raw_exif = None  # format does not expose _getexif (e.g. PNG via older Pillow)

    if not raw_exif:
        # Try the newer getexif() API (Pillow ≥ 6.0)
        try:
            exif_obj = pil_img.getexif()
            raw_exif = dict(exif_obj) if exif_obj else None
        except Exception:
            raw_exif = None

    if not raw_exif:
        logger.debug("extract_exif_metadata: no EXIF block found.")
        return result

    result["raw_exif_present"] = True

    # --- decode numeric tag IDs to human-readable names -----------------------
    decoded: Dict[str, Any] = {}
    for tag_id, value in raw_exif.items():
        tag_name = TAGS.get(tag_id, str(tag_id))
        if tag_name == "GPSInfo":
            result["has_gps"] = True
            decoded["GPSInfo"] = "<stripped>"   # avoid leaking location data
        else:
            # Serialise bytes objects for safe downstream use
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8", errors="replace")
                except Exception:
                    value = repr(value)
            decoded[tag_name] = value

    result["tags"] = decoded

    # --- editing-trace analysis -----------------------------------------------
    if detect_editing:
        traces: list[str] = []

        for tag in _EDITING_SOFTWARE_TAGS:
            if tag in decoded:
                val_lower = str(decoded[tag]).lower()
                for kw in _EDITING_SOFTWARE_KEYWORDS:
                    if kw in val_lower:
                        traces.append(
                            f"Editing software detected in '{tag}': {decoded[tag]!r}"
                        )
                        break

        # DateTime / DateTimeOriginal / DateTimeDigitized mismatch
        dt_original   = decoded.get("DateTimeOriginal")
        dt_digitized  = decoded.get("DateTimeDigitized")
        dt_modified   = decoded.get("DateTime")
        if dt_original and dt_modified and dt_original != dt_modified:
            traces.append(
                f"Modification timestamp differs from original capture time "
                f"({dt_original!r} → {dt_modified!r})."
            )
        if dt_original and dt_digitized and dt_original != dt_digitized:
            traces.append(
                f"Digitized timestamp differs from original capture time "
                f"({dt_original!r} → {dt_digitized!r})."
            )

        # Thumbnail presence without matching dimensions can indicate crop/resize
        if "ThumbnailOffset" in decoded or "JPEGInterchangeFormat" in decoded:
            img_w, img_h = pil_img.size
            # Retrieve thumbnail dimensions if available
            thumb_w = decoded.get("ThumbnailImageWidth") or decoded.get("ImageWidth")
            thumb_h = decoded.get("ThumbnailImageLength") or decoded.get("ImageLength")
            if thumb_w and thumb_h:
                try:
                    if int(thumb_w) != img_w or int(thumb_h) != img_h:
                        traces.append(
                            f"Embedded thumbnail dimensions ({thumb_w}×{thumb_h}) "
                            f"do not match image dimensions ({img_w}×{img_h}) — "
                            "possible crop or resize."
                        )
                except (TypeError, ValueError):
                    pass

        result["editing_traces"] = traces
        if traces:
            logger.info(
                "extract_exif_metadata: %d editing trace(s) found.", len(traces)
            )

    return result


# ---------------------------------------------------------------------------
# 3. load_model_weights
# ---------------------------------------------------------------------------

def load_model_weights(
    weights_path: Union[str, Path],
    *,
    retries: int = 3,
    retry_delay: float = 2.0,
    expected_keys: Optional[list[str]] = None,
    mmap_mode: Optional[str] = None,
) -> Any:
    """Load a joblib-serialised model or weights object from *weights_path*.

    Implements an exponential-backoff retry loop to tolerate transient I/O
    errors (network-mounted storage, NFS timeouts, etc.).

    Parameters
    ----------
    weights_path:
        Path to the ``.joblib`` / ``.pkl`` file produced by ``joblib.dump``.
    retries:
        Maximum number of load attempts.  Must be ≥ 1.
    retry_delay:
        Base delay in seconds between attempts (doubled on each failure).
    expected_keys:
        If the loaded object is a ``dict``, assert that every key in this
        list is present.  Raises ``KeyError`` on mismatch.
    mmap_mode:
        Passed verbatim to ``joblib.load`` as the ``mmap_mode`` argument.
        Use ``"r"`` to enable memory-mapping for large arrays.

    Returns
    -------
    Any
        The deserialised Python object (model, ``dict``, ``np.ndarray``, …).

    Raises
    ------
    FileNotFoundError
        If *weights_path* does not exist before the first attempt.
    RuntimeError
        If all retry attempts are exhausted without a successful load.
    KeyError
        If *expected_keys* validation fails after a successful load.
    """
    path = Path(weights_path)

    if not path.exists():
        raise FileNotFoundError(f"Weights file not found: {path}")

    if retries < 1:
        raise ValueError(f"retries must be ≥ 1, got {retries}.")

    last_exc: Optional[Exception] = None
    delay = retry_delay

    for attempt in range(1, retries + 1):
        try:
            logger.info(
                "load_model_weights: attempt %d/%d — loading '%s'",
                attempt, retries, path,
            )
            kwargs: Dict[str, Any] = {}
            if mmap_mode is not None:
                kwargs["mmap_mode"] = mmap_mode

            obj = joblib.load(path, **kwargs)

            # --- optional integrity check -------------------------------------
            if expected_keys is not None:
                if not isinstance(obj, dict):
                    raise TypeError(
                        f"expected_keys supplied but loaded object is "
                        f"{type(obj).__name__!r}, not dict."
                    )
                missing = [k for k in expected_keys if k not in obj]
                if missing:
                    raise KeyError(
                        f"Loaded weights dict is missing expected keys: {missing}"
                    )

            logger.info(
                "load_model_weights: successfully loaded '%s' (type=%s)",
                path, type(obj).__name__,
            )
            return obj

        except (KeyError, TypeError):
            # Integrity-check failures are not retryable — re-raise immediately.
            raise

        except Exception as exc:
            last_exc = exc
            logger.warning(
                "load_model_weights: attempt %d failed — %s: %s",
                attempt, type(exc).__name__, exc,
            )
            if attempt < retries:
                logger.debug(
                    "load_model_weights: retrying in %.1f s …", delay
                )
                time.sleep(delay)
                delay *= 2.0   # exponential back-off

    raise RuntimeError(
        f"load_model_weights: all {retries} attempt(s) failed for '{path}'. "
        f"Last error: {last_exc}"
    ) from last_exc
