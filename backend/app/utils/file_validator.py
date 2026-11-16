"""
File validation utilities — strict magic byte detection, file parsing, and size/dimension limits.
Eliminates extension-only fallbacks to prevent malicious file uploads.
"""

from __future__ import annotations
import io
from pathlib import Path
from PIL import Image, ImageOps
import pypdfium2 as pdfium
from fastapi import UploadFile

from app.core.exceptions import UnsupportedFileTypeError, FileTooLargeError
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Authoritative Magic Byte Signatures
_PDF_MAGIC = b"%PDF"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_TIFF_LE_MAGIC = b"II*\x00"
_TIFF_BE_MAGIC = b"MM\x00*"


def _detect_file_type_from_magic_bytes(header: bytes) -> str:
    """
    Detects file type strictly from file content magic bytes.
    Zero extension fallback — files must have genuine format signatures.
    """
    if header.startswith(_PDF_MAGIC):
        return "pdf"
    if header.startswith(_PNG_MAGIC):
        return "png"
    if header.startswith(_JPEG_MAGIC):
        return "jpeg"
    if header.startswith(_TIFF_LE_MAGIC) or header.startswith(_TIFF_BE_MAGIC):
        return "tiff"
    return ""


def validate_file_content(content: bytes, file_type: str, settings) -> None:
    """
    Validates that the file parses properly according to its detected format
    and adheres to dimensional and page-count safety ceilings.
    """
    if file_type in ("png", "jpeg", "tiff"):
        try:
            # Enforce decompression bomb protection
            with Image.open(io.BytesIO(content)) as img:
                width, height = img.size
                if width > settings.max_image_dimension or height > settings.max_image_dimension:
                    raise FileTooLargeError(
                        f"Image dimensions ({width}x{height}) exceed maximum allowed limit of {settings.max_image_dimension}px"
                    )
                # Verify image structure
                img.verify()
        except FileTooLargeError:
            raise
        except Exception as exc:
            logger.warning("Image parsing validation failed: %s", exc)
            raise UnsupportedFileTypeError(f"Corrupted or invalid image structure: {exc}")

    elif file_type == "pdf":
        try:
            with pdfium.PdfDocument(content) as doc:
                page_count = len(doc)
                if not page_count:
                    raise UnsupportedFileTypeError("PDF has no pages")
                if page_count > settings.max_pdf_pages:
                    raise FileTooLargeError(
                        f"PDF page count ({page_count}) exceeds maximum allowed limit of {settings.max_pdf_pages} pages"
                    )
        except FileTooLargeError:
            raise
        except Exception as exc:
            logger.warning("PDF parsing validation failed: %s", exc)
            raise UnsupportedFileTypeError(f"Corrupted or invalid PDF structure: {exc}")


async def validate_upload(file: UploadFile, max_size_bytes: int) -> tuple[bytes, str]:
    """
    Reads upload content, strictly enforces magic byte signatures, validates internal
    file format parsing, and enforces size and dimension limits.

    Returns:
        (file_bytes, detected_type)

    Raises:
        UnsupportedFileTypeError: if magic bytes are invalid or content cannot be parsed.
        FileTooLargeError: if file size or dimensions exceed system thresholds.
    """
    settings = get_settings()
    content = await file.read(max_size_bytes + 1)

    # Enforce maximum byte size limit
    if len(content) > max_size_bytes:
        raise FileTooLargeError(max_size_bytes // (1024 * 1024))

    # Reject empty files
    if len(content) < 16:
        raise UnsupportedFileTypeError("File is empty or truncated below minimum header size.")

    # Strict magic byte identification (zero extension fallback)
    file_type = _detect_file_type_from_magic_bytes(content[:16])
    if not file_type:
        raw_ext = Path(file.filename or "unknown").suffix or "unknown"
        logger.warning(
            "Rejected upload with invalid magic bytes | filename='%s' claimed_ext='%s'",
            file.filename,
            raw_ext,
        )
        raise UnsupportedFileTypeError(raw_ext)

    # Validate image/pdf integrity and bounds
    validate_file_content(content, file_type, settings)

    logger.debug(
        "Validated upload exhibit '%s' | format=%s size=%d bytes",
        file.filename,
        file_type,
        len(content),
    )
    return content, file_type
