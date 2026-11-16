"""
config.py

Central configuration dataclass for the forgery generation pipeline.
All tuneable parameters live here so no generator or orchestrator
needs to hard-code values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ForgeryConfig:
    """
    Full configuration for one forgery-generation run.

    Attributes:
        input_dir:                  Root of the authentic dataset
                                    (TrainingDataset/authentic/).
        output_dir:                 Destination for forged images
                                    (TrainingDataset/forged/).
        metadata_path:              Where the metadata CSV/JSON will be written.
        random_seed:                Seed for the numpy random Generator —
                                    guarantees reproducible runs.
        target_forged_per_authentic: How many forged variants to produce per
                                    authentic image.
        enabled_generators:         Names of generators to activate.
                                    Empty list means all registered generators.
        jpeg_quality_range:         (min, max) JPEG quality for JpegGenerator.
        noise_sigma_range:          (min, max) Gaussian sigma for NoiseGenerator.
        blur_kernel_range:          (min_px, max_px) kernel size for BlurGenerator
                                    (odd integers only; clamped at runtime).
        brightness_range:           (min, max) multiplicative brightness factor
                                    for BrightnessGenerator.
        copy_move_patch_range:      (min_px, max_px) patch side-length for
                                    CopyMoveGenerator.
        signature_probability:      Probability [0, 1] that SignatureGenerator
                                    is applied to any given image.
        logo_probability:           Probability [0, 1] that LogoGenerator
                                    is applied to any given image.
        text_probability:           Probability [0, 1] that TextGenerator
                                    is applied to any given image.
    """

    # Paths
    input_dir: Path = Path("TrainingDataset/authentic")
    output_dir: Path = Path("TrainingDataset/forged")
    metadata_path: Path = Path("TrainingDataset/metadata.csv")

    # Reproducibility
    random_seed: int = 42

    # Volume
    target_forged_per_authentic: int = 3

    # Validation mode — limit processing to the first N authentic images.
    # None means process the full dataset.
    max_images: int | None = None

    # Generator selection — empty = all registered generators
    enabled_generators: list[str] = field(default_factory=list)

    # Per-generator parameter ranges
    jpeg_quality_range: tuple[int, int] = (50, 85)
    noise_sigma_range: tuple[float, float] = (5.0, 30.0)
    blur_kernel_range: tuple[int, int] = (3, 15)
    brightness_range: tuple[float, float] = (0.5, 1.5)
    copy_move_patch_range: tuple[int, int] = (32, 128)

    # Overlay probabilities
    signature_probability: float = 0.5
    logo_probability: float = 0.4
    text_probability: float = 0.6
