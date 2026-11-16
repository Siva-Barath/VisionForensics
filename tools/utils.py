"""
utils.py

Reusable, stateless utility functions shared across the forgery
generation pipeline.  No generator or orchestrator should duplicate
these operations.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

# Supported image file extensions (lower-cased, with leading dot).
# This is the single authoritative definition — all pipeline code imports
# supported_extensions() from here rather than maintaining its own list.
_SUPPORTED: frozenset[str] = frozenset([
    ".tif", ".tiff",   # MIDV-500 authentic dataset
    ".jpg", ".jpeg",   # JPEG captures and forged outputs
    ".png",            # PNG captures
    ".bmp",            # BMP captures
])


def supported_extensions() -> frozenset[str]:
    """Return the set of image file extensions the pipeline can process."""
    return _SUPPORTED


def ensure_directory(path: Path) -> Path:
    """
    Create *path* (and any missing parents) if it does not already exist.

    Args:
        path: Directory to create.

    Returns:
        The same *path* for convenient chaining.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_image(path: Path) -> np.ndarray:
    """
    Load an image from *path* and return it as a BGR numpy array.

    Args:
        path: Absolute or relative path to the image file.

    Returns:
        Image as a uint8 numpy array in BGR channel order.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError:        If the file cannot be decoded as an image.
    """
    import cv2  # lazy import — cv2 is only required at generation time

    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"cv2.imread could not decode: {path}")

    log.debug("Loaded image | path=%s | shape=%s", path.name, image.shape)
    return image


def save_image(image: np.ndarray, path: Path, jpeg_quality: int = 95) -> None:
    """
    Save a BGR numpy array to *path*.

    PNG files are written losslessly; JPEG files use *jpeg_quality*.

    Args:
        image:        Image array in BGR channel order.
        path:         Destination file path (extension determines format).
        jpeg_quality: JPEG quality [1, 100] — ignored for non-JPEG formats.

    Raises:
        ValueError: If the image could not be encoded.
    """
    import cv2  # lazy import

    ensure_directory(path.parent)

    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
    else:
        params = []

    ok = cv2.imwrite(str(path), image, params)
    if not ok:
        raise ValueError(f"cv2.imwrite failed for: {path}")

    log.debug("Saved image | path=%s | shape=%s", path.name, image.shape)


def random_choice(items: list, rng: np.random.Generator):
    """
    Return a single element chosen uniformly at random from *items*.

    Args:
        items: Non-empty list to sample from.
        rng:   numpy random Generator (passed in — never created here).

    Returns:
        One element from *items*.

    Raises:
        ValueError: If *items* is empty.
    """
    if not items:
        raise ValueError("random_choice received an empty list")
    index = int(rng.integers(0, len(items)))
    return items[index]
