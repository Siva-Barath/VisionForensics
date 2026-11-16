# VisionForensics AI — API Integration & Security Audit
**Base URL:** `https://127.0.0.1:8443/api/v1`  
**Proxy:** Nginx 1.27 Alpine (`frontend/nginx.pilot.conf`)  
**Backend:** FastAPI 0.111+ ASGI (`backend/app`)  
**Database:** PostgreSQL 17 Alpine (`backend/app/models`)  
**Audit Date:** 2026-11-01  
**Status:** FULLY INTEGRATED & VERIFIED (PASS)

---

## 1. API Route Inventory & Security Matrix

| Method | Endpoint Path | Auth Required | RBAC Scope | IDOR Guard | Description | Frontend Caller |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| `GET` | `/health` | No | Public | None | Service liveness probe and environment verification. | `checkHealth()` |
| `POST` | `/auth/register` | No | Public | None | Public self-registration for forensic examiners. | `apiRegister()` |
| `POST` | `/auth/login` | No | Public | Rate Limited | Authenticates credentials with Argon2id, issues JWT & cookies. | `apiLogin()` |
| `POST` | `/auth/refresh` | No | Public | Token Lock | Rotates refresh token, issues fresh 15m JWT access token. | `apiRefreshToken()` |
| `POST` | `/auth/logout` | Yes | Authenticated | None | Revokes refresh token in database, deletes cookies. | `apiLogout()` |
| `GET` | `/auth/me` | Yes | Authenticated | None | Retrieves authenticated user profile, email, and role. | `apiGetMe()` |
| `GET` | `/admin/users` | Yes | `SYSTEM_ADMIN` | None | Lists all user accounts and activation statuses. | Admin Console |
| `POST` | `/admin/users` | Yes | `SYSTEM_ADMIN` | None | Administrative account creation with explicit role. | Admin Console |
| `PUT` | `/admin/users/{id}/status`| Yes | `SYSTEM_ADMIN` | None | Updates user activation or role; deactivation revokes sessions. | Admin Console |
| `GET` | `/admin/audit-logs` | Yes | `SYSTEM_ADMIN` | None | Retrieves immutable security audit ledger entries. | Admin Console |
| `POST` | `/upload` | Yes | Authenticated | Rate Limited | Ingests document exhibit, checks hash, runs 11-stage pipeline. | `uploadDocument()` |
| `GET` | `/documents` | Yes | Authenticated | Filtered | Lists document exhibits accessible to caller. | `listDocuments()` |
| `GET` | `/documents/{id}/analysis`| Yes | Authenticated | Strict | Retrieves full multi-track analysis, ML scores, and regions. | `getDocumentAnalysis()` |
| `GET` | `/documents/{id}/image` | Yes | Authenticated | Strict | Serves preprocessed raster page image with hash check. | `getDocumentImageUrl()` |
| `GET` | `/documents/{id}/custody-logs`| Yes | Authenticated | Strict | Returns complete defensible chain of custody history. | `get_document_custody_logs` |
| `POST` | `/comparison` | Yes | Authenticated | Dual-Exhibit | Computes ORB alignment, homography, SSIM, and diff mask. | `compareDocuments()` |
| `GET` | `/comparison/{id}` | Yes | Authenticated | Dual-Exhibit | Retrieves comparison metrics, alignment matrix, and regions. | `getComparison()` |
| `GET` | `/comparison/{id}/artifacts/{type}`| Yes | Authenticated | Dual-Exhibit | Serves comparison artifact images (`diff_heatmap`, `diff_mask`).| `getComparisonArtifactUrl()` |
| `POST` | `/reports` | Yes | Authenticated | Strict | Generates defense-grade forensic PDF report with SHA-256. | `generateReport()` |
| `GET` | `/reports` | Yes | Authenticated | Filtered | Lists forensic PDF reports accessible to caller. | `listReports()` |
| `GET` | `/reports/{id}` | Yes | Authenticated | Strict | Retrieves forensic report metadata and analysis snapshot. | `getReport()` |
| `GET` | `/reports/{id}/download`| Yes | Authenticated | Strict | Streams verified PDF dossier with `X-Report-SHA256` header. | `getReportDownloadUrl()` |

---

## 2. Granular Integration Verifications

### 2.1 Exhibit Intake & Storage Ingestion (`POST /upload`)
- **Multipart Form Payload:** `file: UploadFile` (PDF, PNG, JPG, JPEG, TIFF)
- **Security Protections:**
  - In-memory rate limiting: 10 uploads/min per IP.
  - MIME type sniffing and magic byte validation.
  - Cryptographic SHA-256 computation upon file stream read.
  - Association of `uploader_id` with authenticated user UUID.
- **Pipeline Execution:** Synchronous execution across 11 stages (`UploadStage` through `ReportStage`).
- **Response Structure:** `UploadResponse` returning `document_id`, `job_id`, `status: "processed"`, `processing_status: "COMPLETED"`, `processing_time_ms`.

