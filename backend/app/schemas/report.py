"""
report.py — Pydantic schemas for forensic investigation report generation and export.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ReportGenerationRequest(BaseModel):
    """Payload to request compilation of a forensic investigation PDF report."""
    document_id: str = Field(..., description="UUID of primary document exhibit")
    comparison_id: Optional[str] = Field(None, description="Optional UUID of linked comparison record to include")
    title: Optional[str] = Field(None, description="Custom title for the investigation report")
    analyst_notes: Optional[str] = Field(None, description="Analyst-authored observations and conclusions")
    include_comparison: bool = Field(True, description="Whether to include linked comparison findings if available")
    include_evidence_images: bool = Field(True, description="Whether to embed evidence crops and heatmaps")


class ReportSummaryResponse(BaseModel):
    """Brief metadata summary of a generated forensic report."""
    report_id: str
    report_number: str
    document_id: str
    document_name: str
    title: str
    status: str
    sha256_hash: str
    file_size_bytes: int
    page_count: int
    unified_risk_tier: str
    overall_verdict: str
    ml_probability: Optional[float]
    download_url: str
    created_at: str


class ReportDetailResponse(BaseModel):
    """Complete record of a forensic investigation report."""
    report_id: str
    report_number: str
    document_id: str
    title: str
    status: str
    sha256_hash: str
    file_size_bytes: int
    page_count: int
    analysis_version: int
    analyst_notes: Optional[str]
    metadata_snapshot: Dict[str, Any]
    download_url: str
    created_at: str
