"""
extract_features.py

Large-scale feature extraction pipeline for ML dataset generation.

Processes every authentic and forged image, runs the full forensic
pipeline (excluding upload/storage and leakage stages), extracts the
~94 numerical features via the existing FeatureExtractor, and writes:

    features_authentic.csv
    features_forged.csv
    dataset.csv          (concatenation of both)

Usage::

    python tools/extract_features.py ^
        --authentic "D:\\Datasets\\TrainingDataset\\authentic" ^
        --forged    "D:\\Datasets\\TrainingDataset\\forged" ^
        --output    "D:\\Datasets\\TrainingDataset"

    # Dry-run — discover images and print counts only
    python tools/extract_features.py ^
        --authentic "D:\\Datasets\\TrainingDataset\\authentic" ^
        --forged    "D:\\Datasets\\TrainingDataset\\forged" ^
        --output    "D:\\Datasets\\TrainingDataset" ^
        --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path — repo root and backend root must both be present
# ---------------------------------------------------------------------------
_REPO_ROOT    = Path(__file__).resolve().parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for _p in (_REPO_ROOT, _BACKEND_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# tqdm is optional — fall back to a transparent no-op wrapper
try:
    from tqdm import tqdm as _tqdm
    def _progress(iterable, **kw):
        return _tqdm(iterable, **kw)
except ImportError:
    def _progress(iterable, **kw):  # type: ignore[misc]
        print(f"{kw.get('desc', '')}: processing {kw.get('total', '?')} items …")
        return iterable

# ---------------------------------------------------------------------------
# Backend imports
# ---------------------------------------------------------------------------
from app.pipeline.context import AnalysisContext
from app.pipeline.registry import PipelineRegistry
from app.pipeline.pipeline import PipelineManager
from app.pipeline.config import PipelineConfig

# Stages — import from the package __init__ which re-exports them correctly
from app.pipeline.stages import (
    PreprocessingStage,
    OCRStage,
    MetadataStage,
    LayoutAnalysisStage,
    ForgeryDetectionStage,       # name = "forgery"
    DocumentClassificationStage, # name = "document_classification"
)

# EvidenceFusionStage uses a different BaseStage and process() not run(),
# so it is incompatible with PipelineManager.  We call the service directly.
from app.services.evidence_fusion.fusion_service import EvidenceFusionService

from app.services.preprocessing.preprocessor import PreprocessingService
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService
from app.config.settings import get_settings

from app.ml.feature_extractor import FeatureExtractor
from app.ml.feature_registry import FEATURE_NAMES

logging.basicConfig(
    level=logging.WARNING,   # suppress verbose backend logs during bulk runs
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    [".tif", ".tiff", ".jpg", ".jpeg", ".png", ".bmp"]
)

# Stages registered with PipelineManager (upload excluded — we pre-populate
# context directly; risk/explainability/report excluded — leakage).
_PIPELINE_STAGES: list[str] = [
    "preprocessing",
    "ocr",
    "metadata",
    "layout",
    "forgery",
    "document_classification",
]

# CSV column layout
_IDENTITY_COLS: list[str] = ["image_name", "source_image", "document_category", "label"]
_CSV_COLUMNS:   list[str] = _IDENTITY_COLS + FEATURE_NAMES

_LABEL_AUTHENTIC = 0
_LABEL_FORGED    = 1


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def _build_pipeline() -> tuple[PipelineManager, EvidenceFusionService]:
    """
    Construct a PipelineManager wired with all compatible forensic stages,
    plus a standalone EvidenceFusionService for the fusion step.

    The upload stage is intentionally omitted — AnalysisContext.stored_path
    and file_bytes are pre-populated directly, bypassing HTTP validation.

    Returns:
        (pipeline, fusion_service)
    """
    settings = get_settings()
    storage  = StorageService(settings)
    pdf_svc  = PDFService(storage)
    preproc  = PreprocessingService(output_dir=Path(settings.processed_dir))

    registry = PipelineRegistry()
    registry.register(PreprocessingStage(pdf_svc, preproc))
    registry.register(OCRStage())
    registry.register(MetadataStage())
    registry.register(LayoutAnalysisStage())
    registry.register(ForgeryDetectionStage())
    registry.register(DocumentClassificationStage())

    config   = PipelineConfig(enabled_stages=_PIPELINE_STAGES)
    pipeline = PipelineManager(registry, config)

    return pipeline, EvidenceFusionService()


# ---------------------------------------------------------------------------
# Image discovery
# ---------------------------------------------------------------------------

def _discover(root: Path) -> list[Path]:
    """
    Recursively collect all supported image files under *root*.

    Returns a sorted list for deterministic processing order.
    """
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in _SUPPORTED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Per-image processing
# ---------------------------------------------------------------------------

async def _process_image(
    path: Path,
    label: int,
    pipeline: PipelineManager,
    fusion_svc: EvidenceFusionService,
    extractor: FeatureExtractor,
) -> dict | None:
    """
    Run the forensic pipeline on a single image and return a CSV row dict.

    Returns None on failure so the caller can count errors without stopping.

    Strategy:
    - Pre-populate AnalysisContext with file_bytes and stored_path.
    - Run PipelineManager (preprocessing → ocr → metadata → layout →
      forgery → document_classification).
    - Call EvidenceFusionService.fuse() directly to populate fusion_metrics.
    - Extract features via FeatureExtractor.
    - Release raw bytes immediately after the pipeline completes.
    """
    try:
        raw       = path.read_bytes()
        ext       = path.suffix.lower().lstrip(".")
        file_type = "jpeg" if ext in ("jpg", "jpeg") else ext

        context = AnalysisContext(
            original_filename=path.name,
            file_type=file_type,
            file_bytes=raw,
            size_bytes=len(raw),
        )
        # Pre-populate stored_path so PreprocessingStage can locate the file
        # without UploadStage copying it to the uploads/ directory.
        context.stored_path = path

        context = await pipeline.run(context)

        # Release raw bytes — do not keep images in memory
        context.file_bytes = b""

        # Run evidence fusion directly (its stage is incompatible with
        # PipelineManager due to a different BaseStage base class).
        evidence = getattr(context, "evidence", None) or []
        try:
            fusion_svc.fuse(evidence, context)
        except Exception as fuse_exc:
            log.warning("Fusion skipped | path=%s | %s", path.name, fuse_exc)

        label_str = "authentic" if label == _LABEL_AUTHENTIC else "forged"
        vector    = extractor.extract(context, label=label_str)

        return _vector_to_row(vector, path, label)

    except Exception as exc:
        log.error("Failed | path=%s | %s: %s", path, type(exc).__name__, exc)
        return None


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------

def _vector_to_row(vector, source_path: Path, label: int) -> dict:
    """
    Convert a FeatureVector to a flat CSV row dict.

    Identity columns:
        image_name        — filename of the processed image
        source_image      — for forged images, the stem encodes the source
                            (e.g. 05_aze_passport_CA01_blur.tif →
                             source = 05_aze_passport_CA01.tif)
        document_category — immediate parent directory name
        label             — 0 = authentic, 1 = forged
    """
    image_name = source_path.name
    category   = source_path.parent.name

    if label == _LABEL_FORGED:
        parts        = source_path.stem.rsplit("_", 1)
        source_image = (parts[0] + source_path.suffix) if len(parts) == 2 else image_name
    else:
        source_image = image_name

    row: dict = {
        "image_name":        image_name,
        "source_image":      source_image,
        "document_category": category,
        "label":             label,
    }
    for name in FEATURE_NAMES:
        v = vector.features.get(name)
        row[name] = "" if v is None else v
    return row


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _open_csv(path: Path):
    """Open *path* for writing and return (file_handle, DictWriter)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fh     = path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(fh, fieldnames=_CSV_COLUMNS)
    writer.writeheader()
    return fh, writer


