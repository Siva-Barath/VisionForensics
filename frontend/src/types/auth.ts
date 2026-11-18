export type UserRole = 'FORENSIC_ANALYST' | 'SENIOR_INVESTIGATOR' | 'SYSTEM_ADMINISTRATOR';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
  last_login?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface DocumentSummary {
  id: string;
  original_filename: string;
  file_type: string;
  size_bytes: number;
  status: string;
  page_count: number;
  sha256_hash?: string;
  created_at: string;
  uploader_id?: string;
  overall_verdict?: string;
  unified_risk_tier?: string;
  composite_risk_score?: number;
}
