"""
Pure storage utility functions.

Business logic (where to store, how to name files) lives in StorageService.
These helpers are low-level primitives with no dependencies on settings or services.
"""

import uuid
import re
from pathlib import Path


def generate_document_id() -> str:
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from a filename, preserving the extension."""
    stem = Path(filename).stem
    ext = Path(filename).suffix
    safe_stem = re.sub(r'[^\w\-]', '_', stem)[:64]
    return f"{safe_stem}{ext}"