# ---------------------------------------------------------------------------
# Processing loop
# ---------------------------------------------------------------------------

async def _run_split(
    images: list[Path],
    label: int,
    pipeline: PipelineManager,
    fusion_svc: EvidenceFusionService,
    extractor: FeatureExtractor,
    out_csv: Path,
    desc: str,
) -> tuple[int, int]:
    """
    Process all *images*, write rows to *out_csv* incrementally.

    Rows are flushed after every image so a crash does not lose progress.

    Returns:
        (n_processed, n_failed)
    """
    n_ok = n_fail = 0
    fh, writer = _open_csv(out_csv)
    try:
        for path in _progress(images, desc=desc, total=len(images), unit="img"):
            row = await _process_image(path, label, pipeline, fusion_svc, extractor)
            if row is None:
                n_fail += 1
                continue
            writer.writerow(row)
            fh.flush()
            n_ok += 1
    finally:
        fh.close()
    return n_ok, n_fail


# ---------------------------------------------------------------------------
# dataset.csv merge
# ---------------------------------------------------------------------------

def _merge_csvs(authentic_csv: Path, forged_csv: Path, dataset_csv: Path) -> int:
    """
    Concatenate authentic and forged CSVs into a single dataset.csv.

    Authentic rows are written first, then forged.  The ML training step
    should shuffle during cross-validation rather than here.

    Returns:
        Total row count written.
    """
    dataset_csv.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with dataset_csv.open("w", newline="", encoding="utf-8") as out_fh:
        writer = csv.DictWriter(out_fh, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for src in (authentic_csv, forged_csv):
            if not src.exists():
                log.warning("Merge: source CSV not found — %s", src)
                continue
            with src.open(encoding="utf-8") as in_fh:
                for row in csv.DictReader(in_fh):
                    writer.writerow(row)
                    total += 1
    return total


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def _print_summary(
    n_auth_ok: int,
    n_auth_fail: int,
    n_forg_ok: int,
    n_forg_fail: int,
    n_total: int,
    output_dir: Path,
    elapsed: float,
) -> None:
    print("\n" + "=" * 60)
    print("  Feature Extraction — Summary")
    print("=" * 60)
    print(f"  Authentic images processed : {n_auth_ok}")
    print(f"  Forged images processed    : {n_forg_ok}")
    print(f"  Failed images              : {n_auth_fail + n_forg_fail}")
    print(f"  Feature columns            : {len(FEATURE_NAMES)}")
    print(f"  Total dataset rows         : {n_total}")
    print(f"  Elapsed time               : {elapsed:.1f}s")
    print()
    print("  Output files:")
    print(f"    {output_dir / 'features_authentic.csv'}")
    print(f"    {output_dir / 'features_forged.csv'}")
    print(f"    {output_dir / 'dataset.csv'}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def _main(
    authentic_dir: Path,
    forged_dir: Path,
    output_dir: Path,
    dry_run: bool,
) -> None:
    """
    Orchestrate the full feature extraction run.

    Args:
        authentic_dir: Root of the authentic image dataset.
        forged_dir:    Root of the forged image dataset.
        output_dir:    Directory where CSV outputs are written.
        dry_run:       When True, discover images and print counts only.
    """
    t_start = time.perf_counter()

    authentic_images = _discover(authentic_dir) if authentic_dir.is_dir() else []
    forged_images    = _discover(forged_dir)    if forged_dir.is_dir()    else []

    print(f"\nAuthentic images found : {len(authentic_images)}")
    print(f"Forged images found    : {len(forged_images)}")
    print(f"Feature columns        : {len(FEATURE_NAMES)}")

    if dry_run:
        print("\nDry-run — no files written.\n")
        return

    if not authentic_images and not forged_images:
        print("No images found — nothing to do.")
        return

    pipeline, fusion_svc = _build_pipeline()
    extractor            = FeatureExtractor()

    authentic_csv = output_dir / "features_authentic.csv"
    forged_csv    = output_dir / "features_forged.csv"
    dataset_csv   = output_dir / "dataset.csv"

    n_auth_ok = n_auth_fail = 0
    if authentic_images:
        n_auth_ok, n_auth_fail = await _run_split(
            authentic_images, _LABEL_AUTHENTIC,
            pipeline, fusion_svc, extractor,
            authentic_csv, desc="Authentic",
        )

    n_forg_ok = n_forg_fail = 0
    if forged_images:
        n_forg_ok, n_forg_fail = await _run_split(
            forged_images, _LABEL_FORGED,
            pipeline, fusion_svc, extractor,
            forged_csv, desc="Forged",
        )

    n_total = _merge_csvs(authentic_csv, forged_csv, dataset_csv)

    elapsed = time.perf_counter() - t_start
    _print_summary(
        n_auth_ok, n_auth_fail,
        n_forg_ok, n_forg_fail,
        n_total, output_dir, elapsed,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract forensic features from authentic and forged images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--authentic",
        type=Path,
        required=True,
        metavar="DIR",
        help="Path to the authentic image root",
    )
    parser.add_argument(
        "--forged",
        type=Path,
        required=True,
        metavar="DIR",
        help="Path to the forged image root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        metavar="DIR",
        help="Directory where features_authentic.csv, features_forged.csv, and dataset.csv are written",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Discover images and print counts only — do not run the pipeline",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(_main(
        authentic_dir=args.authentic.resolve(),
        forged_dir=args.forged.resolve(),
        output_dir=args.output.resolve(),
        dry_run=args.dry_run,
    ))
