"""
analysis.py — Pydantic schemas for the document forensic analysis retrieval endpoint.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DecisionTraceItem(BaseModel):
    track: str = Field(..., description="Pipeline track or synthesis step")
    finding: str = Field(..., description="Observed forensic measurement or status")
    description: Optional[str] = Field(None, description="Detailed explanation or guidance")
    evidence_items: Optional[List[Dict[str, Any]]] = Field(None, description="Granular evidence breakdown")
    features_considered: Optional[str] = Field(None, description="Input features evaluated")

class ForensicLimitationItem(BaseModel):
    code: str
    severity: str
    message: str

class BoundingBoxResponse(BaseModel):
    points: List[List[float | int]] = Field(default_factory=list, description="Polygon or bounding box coordinates [[x, y], ...]")

class DetectedRegionResponse(BaseModel):
    id: str = Field(..., description="Unique region identifier")
    evidence_id: Optional[str] = Field(None, description="Linked parent evidence identifier")
    detector: str = Field(..., description="Detector subsystem that identified the region")
    category: str = Field(..., description="Forensic category (IMAGE, COPY_MOVE, SIGNATURE, etc.)")
    severity: float = Field(..., description="Severity score 0-100")
    confidence: float = Field(1.0, description="Confidence of detection 0.0-1.0")
    description: str = Field(..., description="Forensic explanation of suspicious area")
    page_index: int = Field(0, description="0-indexed page number containing the region")
    bounding_box: BoundingBoxResponse = Field(..., description="Bounding box points")

class PageDimension(BaseModel):
    page_index: int = Field(..., description="0-indexed page number")
    width: int = Field(..., description="Page width in pixels")
    height: int = Field(..., description="Page height in pixels")
    dpi: int = Field(200, description="Rasterization DPI")

class DocumentDimensions(BaseModel):
    width: int = Field(..., description="Image width in pixels (primary page 0)")
    height: int = Field(..., description="Image height in pixels (primary page 0)")
    page_count: int = Field(1, description="Total document pages")
    pages: List[PageDimension] = Field(default_factory=list, description="Per-page pixel dimensions")

class Track1MLSummary(BaseModel):
    available: bool
    status: str
    forgery_probability: Optional[float]
    predicted_class: Optional[str]
    feature_vector: Dict[str, Optional[float]] = Field(default_factory=dict, description="Actual ordered model inputs; imputed entries identified separately")
    risk_tier: str
    operational_threshold: float = 0.40
    feature_completeness: float = 1.0
    imputed_features: Dict[str, float] = Field(default_factory=dict)
    top_contributing_features: Dict[str, float] = Field(default_factory=dict)

class RawMLResult(Track1MLSummary):
    source_page_index: Optional[int] = None
    selection_method: str
    is_document_probability: bool = False


class Track2SymbolicSummary(BaseModel):
    available: bool
    symbolic_severity_score: float
    symbolic_evidence: List[Dict[str, Any]] = Field(default_factory=list)

class PageMLSummary(BaseModel):
    page_index: int = Field(..., description="0-indexed page number")
    forgery_probability: Optional[float] = Field(None, description="Per-page Random Forest forgery probability")
    predicted_class: Optional[str] = Field(None, description="Per-page predicted class (AUTHENTIC or FORGED)")
    risk_tier: str = Field(..., description="Per-page risk tier")
    status: str = Field("SUCCESS", description="Per-page ML inference status")
    feature_completeness: float = Field(1.0, description="Per-page feature completeness")
    top_contributing_features: Dict[str, float] = Field(default_factory=dict)

class VisualEvidenceSummary(BaseModel):
    available: bool = Field(False)
    detected_clusters: int = Field(0)
    max_cluster_confidence: float = Field(0.0)
    total_inlier_matches: int = Field(0)
    copy_move_confirmed: bool = Field(False)
    visual_tier: str = Field("LOW_RISK")
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)

class CompressionQualificationSummary(BaseModel):
    is_jpeg: bool = Field(False)
    estimated_quality: Optional[float] = Field(None)
    is_heavily_compressed: bool = Field(False)
    compression_notice: Optional[str] = Field(None)

class DocumentAnalysisResponse(BaseModel):
    document_id: str = Field(..., description="Unique document UUID")
    job_id: str = Field(..., description="Pipeline job tracking UUID")
    original_filename: str = Field(..., description="Filename provided at upload")
    file_type: str = Field(..., description="Detected document format")
    status: str = Field(..., description="Document processing status")
    overall_verdict: str = Field(..., description="Synthesized forensic verdict")
    unified_risk_tier: str = Field(..., description="LOW_RISK | SUSPICIOUS | HIGH_RISK | UNKNOWN")
    risk_description: str = Field(..., description="Operational meaning of the assigned risk tier")
    composite_risk_score: float = Field(..., ge=0.0, le=100.0, description="0-100 composite risk score for UI display")
    track_1_ml: Track1MLSummary = Field(..., description="Statistical substrate ML analysis")
    raw_ml: Optional[RawMLResult] = Field(None, description="Unmodified model result for the identified source page; not a document-wide probability")
    module_statuses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    heatmap_available_pages: List[int] = Field(default_factory=list)
    track_2_symbolic: Track2SymbolicSummary = Field(..., description="Symbolic metadata, OCR, and layout analysis")
    track_3_visual: Optional[VisualEvidenceSummary] = Field(None, description="Independent Visual Evidence Track")
    compression_qualification: Optional[CompressionQualificationSummary] = Field(None, description="Non-destructive JPEG quality metrics")
    pages_ml: List[PageMLSummary] = Field(default_factory=list, description="Per-page ML predictions for multi-page documents")
    decision_trace: List[DecisionTraceItem] = Field(default_factory=list, description="Step-by-step audit trace")
    limitations: List[ForensicLimitationItem] = Field(default_factory=list, description="Forensic decision support disclaimers")
    warnings: List[str] = Field(default_factory=list, description="Extraction or processing warnings")
    processing_time_ms: Optional[float] = Field(None, description="Total pipeline processing latency")
    detected_regions: List[DetectedRegionResponse] = Field(default_factory=list, description="Detected visual evidence regions")
    image_dimensions: Optional[DocumentDimensions] = Field(None, description="Intrinsic pixel dimensions of document image")
    preview_available: bool = Field(True, description="Whether document image preview is available")
    metadata_info: Optional[Dict[str, Any]] = Field(None, description="Extracted EXIF or PDF metadata catalog")
