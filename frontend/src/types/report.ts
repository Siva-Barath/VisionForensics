/**
 * report.ts — TypeScript interfaces for forensic report generation and downloads.
 */

export interface ReportGenerationRequest {
  document_id: string;
  comparison_id?: string | null;
  title?: string | null;
  analyst_notes?: string | null;
  include_comparison?: boolean;
  include_evidence_images?: boolean;
}

export interface ReportSummaryResponse {
  report_id: string;
  report_number: string;
  document_id: string;
  document_name: string;
  title: string;
  status: string;
  sha256_hash: string;
  file_size_bytes: number;
  page_count: number;
  unified_risk_tier: string;
  overall_verdict: string;
  ml_probability?: number | null;
  download_url: string;
  created_at: string;
  case_id?: string | null;
  case_number?: string | null;
  case_title?: string | null;
  report_type?: string;
  key_findings?: string[];
  composite_risk_score?: number | null;
}

export interface ReportStats {
  total_reports: number;
  finalized: number;
  in_progress: number;
  under_review: number;
  requires_action: number;
}

export interface ReportDetailResponse {
  report_id: string;
  report_number: string;
  document_id: string;
  title: string;
  status: string;
  sha256_hash: string;
  file_size_bytes: number;
  page_count: number;
  analysis_version: number;
  analyst_notes?: string | null;
  metadata_snapshot: Record<string, any>;
  download_url: string;
  created_at: string;
}
