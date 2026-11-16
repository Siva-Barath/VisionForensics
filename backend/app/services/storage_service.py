"""
StorageService — all filesystem I/O for document storage.

No route or pipeline stage touches the filesystem directly.
Guarantees path traversal prevention, directory jail confinement,
and strictly prohibits silent overwriting of original uploaded exhibits.
"""

from __future__ import annotations
import re
from pathlib import Path

from app.config.settings import Settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def save_upload(self, content: bytes, document_id: str, original_filename: str) -> Path:
        """Persist raw upload bytes and return the stored path. Never overwrites existing files."""
        destination = self._upload_path(document_id, original_filename)
        if destination.exists():
            logger.warning("Attempted overwrite on existing exhibit: %s", destination)
            raise StorageError(f"Exhibit '{destination.name}' already exists. Overwrites prohibited.")
        self._write(content, destination)
        return destination

    def upload_path(self, document_id: str, original_filename: str) -> Path:
        """Return the path where an upload would be stored (without writing)."""
        return self._upload_path(document_id, original_filename)

    def processed_dir(self, document_id: str) -> Path:
        """Return the directory for processed (PDF page) images of a document."""
        base = Path(self._settings.processed_dir).resolve()
        safe_id = re.sub(r"[^\w\-]", "", document_id)[:64]
        target = (base / safe_id).resolve()
        if not str(target).startswith(str(base)):
            raise StorageError("Path traversal detected in processed directory.")
        return target

    def ensure_directories(self) -> None:
        """Create all configured storage directories if they do not exist."""
        for d in (
            self._settings.upload_dir,
            self._settings.processed_dir,
            self._settings.reports_dir,
            self._settings.heatmaps_dir,
        ):
            Path(d).mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured directory: %s", d)

    # ------------------------------------------------------------------ #
    # Private helpers                                                    #
    # ------------------------------------------------------------------ #

    def _upload_path(self, document_id: str, original_filename: str) -> Path:
        base = Path(self._settings.upload_dir).resolve()
        safe_name = self._sanitize(original_filename)
        safe_id = re.sub(r"[^\w\-]", "", document_id)[:64]
        target = (base / f"{safe_id}_{safe_name}").resolve()
        if not str(target).startswith(str(base)):
            logger.critical("Path traversal attempt blocked: filename='%s'", original_filename)
            raise StorageError("Path traversal attempt detected.")
        return target

    @staticmethod
    def _sanitize(filename: str) -> str:
        # Strip all directory traversal markers
        clean_name = Path(filename).name
        stem = Path(clean_name).stem
        ext = Path(clean_name).suffix.lower()
        # Restrict stem to alphanumeric and hyphen
        safe_stem = re.sub(r"[^\w\-]", "_", stem)[:64]
        # Whitelist extension characters
        safe_ext = re.sub(r"[^\w.]", "", ext)[:10]
        return f"{safe_stem}{safe_ext}"

    @staticmethod
    def _write(content: bytes, destination: Path) -> None:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            logger.info("Stored file: %s (%d bytes)", destination, len(content))
        except OSError as exc:
            logger.error("Failed to write %s: %s", destination, exc)
            raise StorageError(str(exc)) from exc
