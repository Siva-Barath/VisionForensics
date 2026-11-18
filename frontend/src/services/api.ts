import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  UploadResponse,
  HealthResponse,
  DocumentAnalysisResponse,
  TokenResponse,
  LoginCredentials,
  RegisterData,
  User,
  DocumentSummary,
  WorkspaceStats,
  InvestigationCase,
  CaseStats,
  ModelIntegrityVerification,
  AuditLogEntry,
} from '@/types';

const TOKEN_KEY = 'vf_access_token';
const REFRESH_TOKEN_KEY = 'vf_refresh_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // ignore local storage errors in private browsing
  }
}

export function getStoredRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredRefreshToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  } catch {
    // ignore
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // ignore
  }
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60_000,
  withCredentials: true, // Send HttpOnly refresh cookies automatically
});

// Request Interceptor: Attach Bearer Access Token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getStoredToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Concurrency mutex for token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor: Intercept 401 and transparently refresh token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (!originalRequest) {
      return Promise.reject(error);
    }

    // Do not attempt refresh on auth endpoints to avoid infinite loops
    const url = originalRequest.url || '';
    const isAuthRoute =
      url.includes('/auth/login') ||
      url.includes('/auth/register') ||
      url.includes('/auth/refresh') ||
      url.includes('/auth/logout');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRoute) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = getStoredRefreshToken();
        const { data } = await api.post<TokenResponse>(
          '/auth/refresh',
          refreshToken ? { refresh_token: refreshToken } : {}
        );
        setStoredToken(data.access_token);
        if (data.refresh_token) {
          setStoredRefreshToken(data.refresh_token);
        }
        processQueue(null, data.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        clearStoredToken();
        window.dispatchEvent(new CustomEvent('vf_auth_unauthorized'));
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------- //
// Authentication Endpoints                                               //
// ---------------------------------------------------------------------- //

export async function apiLogin(credentials: LoginCredentials): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', credentials);
  setStoredToken(data.access_token);
  if (data.refresh_token) {
    setStoredRefreshToken(data.refresh_token);
  }
  return data;
}

export async function apiRegister(payload: RegisterData): Promise<User> {
  const { data } = await api.post<User>('/auth/register', payload);
  return data;
}

export async function apiLogout(): Promise<void> {
  try {
    const refreshToken = getStoredRefreshToken();
    await api.post('/auth/logout', refreshToken ? { refresh_token: refreshToken } : {});
  } finally {
    clearStoredToken();
  }
}

export async function apiGetMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}

export async function apiRefreshToken(): Promise<TokenResponse> {
  const refreshToken = getStoredRefreshToken();
  const { data } = await api.post<TokenResponse>(
    '/auth/refresh',
    refreshToken ? { refresh_token: refreshToken } : {}
  );
  setStoredToken(data.access_token);
  if (data.refresh_token) {
    setStoredRefreshToken(data.refresh_token);
  }
  return data;
}

// ---------------------------------------------------------------------- //
// Document & Investigation Endpoints                                     //
// ---------------------------------------------------------------------- //

export async function listDocuments(
  limit: number = 50,
  skip: number = 0
): Promise<DocumentSummary[]> {
  const { data } = await api.get<DocumentSummary[]>('/documents', {
    params: { limit, skip },
  });
  return data;
}

export async function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void,
  caseDetails?: { title: string; notes: string; priority: 'routine' | 'urgent' }
): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  if (caseDetails?.title.trim()) {
    form.append('case_title', caseDetails.title.trim());
    form.append('case_notes', caseDetails.notes);
    form.append('priority', caseDetails.priority);
  }

  const { data } = await api.post<UploadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });

  return data;
}

export async function getDocumentAnalysis(
  documentId: string
): Promise<DocumentAnalysisResponse> {
  const { data } = await api.get<DocumentAnalysisResponse>(`/documents/${documentId}/analysis`);
  return data;
}

