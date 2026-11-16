/**
 * analysis.ts — Authoritative TypeScript definitions for forensic analysis responses.
 * Strictly reflects backend Pydantic models from backend/app/schemas/analysis.py.
 */

export type UnifiedRiskTier = 'LOW_RISK' | 'SUSPICIOUS' | 'HIGH_RISK' | 'UNKNOWN';

export type InferenceStatus = 'SUCCESS' | 'DEGRADED' | 'ML_UNAVAILABLE';

export type PredictedClass = 'AUTHENTIC' | 'FORGED';

export interface ForensicLimitationItem {
  code: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | string;
  message: string;
}

export interface BoundingBoxResponse {
  points: [number, number][];
}

export interface DetectedRegionResponse {
  id: string;
  evidence_id?: string | null;
  detector: string;
  category: string;
  severity: number;
  confidence?: number;
  description: string;
  page_index?: number;
  bounding_box: BoundingBoxResponse;
}

export interface PageDimension {
  page_index: number;
  width: number;
  height: number;
  dpi?: number;
}

export interface DocumentDimensions {
  width: number;
  height: number;
  page_count?: number;
  pages?: PageDimension[];
}

export interface DecisionTraceItem {
  track: string;
  finding: string;
  description?: string | null;
  evidence_items?: Array<{
    category: string;
    severity: number;
    description: string;
    [key: string]: unknown;
  }> | null;
  features_considered?: string | null;
}

export interface Track1MLSummary {
  available: boolean;
  status: InferenceStatus | string;
  forgery_probability: number | null;
  predicted_class: PredictedClass | null;
  feature_vector?: Record<string, number | null>;
  risk_tier: UnifiedRiskTier | string;
  operational_threshold: number; // Default: 0.40
  feature_completeness: number; // 0.0 - 1.0
  imputed_features: Record<string, number>;
  top_contributing_features: Record<string, number>;
}

export interface Track2SymbolicSummary {
  available: boolean;
  symbolic_severity_score: number;
  symbolic_evidence: Array<{
    category: string;
    severity: number;
    description: string;
    [key: string]: unknown;
  }>;
}

export interface PageMLSummary {
  page_index: number;
  forgery_probability: number | null;
  predicted_class: PredictedClass | string | null;
  risk_tier: UnifiedRiskTier | string;
  status: string;
  feature_completeness: number;
  top_contributing_features: Record<string, number>;
}

export interface VisualEvidenceSummary {
  available: boolean;
  detected_clusters: number;
  max_cluster_confidence: number;
  total_inlier_matches: number;
  copy_move_confirmed: boolean;
  visual_tier: UnifiedRiskTier | string;
  evidence_items: Array<Record<string, unknown>>;
}

export interface CompressionQualificationSummary {
  is_jpeg: boolean;
  estimated_quality: number | null;
  is_heavily_compressed: boolean;
  compression_notice?: string | null;
}

export interface DocumentAnalysisResponse {
  heatmap_available_pages?: number[];
  module_statuses?: Record<string, { status: 'COMPLETED' | 'PARTIAL' | 'UNAVAILABLE' | 'NOT IMPLEMENTED' | 'NOT APPLICABLE' | 'FAILED'; reason: string }>;
  raw_ml?: (Track1MLSummary & { source_page_index: number | null; selection_method: string; is_document_probability: false }) | null;
  document_id: string;
  job_id: string;
  original_filename: string;
  file_type: string;
  status: string;
  overall_verdict: string;
  unified_risk_tier: UnifiedRiskTier;
  risk_description: string;
  composite_risk_score: number; // 0.0 - 100.0 display score
  track_1_ml: Track1MLSummary;
  track_2_symbolic: Track2SymbolicSummary;
  track_3_visual?: VisualEvidenceSummary | null;
  compression_qualification?: CompressionQualificationSummary | null;
  pages_ml?: PageMLSummary[];
  decision_trace: DecisionTraceItem[];
  limitations: ForensicLimitationItem[];
  warnings: string[];
  processing_time_ms?: number | null;
  detected_regions?: DetectedRegionResponse[];
  image_dimensions?: DocumentDimensions | null;
  preview_available?: boolean;
  metadata_info?: Record<string, any> | null;
}
