"""
metadata_writer.py

Accumulates per-image forgery records during a generation run and
persists them as CSV and JSON at the end.  No file is written until
save_csv() or save_json() is called explicitly.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from tools.utils import ensure_directory

log = logging.getLogger(__name__)

# Canonical column order for the CSV output
_CSV_FIELDS: list[str] = [
    "image_name",
    "source_image",
    "document_category",
    "forgery_type",
    "severity",
    "generator",
    "label",
    "timestamp",
]


@dataclass
class ForgeryRecord:
    """
    Metadata for a single generated (or authentic) image entry.

    Attributes:
        image_name:         Filename of the output image.
        source_image:       Filename of the authentic source image.
        document_category:  e.g. ``"passport"``, ``"id_card"``.
        forgery_type:       e.g. ``"blur"``, ``"noise"``, ``"authentic"``.
        severity:           Numeric severity in [0.0, 1.0] or ``None``.
        generator:          Class name of the generator that produced this image.
        label:              ``0`` = authentic, ``1`` = forged.
        timestamp:          ISO-8601 UTC timestamp of record creation.
    """

    image_name: str
    source_image: str
    document_category: str
    forgery_type: str
    severity: float | None
    generator: str
    label: int
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MetadataWriter:
    """
    Collects ForgeryRecord objects and writes them to CSV and/or JSON.

    Usage::

        writer = MetadataWriter()
        writer.add_record(ForgeryRecord(...))
        writer.save_csv(Path("TrainingDataset/metadata.csv"))
        writer.save_json(Path("TrainingDataset/metadata.json"))
    """

    def __init__(self) -> None:
        self._records: list[ForgeryRecord] = []

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def add_record(self, record: ForgeryRecord) -> None:
        """
        Append a single ForgeryRecord to the in-memory collection.

        Args:
            record: Populated ForgeryRecord instance.
        """
        self._records.append(record)
        log.debug(
            "Record added | image=%s | type=%s | label=%d",
            record.image_name,
            record.forgery_type,
            record.label,
        )

    def save_csv(self, path: Path) -> None:
        """
        Write all accumulated records to a CSV file at *path*.

        The file is created (or overwritten) atomically.  Parent
        directories are created automatically.

        Args:
            path: Destination CSV file path.
        """
        ensure_directory(path.parent)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            for record in self._records:
                writer.writerow(asdict(record))
        log.info("Metadata CSV saved | path=%s | records=%d", path, len(self._records))

    def save_json(self, path: Path) -> None:
        """
        Write all accumulated records to a JSON file at *path*.

        Args:
            path: Destination JSON file path.
        """
        ensure_directory(path.parent)
        with path.open("w", encoding="utf-8") as fh:
            json.dump([asdict(r) for r in self._records], fh, indent=2)
        log.info("Metadata JSON saved | path=%s | records=%d", path, len(self._records))

    # ------------------------------------------------------------------ #
    # Introspection                                                        #
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> list[ForgeryRecord]:
        """Read-only view of accumulated records."""
        return list(self._records)
