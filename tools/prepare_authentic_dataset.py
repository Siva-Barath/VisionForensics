"""
prepare_authentic_dataset.py

Extracts authentic document images from the MIDV-500 dataset into
TrainingDataset/authentic/<category>/ without modifying the source.

Usage:
    python tools/prepare_authentic_dataset.py
    python tools/prepare_authentic_dataset.py --midv path/to/MIDV500 --out path/to/TrainingDataset
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Capture-condition sub-folders to include (skip videos/, ground_truth/, etc.)
CAPTURE_CONDITIONS: frozenset[str] = frozenset(
    ["CA", "CS", "HA", "HS", "KA", "KS", "PA", "PS", "TA", "TS"]
)

# Keyword → category mapping (matched against the MIDV folder name, lower-cased)
CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("passport", "passport"),
    ("drvlic",   "driving_license"),
    ("id",       "id_card"),
]

IMAGE_SUFFIXES: frozenset[str] = frozenset([
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
])

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_category(folder_name: str) -> str | None:
    """Return the dataset category for a MIDV document folder name, or None to skip."""
    name = folder_name.lower()
    for keyword, category in CATEGORY_KEYWORDS:
        if keyword in name:
            return category
    return None


def build_dest_filename(doc_folder: str, condition: str, src: Path, index: int) -> str:
    """
    Build a collision-free filename.

    Format: <doc_folder>_<condition><index><suffix>
    Example: aze_passport_CA05_01.jpg  →  aze_passport_CA_01.jpg
    We keep the original stem to preserve as much provenance as possible,
    but prefix with the document folder so names are globally unique.
    """
    return f"{doc_folder}_{condition}{index:02d}{src.suffix.lower()}"


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def process_midv(midv_root: Path, out_root: Path) -> None:
    """
    Scan *midv_root*, copy qualifying images into *out_root*/authentic/<category>/.

    Args:
        midv_root: Path to the MIDV500 directory.
        out_root:  Path to the TrainingDataset directory.
    """
    if not midv_root.is_dir():
        log.error("MIDV500 directory not found: %s", midv_root)
        raise SystemExit(1)

    counts: dict[str, int] = defaultdict(int)
    skipped = 0

    # Each top-level sub-folder is one document type (e.g. 01_alb_passport)
    doc_folders = sorted(p for p in midv_root.iterdir() if p.is_dir())
    log.info("Found %d document folders in %s", len(doc_folders), midv_root)

    for doc_dir in doc_folders:
        category = resolve_category(doc_dir.name)
        if category is None:
            log.debug("Skipping unrecognised folder: %s", doc_dir.name)
            skipped += 1
            continue

        dest_dir = out_root / "authentic" / category
        dest_dir.mkdir(parents=True, exist_ok=True)

        images_root = doc_dir / "images"
        if not images_root.is_dir():
            log.warning("No images/ sub-folder in %s — skipping", doc_dir.name)
            continue

        for condition_dir in sorted(images_root.iterdir()):
            if not condition_dir.is_dir():
                # Skip the reference .tif scan sitting directly in images/
                continue
            if condition_dir.name not in CAPTURE_CONDITIONS:
                log.debug("Ignoring non-capture folder: %s", condition_dir)
                continue

            image_files = sorted(
                f for f in condition_dir.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_SUFFIXES
            )

            for idx, src in enumerate(image_files, start=1):
                dest_name = build_dest_filename(
                    doc_dir.name, condition_dir.name, src, idx
                )
                dest = dest_dir / dest_name

                if dest.exists():
                    log.debug("Already exists, skipping: %s", dest_name)
                    continue

                shutil.copy2(src, dest)
                counts[category] += 1
                log.debug("Copied %s → %s/%s", src.name, category, dest_name)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    total = sum(counts.values())
    print("\n" + "=" * 50)
    print("  Authentic Dataset — Build Summary")
    print("=" * 50)
    print(f"  Passports copied:         {counts.get('passport', 0)}")
    print(f"  ID cards copied:          {counts.get('id_card', 0)}")
    print(f"  Driving licenses copied:  {counts.get('driving_license', 0)}")
    print(f"  Total images:             {total}")
    print(f"  Skipped (unrecognised):   {skipped}")
    print("=" * 50 + "\n")

    log.info("Done. %d images written to %s", total, out_root / "authentic")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Build authentic dataset from MIDV-500.")
    parser.add_argument(
        "--midv",
        type=Path,
        default=repo_root / "MIDV500",
        help="Path to the MIDV500 root directory (default: <repo>/MIDV500)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=repo_root / "TrainingDataset",
        help="Path to the TrainingDataset root directory (default: <repo>/TrainingDataset)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    log.info("MIDV500 source : %s", args.midv)
    log.info("Output root    : %s", args.out)
    process_midv(args.midv, args.out)
