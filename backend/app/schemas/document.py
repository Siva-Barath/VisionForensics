from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier for async tracking")
    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    filename: str = Field(..., description="Sanitized filename as stored on disk")
    original_filename: str = Field(..., description="Original filename provided by the user")
    path: str = Field(..., description="Relative storage path")
    type: str = Field(..., description="Detected file format (pdf, png, jpeg)")
    size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Document processing status")
    processing_status: str = Field(..., description="Pipeline execution status")
    pipeline_stage: str = Field(..., description="Last completed pipeline stage")
    page_count: Optional[int] = Field(None, description="Number of pages (PDF only)")
    pages: Optional[list[str]] = Field(None, description="Paths to converted page images (PDF only)")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings from pipeline stages")
    processing_time_ms: Optional[float] = Field(None, description="Total pipeline execution time in milliseconds")


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    environment: str
    modules: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    details: Optional[list] = None


class DocumentListItem(BaseModel):
    id: str = Field(..., description="Unique document UUID")
    original_filename: str = Field(..., description="Filename provided at upload")
    file_type: str = Field(..., description="Detected file format")
    size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    page_count: Optional[int] = Field(1, description="Page count")
    sha256_hash: Optional[str] = Field(None, description="Cryptographic SHA-256 hash")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    uploader_id: Optional[str] = Field(None, description="Uploader user UUID")
    overall_verdict: Optional[str] = Field(None, description="Synthesized verdict")
    unified_risk_tier: Optional[str] = Field(None, description="Risk tier: LOW_RISK, SUSPICIOUS, HIGH_RISK, UNKNOWN")
    composite_risk_score: Optional[float] = Field(None, description="Composite risk score 0-100")

