export interface UploadResponse {
  job_id: string;
  document_id: string;
  filename: string;
  original_filename: string;
  path: string;
  type: string;
  size_bytes: number;
  status: string;
  processing_status: string;
  pipeline_stage: string;
  page_count?: number | null;
  pages?: string[] | null;
  warnings?: string[];
  processing_time_ms?: number | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  modules?: Record<string, { status: string; reason?: string; integrity_verified?: boolean }>;
}

export interface WorkspaceStats {
  total_cases: number;
  total_documents: number;
  examined_documents: number;
  requires_review: number;
  high_risk: number;
  low_risk: number;
  unknown: number;
}

export interface InvestigationCase {
  id: string;
  case_number: string;
  title: string;
  notes?: string | null;
  status: string;
  priority: string;
  document_count: number;
  created_at: string;
  updated_at?: string;
  final_assessment?: 'HIGH_RISK' | 'SUSPICIOUS' | 'LOW_RISK' | 'PENDING' | string;
  primary_document_id?: string | null;
  exhibit_filenames?: string[];
}

export interface CaseStats {
  total_cases: number;
  active: number;
  under_review: number;
  completed: number;
  escalated: number;
}

export interface ApiError {
  error: string;
  status_code: number;
  details?: unknown[];
}

export type UploadState =
  | { phase: 'idle' }
  | { phase: 'uploading'; progress: number }
  | { phase: 'success'; result: UploadResponse }
  | { phase: 'error'; message: string };

export interface ModelIntegrityVerification {
  status: 'VERIFIED' | 'FAILED';
  verified_at: string;
  model: {
    name: string;
    version: string;
    trees: number;
    criterion: string;
    operational_threshold: number;
    expected_sha256: string;
    actual_sha256: string;
    verified: boolean;
    feature_count: number;
  };
  schema: {
    name: string;
    version: string;
    expected_sha256: string;
    actual_sha256: string;
    verified: boolean;
    feature_count: number;
  };
  decision_threshold: {
    threshold: number;
    status: string;
    protocol: string;
    superseded_thresholds: number[];
  };
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  event_type: string;
  category: string;
  status: string;
  sha256_hash?: string;
  user_id?: string;
  user_email?: string;
  ip_address?: string;
  details?: Record<string, any>;
}

export * from './analysis';
export * from './comparison';
export * from './report';
export * from './auth';

