/**
 * comparison.ts — TypeScript interfaces for forensic document comparison.
 */

export interface ComparisonRequest {
  document_a_id: string;
  document_b_id: string;
  page_a?: number;
  page_b?: number;
  align_images?: boolean;
}

export interface ComparisonBoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DifferentialRegion {
  region_id: string;
  category: string;
  bounding_box: ComparisonBoundingBox;
  polygon: number[][];
  severity: number;
  area: number;
  page_a: number;
  page_b: number;
}

export interface ComparisonAlignment {
  status: 'FEATURE_ALIGNED' | 'FALLBACK_DIRECT_RESIZE' | 'DIRECT_RESIZE_UNALIGNED' | 'ALIGNMENT_FAILED' | string;
  confidence: number;
  keypoints_detected_a: number;
  keypoints_detected_b: number;
  matches_found: number;
}

export interface ComparisonMetrics {
  similarity_score: number;
  ssim_score: number;
  difference_percentage: number;
  differing_pixels: number;
  total_pixels: number;
}

export interface ComparisonDocumentMetadata {
  document_id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  page_count: number;
  current_page: number;
  sha256_hash: string;
  dimensions: [number, number];
}

export interface ComparisonMetadataDiff {
  document_a: ComparisonDocumentMetadata;
  document_b: ComparisonDocumentMetadata;
  dimension_match: boolean;
  page_count_match: boolean;
  format_match: boolean;
  hash_match: boolean;
}

export interface ComparisonSummary {
  verdict_category: 'IDENTICAL' | 'LOCALIZED_DIFFERENCES' | 'SIGNIFICANT_DIFFERENCES' | 'DIFFERENT_DOCUMENTS' | 'INCONCLUSIVE_ALIGNMENT' | string;
  differential_regions_count: number;
  forensic_caveat: string;
}

export interface ComparisonResponse {
  comparison_id: string;
  document_a_id: string;
  document_b_id: string;
  page_a: number;
  page_b: number;
  alignment: ComparisonAlignment;
  metrics: ComparisonMetrics;
  differential_regions: DifferentialRegion[];
  metadata_diff: ComparisonMetadataDiff;
  summary: ComparisonSummary;
  artifact_urls: {
    diff_heatmap: string;
    diff_mask: string;
    aligned_b: string;
  };
  created_at: string;
}
