"""
forgery_generator.py

Main orchestrator for the forgery generation pipeline.

This module wires together:
- GeneratorRegistry  — discovers and holds all generator plugins
- ForgeryGenerator   — scans the authentic dataset and produces forged images

All dataset paths are supplied via CLI so the script works regardless of
where the datasets are stored relative to the repository.

Usage::

    # Dry-run — statistics only, no files written
    python tools/forgery_generator.py \\
        --input  "D:\\Datasets\\TrainingDataset\\authentic" \\
        --dry-run

    # Validation run — process only the first 20 images
    python tools/forgery_generator.py \\
        --input  "D:\\Datasets\\TrainingDataset\\authentic" \\
        --output "D:\\Datasets\\TrainingDataset\\forged" \\
        --max-images 20

    # Full generation run
    python tools/forgery_generator.py \\
        --input    "D:\\Datasets\\TrainingDataset\\authentic" \\
        --output   "D:\\Datasets\\TrainingDataset\\forged" \\
        --metadata "D:\\Datasets\\TrainingDataset\\metadata.csv"
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

# Ensure the repo root is on sys.path when run directly
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.config import ForgeryConfig
from tools.generators import (
    BlurGenerator,
    BrightnessGenerator,
    CopyMoveGenerator,
    JpegGenerator,
    LogoGenerator,
    NoiseGenerator,
    SignatureGenerator,
    TextGenerator,
)
from tools.metadata_writer import ForgeryRecord, MetadataWriter
from tools.utils import ensure_directory, load_image, save_image, supported_extensions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generator protocol (structural — no ABC import required)
# ---------------------------------------------------------------------------

class _GeneratorProtocol:
    """
    Documents the interface every generator must satisfy.

    Attributes:
        name: Unique forgery-type identifier, e.g. ``"blur"``.
    """

    name: str

    def apply(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """Apply the forgery and return the modified image."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class GeneratorRegistry:
    """
    Holds all registered generator instances and provides filtered access.

    Generators are registered at construction time from the canonical list.
    No generator is instantiated lazily — all are available immediately.
    """

    def __init__(self, generators: list) -> None:
        """
        Args:
            generators: List of instantiated generator objects.
        """
        self._generators: dict[str, object] = {g.name: g for g in generators}
        log.info(
            "GeneratorRegistry initialised | generators=%s",
            list(self._generators.keys()),
        )

    def all(self) -> list:
        """Return all registered generators."""
        return list(self._generators.values())

    def get(self, name: str) -> object:
        """
        Return the generator registered under *name*.

        Raises:
            KeyError: If no generator with that name is registered.
        """
        if name not in self._generators:
            raise KeyError(f"No generator registered with name '{name}'")
        return self._generators[name]

    def filter(self, names: list[str]) -> list:
        """
        Return only the generators whose names appear in *names*.

        Args:
            names: Subset of generator names to activate.
                   Empty list returns all generators.

        Returns:
            Filtered list of generator instances.
        """
        if not names:
            return self.all()
        return [self._generators[n] for n in names if n in self._generators]

    def __len__(self) -> int:
        return len(self._generators)

    def __repr__(self) -> str:
        return f"GeneratorRegistry(generators={list(self._generators.keys())})"


