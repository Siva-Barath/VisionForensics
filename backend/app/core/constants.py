"""Application-wide constants."""

# Supported MIME types and their canonical format names
ALLOWED_MIME_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
}

# Allowed file extensions (used as a secondary check)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"pdf", "png", "jpg", "jpeg"})

# Document processing statuses
class DocumentStatus:
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


# Pipeline execution statuses
class PipelineStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # some stages skipped due to non-fatal errors


# Canonical pipeline stage names — order matters
PIPELINE_STAGE_ORDER: list[str] = [
    "upload",
    "preprocessing",
    "ocr",
    "layout",
    "metadata",
    "forgery",
    "document_classification",
    "ml_inference",
    "risk",
    "explainability",
    "report",
]

# PDF conversion settings
PDF_DPI = 200
PDF_IMAGE_FORMAT = "PNG"