export async function getDocumentCustodyLogs(
  documentId: string
): Promise<Array<{
  id: string;
  document_id: string;
  event_type: string;
  timestamp: string;
  user_id?: string | null;
  status: string;
  ip_address?: string | null;
  sha256_hash?: string | null;
  details?: Record<string, unknown> | null;
}>> {
  const { data } = await api.get(`/documents/${documentId}/custody-logs`);
  return data;
}

export function getDocumentImageUrl(documentId: string, page: number = 0): string {
  return `/api/v1/documents/${documentId}/image?page=${page}`;
}

export async function compareDocuments(
  params: import('@/types').ComparisonRequest
): Promise<import('@/types').ComparisonResponse> {
  const { data } = await api.post<import('@/types').ComparisonResponse>('/comparison', params);
  return data;
}

export async function getComparison(
  comparisonId: string
): Promise<import('@/types').ComparisonResponse> {
  const { data } = await api.get<import('@/types').ComparisonResponse>(`/comparison/${comparisonId}`);
  return data;
}

export function getComparisonArtifactUrl(
  comparisonId: string,
  artifactType: 'diff_heatmap' | 'diff_mask' | 'aligned_b'
): string {
  return `/api/v1/comparison/${comparisonId}/artifacts/${artifactType}`;
}

export async function generateReport(
  payload: import('@/types').ReportGenerationRequest
): Promise<import('@/types').ReportDetailResponse> {
  const { data } = await api.post<import('@/types').ReportDetailResponse>('/reports', payload);
  return data;
}

export async function getReport(
  reportId: string
): Promise<import('@/types').ReportDetailResponse> {
  const { data } = await api.get<import('@/types').ReportDetailResponse>(`/reports/${reportId}`);
  return data;
}

export async function listReports(
  limit: number = 150,
  offset: number = 0,
  status?: string,
  search?: string
): Promise<import('@/types').ReportSummaryResponse[]> {
  const { data } = await api.get<import('@/types').ReportSummaryResponse[]>('/reports', {
    params: { limit, offset, status, search },
  });
  return data;
}

export async function getReportStats(): Promise<import('@/types').ReportStats> {
  const { data } = await api.get<import('@/types').ReportStats>('/reports/stats');
  return data;
}

export function getReportDownloadUrl(reportId: string): string {
  return `/api/v1/reports/${reportId}/download`;
}

export function getReportPreviewPdfUrl(reportId: string): string {
  return `/api/v1/reports/${reportId}/pdf`;
}

export async function checkHealth(): Promise<HealthResponse> {
  try {
    const { data } = await api.get<HealthResponse>('/health');
    return data;
  } catch (error) {
    if (axios.isAxiosError<HealthResponse>(error) && error.response?.status === 503 && error.response.data.modules) {
      return error.response.data;
    }
    throw error;
  }
}

export async function getWorkspaceStats(): Promise<WorkspaceStats> {
  return (await api.get<WorkspaceStats>('/workspace/stats')).data;
}

export async function listCases(params?: { limit?: number; skip?: number; status?: string; search?: string }): Promise<InvestigationCase[]> {
  return (await api.get<InvestigationCase[]>('/cases', { params: { limit: 150, ...params } })).data;
}

export async function getCaseStats(): Promise<CaseStats> {
  return (await api.get<CaseStats>('/cases/stats')).data;
}

export async function createCase(payload: { title: string; notes?: string; priority?: string; status?: string }): Promise<InvestigationCase> {
  return (await api.post<InvestigationCase>('/cases', payload)).data;
}

export async function verifyModelIntegrity(): Promise<ModelIntegrityVerification> {
  return (await api.get<ModelIntegrityVerification>('/health/verify-integrity')).data;
}

export async function getAuditLogs(params?: {
  limit?: number;
  skip?: number;
  category?: string;
  search?: string;
}): Promise<AuditLogEntry[]> {
  return (await api.get<AuditLogEntry[]>('/admin/audit-logs', { params })).data;
}

export default api;