### 2.2 Analysis Retrieval & Tamper Alarm (`GET /documents/{id}/analysis`)
- **Authorization & IDOR Protection:**
  - Calls `check_document_access(document_id, current_user, db, request)`.
  - Non-owners receive `HTTP 403 Forbidden` and generate an `AUTHZ_FAILURE` security audit log.
- **Cryptographic File Integrity Verification:**
  - Before returning analysis data, the service reads the on-disk exhibit and recalculates its SHA-256 digest.
  - If the hash differs from the database custody record, an `HTTP 409 Conflict` (`TAMPERING_ALARM`) is raised and recorded in `exhibit_custody_logs`.
- **Response Structure:** `DocumentAnalysisResponse` returning:
  - `overall_verdict`: Synthesized forensic verdict.
  - `unified_risk_tier`: `LOW_RISK` | `SUSPICIOUS` | `HIGH_RISK` | `UNKNOWN`.
  - `composite_risk_score`: Calibrated 0–100 score for UI visualization.
  - `track_1_ml`: Random Forest predictions, 18 features, feature completeness, top contributing features.
  - `track_2_symbolic`: Symbolic severity score and metadata anomaly breakdown.
  - `track_3_visual`: ORB cluster count, inlier matches, and copy-move confirmation.
  - `compression_qualification`: Non-destructive JPEG quality estimation and qualification notice.
  - `pages_ml`: Per-page ML predictions for multi-page documents.
  - `decision_trace`: Step-by-step audit trail.
  - `limitations`: System boundary notices.
  - `detected_regions`: Visual polygons and bounding box coordinates.

### 2.3 Exhibit Image Serving (`GET /documents/{id}/image`)
- **Query Parameter:** `page: int = 0` (0-indexed page number)
- **Authentication Support:** Checks Bearer Authorization header, HttpOnly `access_token` cookie, or `?token=` query param.
- **Integrity Check:** Verifies disk exhibit SHA-256 prior to streaming image.
- **Content-Type:** `image/png` or `image/jpeg`.

### 2.4 Document Differential Comparison (`POST /comparison`)
- **Payload:** `ComparisonRequest` (`document_a_id`, `document_b_id`, `page_a`, `page_b`, `align_images`).
- **Security Check:** Caller must have authorized access to **BOTH** exhibits; prevents cross-case evidence leakage.
- **Differential Engine:**
  - ORB keypoint feature detection.
  - RANSAC Homography estimation ($3\times3$ transformation matrix, inlier count).
  - Structural Similarity Index Measure (SSIM) score.
  - Generates diff heatmap and diff mask images on disk.
- **Persistence:** Saved in `document_comparisons` table with unique UUID.

### 2.5 Report Generation & Streaming (`POST /reports` & `GET /reports/{id}/download`)
- **Payload:** `ReportGenerationRequest` (`document_id`, `comparison_id`, `title`, `analyst_notes`, `include_comparison`).
- **PDF Compilation:** ReportLab engine formats multi-page dossier with metadata header, exhibit hashes, ML probabilities, decision trace, and custody history.
- **Cryptographic Sealing:** Computes SHA-256 hash of generated PDF; records `REPORT_GENERATED` in custody log.
- **Download Route:** Streams file with headers:
  - `Content-Disposition: attachment; filename="<report_number>.pdf"`
  - `X-Report-SHA256: <sha256_hash>`
  - `Cache-Control: private, no-cache, no-store, must-revalidate`
- **Custody Event:** Records `REPORT_DOWNLOADED` with client IP and user ID.

---

## 3. Disconnects & Fixes Executed

| Component | Identified Defect | Remediation Executed |
| :--- | :--- | :--- |
| `frontend/src/services/api.ts` | No `Authorization` header attached; no token stored. | Implemented Bearer token injection, storage helpers, and 401 transparent auto-refresh response interceptor. |
| `backend/app/api/auth.py` | Did not set `access_token` cookie; only set `refresh_token`. | Configured `access_token` cookie on login and refresh so that `<img>` tags and PDF downloads load natively without query string leaking. |
| `backend/app/api/documents.py` | Missing `/documents` list endpoint; frontend had to use hardcoded mocks. | Implemented `GET /api/v1/documents` with access control filtering and latest analysis aggregation. |
| `frontend/src/pages/CasesPage.tsx` | Displayed 4 hardcoded mock cases (`mockCases`). | Connected to `listDocuments()` to display real database exhibits, hashes, verdicts, and page counts. |
| `frontend/src/pages/HomePage.tsx` | Hardcoded active caseload list. | Connected to `listDocuments(5, 0)` for live active caseload exhibits. |
| `frontend/src/pages/AnalyticsPage.tsx` | Hardcoded mock stats ("1.2K cases", "Confirmed Forgeries 89"). | Rewrote to compute dynamic metrics from database exhibits; eliminated prohibited claim "Confirmed Forgeries". |
| `frontend/src/pages/SettingsPage.tsx` | Showed editable slider claiming risk threshold could be set to 65%. | Replaced with read-only model governance card showing locked $T = 0.40$ and frozen model SHA-256. |
