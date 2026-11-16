"""
jpeg_quality_estimator.py — Non-destructive JPEG Quality Estimation & Qualification (REM-04).

Extracts JPEG Luminance Quantization Tables (DQT) directly from file bytes or Pillow metadata
to compute an exact IJG-equivalent quality factor Q in [1, 100].

CRITICAL FORENSIC INVARIANT:
Never applies deblocking, Gaussian filtering, or image smoothing to raw exhibit pixels.
Exhibit bytes and forensic SHA-256 integrity remain 100% untouched.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Standard IJG 50 luminance quantization table (ITU-T T.81 / ISO/IEC 10918-1)
STD_LUM_50: List[int] = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
]


def estimate_jpeg_quality_from_dqt(dqt_table: Optional[List[int]]) -> Optional[float]:
    """
    Computes estimated IJG quality factor Q from a 64-element luminance quantization table.
    Uses median of inverse IJG scaling factors across standard low-frequency coefficients.
    """
    if not dqt_table or len(dqt_table) < len(STD_LUM_50):
        return None

    qs = []
    for i in range(len(STD_LUM_50)):
        q_val = dqt_table[i]
        std_val = STD_LUM_50[i]
        if q_val <= 0:
            continue
        scale = (float(q_val) * 100.0) / float(std_val)
        if scale > 100.0:
            q = 5000.0 / scale
        else:
            q = (200.0 - scale) / 2.0
        # Clamp to valid JPEG quality range [1, 100]
        q = max(1.0, min(100.0, q))
        qs.append(q)

    if not qs:
        return None

    return round(float(np.median(qs)), 1)


def estimate_jpeg_quality_from_bytes(file_bytes: bytes) -> Optional[float]:
    """Extracts quantization table from raw JPEG file bytes."""
    if not file_bytes:
        return None
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            if img.format not in ("JPEG", "MPO"):
                return None
            qt = getattr(img, "quantization", {})
            lum_table = qt.get(0) if qt else None
            return estimate_jpeg_quality_from_dqt(lum_table)
    except Exception as e:
        logger.debug("Non-JPEG or unreadable bytes in quality estimation: %s", e)
        return None


def estimate_jpeg_quality_from_path(file_path: Path | str) -> Optional[float]:
    """Extracts quantization table from image on disk."""
    p = Path(file_path)
    if not p.exists() or p.stat().st_size == 0:
        return None
    try:
        with Image.open(p) as img:
            if img.format not in ("JPEG", "MPO"):
                return None
            qt = getattr(img, "quantization", {})
            lum_table = qt.get(0) if qt else None
            return estimate_jpeg_quality_from_dqt(lum_table)
    except Exception as e:
        logger.debug("Failed to read image for JPEG quality from %s: %s", file_path, e)
        return None


def inspect_compression_quality(context: Any) -> Dict[str, Any]:
    """
    Evaluates compression characteristics of context exhibit non-destructively.
    Returns dictionary with estimated quality, heavy compression flag, and qualification notice.
    """
    est_q: Optional[float] = None

    # Check raw exhibit bytes
    if getattr(context, "file_bytes", None):
        est_q = estimate_jpeg_quality_from_bytes(context.file_bytes)

    # Fallback to stored exhibit path
    if est_q is None and getattr(context, "stored_path", None):
        est_q = estimate_jpeg_quality_from_path(context.stored_path)

    # Fallback to first page image
    if est_q is None and getattr(context, "page_images", None) and context.page_images:
        est_q = estimate_jpeg_quality_from_path(context.page_images[0])

    is_heavy = est_q is not None and est_q < 40.0

    notice = None
    if is_heavy:
        notice = (
            f"Document exhibits severe JPEG compression artifacts (estimated Q={est_q:.0f} < 40). "
            f"High-frequency 8x8 DCT block boundaries may artificially elevate blur, edge density, "
            f"and Laplacian variance features."
        )

    return {
        "is_jpeg": est_q is not None,
        "estimated_quality": est_q,
        "is_heavily_compressed": is_heavy,
        "compression_notice": notice,
    }