def build_registry() -> GeneratorRegistry:
    """
    Instantiate every generator and return a populated GeneratorRegistry.

    To add a new generator: import it here and append an instance to the list.
    """
    return GeneratorRegistry([
        SignatureGenerator(),
        LogoGenerator(),
        TextGenerator(),
        CopyMoveGenerator(),
        BlurGenerator(),
        NoiseGenerator(),
        JpegGenerator(),
        BrightnessGenerator(),
    ])


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ForgeryGenerator:
    """
    Top-level orchestrator for the forgery generation pipeline.

    Phase 16.2 behaviour: discovers authentic images and reports statistics.
    Phase 16.3 will call each generator's apply() to produce forged images.

    Args:
        config:   ForgeryConfig controlling all pipeline parameters.
        registry: Populated GeneratorRegistry.
    """

    def __init__(self, config: ForgeryConfig, registry: GeneratorRegistry) -> None:
        self._config = config
        self._registry = registry
        self._rng = np.random.default_rng(config.random_seed)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def load_generators(self) -> list:
        """
        Return the active generator list, filtered by config.enabled_generators.

        Returns:
            List of generator instances that will be applied during a run.
        """
        active = self._registry.filter(self._config.enabled_generators)
        log.info(
            "Active generators | count=%d | names=%s",
            len(active),
            [g.name for g in active],
        )
        return active

    def discover_authentic_images(self) -> list[Path]:
        """
        Recursively collect all supported image files under config.input_dir.

        When ``config.max_images`` is set, only the first N images (sorted
        alphabetically) are returned — this enables safe validation runs
        before processing the full dataset.

        Returns:
            Sorted list of absolute image paths, capped at max_images if set.

        Raises:
            SystemExit: If input_dir does not exist.
        """
        input_dir = self._config.input_dir
        if not input_dir.is_dir():
            log.error("Authentic dataset directory not found: %s", input_dir)
            raise SystemExit(1)

        exts = supported_extensions()
        images = sorted(
            p for p in input_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in exts
        )

        if self._config.max_images is not None:
            images = self._balanced_sample(images, self._config.max_images)

        self._print_discovery_summary(input_dir, images)
        return images

    def _balanced_sample(self, images: list[Path], max_images: int) -> list[Path]:
        """
        Sample up to *max_images* paths with approximately equal representation
        from every category (parent directory name).

        Algorithm:
        1. Group images by category.
        2. Distribute the quota evenly: base = max_images // n_categories.
        3. Assign one extra image to the first *remainder* categories
           (sorted alphabetically for determinism).
        4. If a category has fewer images than its quota, use all of them
           and redistribute the surplus to the remaining categories in a
           second pass.
        5. Within each category, sample without replacement using self._rng.

        Args:
            images:     Full sorted list of authentic image paths.
            max_images: Maximum total images to return.

        Returns:
            Balanced sample as a flat sorted list.
        """
        # Group by category (immediate parent directory name)
        by_category: dict[str, list[Path]] = {}
        for img in images:
            cat = img.parent.name
            by_category.setdefault(cat, []).append(img)

        categories = sorted(by_category.keys())  # alphabetical for determinism
        n_cats = len(categories)

        if n_cats == 0:
            return []

        # --- Initial quota allocation --------------------------------------- #
        base, remainder = divmod(max_images, n_cats)
        # First `remainder` categories get one extra image
        quotas: dict[str, int] = {
            cat: base + (1 if i < remainder else 0)
            for i, cat in enumerate(categories)
        }

        # --- Redistribute surplus from under-stocked categories ------------ #
        # Iterate until stable (at most n_cats passes)
        for _ in range(n_cats):
            surplus = 0
            needy: list[str] = []
            for cat in categories:
                available = len(by_category[cat])
                if available < quotas[cat]:
                    surplus += quotas[cat] - available
                    quotas[cat] = available
                else:
                    needy.append(cat)
            if surplus == 0:
                break
            # Spread surplus across categories that still have headroom
            extra_base, extra_rem = divmod(surplus, len(needy)) if needy else (0, 0)
            for i, cat in enumerate(needy):
                quotas[cat] += extra_base + (1 if i < extra_rem else 0)

        # --- Sample within each category ------------------------------------ #
        sampled: list[Path] = []
        sample_counts: dict[str, int] = {}
        for cat in categories:
            pool = by_category[cat]
            n = min(quotas[cat], len(pool))
            if n == 0:
                sample_counts[cat] = 0
                continue
            indices = self._rng.choice(len(pool), size=n, replace=False)
            chosen = [pool[int(i)] for i in sorted(indices)]
            sampled.extend(chosen)
            sample_counts[cat] = n

        # Print validation sampling summary
        print("\nValidation sampling:")
        for cat in categories:
            print(f"  {cat:<22}: {sample_counts.get(cat, 0)}")
        print(f"  {'Total':<22}: {len(sampled)}")
        print()

        log.info(
            "Balanced validation sample | max_images=%d | actual=%d | categories=%s",
            max_images, len(sampled), sample_counts,
        )
        return sorted(sampled)

    @staticmethod
    def _print_discovery_summary(input_dir: Path, images: list[Path]) -> None:
        """Print a per-extension breakdown of discovered images to stdout."""
        # Group by normalised extension (.tif and .tiff counted together under TIFF)
        _EXT_LABELS: list[tuple[frozenset[str], str]] = [
            (frozenset([".tif", ".tiff"]), "TIFF"),
            (frozenset([".jpg", ".jpeg"]), "JPEG"),
            (frozenset([".png"]),          "PNG"),
            (frozenset([".bmp"]),          "BMP"),
        ]
        counts: dict[str, int] = {label: 0 for _, label in _EXT_LABELS}
        for img in images:
            ext = img.suffix.lower()
            for exts, label in _EXT_LABELS:
                if ext in exts:
                    counts[label] += 1
                    break

        print("\nAuthentic directory:")
        print(f"  {input_dir}")
        print("\nFiles discovered:")
        for _, label in _EXT_LABELS:
            print(f"  {label:<6}: {counts[label]}")
        print(f"  {'Total':<6}: {len(images)}")
        print()

    def statistics(self, images: list[Path], active_generators: list) -> None:
        """
        Print a summary of what the pipeline *would* produce.

        No files are read or written.

        Args:
            images:            List of discovered authentic image paths.
            active_generators: Generators that will be applied.
        """
        n_images = len(images)
        n_generators = len(active_generators)
        n_forged = n_images * self._config.target_forged_per_authentic

        # Per-category breakdown
        category_counts: dict[str, int] = {}
        for img in images:
            # The category is the name of the immediate parent directory
            cat = img.parent.name
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print("\n" + "=" * 55)
        print("  Forgery Generation Framework — Dry-Run Statistics")
        print("=" * 55)
        print(f"  Authentic images found:       {n_images}")
        print(f"  Active generators:            {n_generators}")
        print(f"    " + ", ".join(g.name for g in active_generators))
        print(f"  Forged per authentic:         {self._config.target_forged_per_authentic}")
        print(f"  Estimated forged dataset size:{n_forged:>6}")
        print(f"  Estimated total dataset size: {n_images + n_forged}")
        if category_counts:
            print()
            print("  Breakdown by category:")
            for cat, count in sorted(category_counts.items()):
                est = count * self._config.target_forged_per_authentic
                print(f"    {cat:<22} authentic={count:>4}  forged~{est:>4}")
        print("=" * 55 + "\n")

    # ------------------------------------------------------------------ #
    # Implemented generators — only these are safe to call apply() on     #
    # ------------------------------------------------------------------ #

    _IMPLEMENTED: frozenset[str] = frozenset(["jpeg", "blur", "noise", "brightness", "text", "copy_move", "signature", "logo"])

    def _active_implemented(self, active: list) -> list:
        """Filter *active* to only generators with a working apply()."""
        return [g for g in active if g.name in self._IMPLEMENTED]

    def _build_dest_path(self, source: Path, generator_name: str) -> Path:
        """
        Construct the output path for a forged image.

        The original filename stem is preserved so every forged image is
        immediately traceable back to its authentic source.

        Format:  <output_dir>/<category>/<original_stem>_<generator>.<ext>
        JPEG generator always uses .jpg regardless of the source extension.

        Examples:
            05_aze_passport_CA01.tif  + blur       →  05_aze_passport_CA01_blur.tif
            05_aze_passport_CA01.tif  + jpeg       →  05_aze_passport_CA01_jpeg.jpg
        """
        category = source.parent.name
        dest_dir = self._config.output_dir / category
        ensure_directory(dest_dir)
        suffix = ".jpg" if generator_name == "jpeg" else source.suffix
        return dest_dir / f"{source.stem}_{generator_name}{suffix}"

    def _generate_one(
        self,
        source: Path,
        generator,
        writer: MetadataWriter,
    ) -> bool:
        """
        Apply *generator* to the image at *source* and save the result.

        Returns True if the image was written, False if it already existed.
        """
        dest = self._build_dest_path(source, generator.name)
        if dest.exists():
            log.debug("Already exists, skipping | %s", dest.name)
            return False

        image = load_image(source)

        # Pass only the range parameters the generator needs
        kwargs = self._range_kwargs(generator.name)
        forged, meta = generator.apply(image, self._rng, **kwargs)

        save_image(forged, dest)

        writer.add_record(ForgeryRecord(
            image_name=dest.name,
            source_image=source.name,
            document_category=source.parent.name,
            forgery_type=generator.name,
            severity=meta.get("severity"),
            generator=type(generator).__name__,
            label=1,
        ))
        return True

    def _range_kwargs(self, generator_name: str) -> dict:
        """Return the config range parameters for the named generator."""
        cfg = self._config
        return {
            "jpeg":       {"jpeg_quality_range": cfg.jpeg_quality_range},
            "blur":       {"blur_kernel_range": cfg.blur_kernel_range},
            "noise":      {"noise_sigma_range": cfg.noise_sigma_range},
            "brightness": {"brightness_range": cfg.brightness_range},
        }.get(generator_name, {})

    def run(self, dry_run: bool = False) -> None:
        """
        Execute the pipeline.

        Args:
            dry_run: When True, only prints statistics — no files are read
                     or written.  Defaults to False so the script generates
                     images unless ``--dry-run`` is passed explicitly.
        """
        log.info(
            "ForgeryGenerator starting | seed=%d | dry_run=%s | max_images=%s",
            self._config.random_seed, dry_run, self._config.max_images,
        )
        t_start = time.perf_counter()

        active_generators = self.load_generators()
        images = self.discover_authentic_images()
        self.statistics(images, active_generators)

        if dry_run:
            log.info("Dry-run complete — no images modified")
            return

        # ------------------------------------------------------------------ #
        # Generation loop                                                     #
        # ------------------------------------------------------------------ #
        impl_generators = self._active_implemented(active_generators)
        if not impl_generators:
            log.warning("No implemented generators active — nothing to generate")
            return

        writer = MetadataWriter()
        gen_usage: dict[str, int] = {g.name: 0 for g in impl_generators}
        category_counts: dict[str, int] = {}
        total_written = 0

        for source in images:
            # Randomly select up to target_forged_per_authentic generators
            n = min(self._config.target_forged_per_authentic, len(impl_generators))
            chosen_indices = self._rng.choice(len(impl_generators), size=n, replace=False)
            chosen = [impl_generators[int(i)] for i in chosen_indices]

            for gen in chosen:
                written = self._generate_one(source, gen, writer)
                if written:
                    gen_usage[gen.name] = gen_usage.get(gen.name, 0) + 1
                    cat = source.parent.name
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    total_written += 1

        # Persist metadata
        writer.save_csv(self._config.metadata_path)
        writer.save_json(self._config.metadata_path.with_suffix(".json"))

        elapsed = time.perf_counter() - t_start
        self._print_run_statistics(
            len(images), total_written, gen_usage, category_counts,
            len(writer), elapsed,
        )
        log.info("ForgeryGenerator finished | forged=%d | elapsed=%.1fs", total_written, elapsed)

    def _print_run_statistics(
        self,
        n_authentic: int,
        n_forged: int,
        gen_usage: dict[str, int],
        category_counts: dict[str, int],
        n_metadata_records: int,
        elapsed: float,
    ) -> None:
        """Print a post-run summary to stdout."""
        print("\n" + "=" * 55)
        print("  Forgery Generation — Run Summary")
        print("=" * 55)
        print(f"  Authentic images processed: {n_authentic}")
        print(f"  Forged images generated:    {n_forged}")
        print(f"  Metadata records written:   {n_metadata_records}")
        print(f"  Elapsed time:               {elapsed:.1f}s")
        print()
        print("  Generator usage:")
        for name, count in sorted(gen_usage.items()):
            print(f"    {name:<18} {count}")
        if category_counts:
            print()
            print("  Per-category forged:")
            for cat, count in sorted(category_counts.items()):
                print(f"    {cat:<22} {count}")
        print("=" * 55 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Forgery generation pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        metavar="DIR",
        help="Path to the authentic dataset root (e.g. D:\\Datasets\\TrainingDataset\\authentic)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        metavar="DIR",
        help="Path for forged image output.  Defaults to <input>/../forged",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        metavar="FILE",
        help="Path for metadata CSV output.  Defaults to <input>/../metadata.csv",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--generators",
        nargs="*",
        default=[],
        metavar="NAME",
        help="Restrict to specific generators by name (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Print statistics only — do not generate any files",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        dest="max_images",
        metavar="N",
        help="Process only the first N authentic images (validation mode)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    input_dir = args.input.resolve()
    # Derive sibling defaults so --output and --metadata are optional
    output_dir  = args.output.resolve()   if args.output   else input_dir.parent / "forged"
    metadata_path = args.metadata.resolve() if args.metadata else input_dir.parent / "metadata.csv"

    log.info("Input dir    : %s", input_dir)
    log.info("Output dir   : %s", output_dir)
    log.info("Metadata path: %s", metadata_path)

    config = ForgeryConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        metadata_path=metadata_path,
        random_seed=args.seed,
        enabled_generators=args.generators,
        max_images=args.max_images,
    )

    registry = build_registry()
    generator = ForgeryGenerator(config, registry)
    generator.run(dry_run=args.dry_run)
