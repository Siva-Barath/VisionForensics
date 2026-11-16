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

export * from './analysis';
export * from './comparison';
export * from './report';
export * from './auth';

