"""
comparison.py — Pydantic schemas for document comparison requests and responses.
Defines data structures for differential analysis, alignment, and metrics.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas.analysis import BoundingBoxResponse


class ComparisonRequest(BaseModel):
    """Request payload to initiate a forensic comparison between two documents."""
    document_a_id: str = Field(..., description="UUID of primary reference document exhibit")
    document_b_id: str = Field(..., description="UUID of comparison document exhibit")
    page_a: int = Field(0, ge=0, description="0-indexed page number of Document A")
    page_b: int = Field(0, ge=0, description="0-indexed page number of Document B")
    align_images: bool = Field(True, description="Whether to perform automated feature-based alignment/registration")


class ComparisonBoundingBox(BaseModel):
    """Bounding box coordinates for a differential region."""
    x: int
    y: int
    width: int
    height: int


class DifferentialRegionResponse(BaseModel):
    """Forensic region exhibiting visual or structural discrepancy between exhibits."""
    region_id: str
    category: str
    bounding_box: ComparisonBoundingBox
    polygon: List[List[int]]
    severity: float
    area: int
    page_a: int
    page_b: int


class ComparisonAlignmentResponse(BaseModel):
    """Status and metrics of geometric alignment and registration."""
    status: str
    confidence: float
    keypoints_detected_a: int
    keypoints_detected_b: int
    matches_found: int


class ComparisonMetricsResponse(BaseModel):
    """Quantitative comparison metrics."""
    similarity_score: float
    ssim_score: float
    difference_percentage: float
    differing_pixels: int
    total_pixels: int


class ComparisonDocumentMetadata(BaseModel):
    """Metadata summary of an individual document exhibit."""
    document_id: str
    filename: str
    file_type: str
    size_bytes: int
    page_count: int
    current_page: int
    sha256_hash: str
    dimensions: List[int]


class ComparisonMetadataDiff(BaseModel):
    """Differential metadata analysis between two document exhibits."""
    document_a: ComparisonDocumentMetadata
    document_b: ComparisonDocumentMetadata
    dimension_match: bool
    page_count_match: bool
    format_match: bool
    hash_match: bool


class ComparisonSummaryResponse(BaseModel):
    """Forensic summary and defensibility caveats."""
    verdict_category: str
    differential_regions_count: int
    forensic_caveat: str


class ComparisonResponse(BaseModel):
    """Complete forensic comparison result."""
    comparison_id: str
    document_a_id: str
    document_b_id: str
    page_a: int
    page_b: int
    alignment: ComparisonAlignmentResponse
    metrics: ComparisonMetricsResponse
    differential_regions: List[DifferentialRegionResponse]
    metadata_diff: ComparisonMetadataDiff
    summary: ComparisonSummaryResponse
    artifact_urls: Dict[str, str]
    created_at: str
