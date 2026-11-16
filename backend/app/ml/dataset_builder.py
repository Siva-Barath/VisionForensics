"""
DatasetBuilder — builds a labelled feature dataset from a directory of documents.

Usage
-----
    builder = DatasetBuilder(document_service)
    await builder.build(
        input_dir=Path("data/raw"),
        output_csv=Path("data/dataset.csv"),
        label_map={"forged": ["forged/"], "authentic": ["authentic/"]},
    )

label_map keys are label strings; values are path prefixes (relative to
input_dir) used to assign labels.  Files that match no prefix get label "".

The builder calls DocumentService.ingest() for each file, then
FeatureExtractor.extract(), and appends one row per document to the CSV.
After writing, _validate_csv() verifies column order, column count,
feature count, metadata count, and row count — aborting with a descriptive
error if any check fails.
"""
from __future__ import annotations

import csv
import io
import logging
from pathlib import Path

from fastapi import UploadFile

from app.services.document_service import DocumentService
from app.ml.feature_extractor import FeatureExtractor
from app.ml.feature_registry import FEATURE_NAMES
from app.ml.feature_vector import FeatureVector

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

_METADATA_COLUMNS = ["document_id", "original_filename", "file_type", "label"]
CSV_COLUMNS = _METADATA_COLUMNS + FEATURE_NAMES

_EXPECTED_COLUMN_COUNT   = len(CSV_COLUMNS)
_EXPECTED_FEATURE_COUNT  = len(FEATURE_NAMES)
_EXPECTED_METADATA_COUNT = len(_METADATA_COLUMNS)


class DatasetBuilder:
    def __init__(self, document_service: DocumentService) -> None:
        self._service = document_service
        self._extractor = FeatureExtractor()

    async def build(
        self,
        input_dir: Path,
        output_csv: Path,
        label_map: dict[str, list[str]] | None = None,
    ) -> int:
        """
        Process every supported file under input_dir and write output_csv.

        Returns the number of rows written.
        Raises RuntimeError if post-build CSV validation fails.
        """
        files = [
            p for p in sorted(input_dir.rglob("*"))
            if p.is_file() and p.suffix.lower() in _SUPPORTED_EXTENSIONS
        ]
        if not files:
            logger.warning("DatasetBuilder: no supported files found in %s", input_dir)
            return 0

        output_csv.parent.mkdir(parents=True, exist_ok=True)

        rows_written = 0
        with output_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            writer.writeheader()

            for path in files:
                label = self._resolve_label(path, input_dir, label_map or {})
                try:
                    vector = await self._process_file(path, label)
                    writer.writerow(vector.to_row(FEATURE_NAMES))
                    rows_written += 1
                    logger.info("DatasetBuilder: processed %s → label=%s", path.name, label)
                except Exception as exc:
                    logger.error("DatasetBuilder: failed on %s — %s", path.name, exc)

        logger.info("DatasetBuilder: wrote %d rows to %s", rows_written, output_csv)
        self._validate_csv(output_csv, rows_written)
        return rows_written

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _process_file(self, path: Path, label: str | None) -> FeatureVector:
        content = path.read_bytes()
        upload = _BytesUploadFile(filename=path.name, content=content)
        context = await self._service.ingest(upload)
        return self._extractor.extract(context, label=label)

    @staticmethod
    def _validate_csv(path: Path, expected_rows: int) -> None:
        """Abort with a descriptive error if the written CSV is structurally invalid."""
        if not path.exists():
            raise RuntimeError(
                f"DatasetBuilder: output CSV was not created at {path}"
            )

        with path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            actual_columns = list(reader.fieldnames or [])
            rows = list(reader)

        # 1. Column count
        actual_col_count = len(actual_columns)
        if actual_col_count != _EXPECTED_COLUMN_COUNT:
            raise RuntimeError(
                f"DatasetBuilder: CSV column count mismatch — "
                f"expected {_EXPECTED_COLUMN_COUNT}, got {actual_col_count}"
            )

        # 2. Column order
        if actual_columns != CSV_COLUMNS:
            mismatches = [
                f"col[{i}] expected={e!r} got={a!r}"
                for i, (e, a) in enumerate(zip(CSV_COLUMNS, actual_columns))
                if e != a
            ]
            raise RuntimeError(
                f"DatasetBuilder: CSV column order mismatch — {mismatches[:5]}"
            )

        # 3. Feature column count
        feature_cols = [c for c in actual_columns if c not in set(_METADATA_COLUMNS)]
        if len(feature_cols) != _EXPECTED_FEATURE_COUNT:
            raise RuntimeError(
                f"DatasetBuilder: feature column count mismatch — "
                f"expected {_EXPECTED_FEATURE_COUNT}, got {len(feature_cols)}"
            )

        # 4. Metadata column count
        meta_cols = [c for c in actual_columns if c in set(_METADATA_COLUMNS)]
        if len(meta_cols) != _EXPECTED_METADATA_COUNT:
            raise RuntimeError(
                f"DatasetBuilder: metadata column count mismatch — "
                f"expected {_EXPECTED_METADATA_COUNT}, got {len(meta_cols)}"
            )

        # 5. Row count
        if len(rows) != expected_rows:
            raise RuntimeError(
                f"DatasetBuilder: row count mismatch — "
                f"expected {expected_rows}, got {len(rows)}"
            )

        logger.info(
            "DatasetBuilder: CSV validation passed — "
            "%d columns (%d features + %d metadata), %d rows",
            actual_col_count, len(feature_cols), len(meta_cols), len(rows),
        )

    @staticmethod
    def _resolve_label(
        path: Path,
        base: Path,
        label_map: dict[str, list[str]],
    ) -> str | None:
        relative = str(path.relative_to(base)).replace("\\", "/")
        for label, prefixes in label_map.items():
            for prefix in prefixes:
                if relative.startswith(prefix.lstrip("/")):
                    return label
        return None


class _BytesUploadFile(UploadFile):
    """Minimal UploadFile backed by in-memory bytes — no temp file needed."""

    def __init__(self, filename: str, content: bytes) -> None:
        super().__init__(filename=filename, file=io.BytesIO(content))
        self._content = content

    async def read(self, size: int = -1) -> bytes:  # type: ignore[override]
        return self._content if size == -1 else self._content[:size]
