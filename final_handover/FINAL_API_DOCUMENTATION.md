# VisionForensics AI — Final API Documentation
## Comprehensive REST API Specification & Endpoint Integration Guide

**Document Reference:** `VF-API-FINAL-20261101`  
**API Version:** `v1`  
**Base URL:** `https://127.0.0.1:8443/api/v1`  
**Specification Standard:** OpenAPI 3.0 / JSON Schema  
**Date:** November 1, 2026

---

## 1. Authentication & Security Scheme

VisionForensics AI enforces token-based authentication using **Argon2id** password hashing and **JSON Web Tokens (JWT)** signed via HMAC-SHA256.

### Authentication Flow:
1. **Analyst Login:** Analyst posts credentials to `/api/v1/auth/login`. On successful authentication, the server returns a short-lived access token (`exp`: 15 minutes) and a sliding refresh token (`exp`: 7 days).
2. **Authorized Requests:** All subsequent API requests must include the Bearer token in the HTTP Authorization header:
   ```http
   Authorization: Bearer <access_token>
   ```
3. **Token Rotation:** Clients rotate expired access tokens via `/api/v1/auth/refresh`. When rotated, the old refresh token is immediately invalidated (single-use rotation) to prevent replay attacks.
4. **Role-Based Access Control (RBAC):**
   - `analyst`: Can upload exhibits, trigger analyses, perform comparisons, and export reports for their own investigations.
   - `admin`: Superuser authority with exclusive access to cross-tenant security audit logs and system custody ledgers.
5. **IDOR Prevention:** Analysts are strictly prohibited from viewing, comparing, or downloading documents owned by other investigators. Any unauthorized cross-tenant request immediately aborts with `HTTP 403 Forbidden`.

---

## 2. API Endpoints Directory

| Category | HTTP Method | Endpoint Path | Role Required | Description |
| :--- | :---: | :--- | :---: | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | Public | Authenticates analyst and issues JWT pair. |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Public | Exchanges valid refresh token for replacement JWT pair. |
| **Auth** | `POST` | `/api/v1/auth/logout` | Authenticated | Invalidates session and revokes refresh token. |
| **Auth** | `GET` | `/api/v1/auth/me` | Authenticated | Retrieves profile and role of authenticated user. |
| **Document** | `POST` | `/api/v1/upload` | `analyst` | Uploads and executes 11-stage forensic pipeline. |
| **Document** | `GET` | `/api/v1/documents/{id}` | `analyst` | Retrieves document metadata and ingestion status. |
| **Document** | `GET` | `/api/v1/documents/{id}/analysis` | `analyst` | Retrieves full multi-track analysis, `pages_ml`, and overlays. |
| **Document** | `GET` | `/api/v1/documents/{id}/file` | `analyst` | Streams original exhibit bytes with real-time SHA-256 check. |
| **Compare** | `POST` | `/api/v1/comparison` | `analyst` | Executes two-document differential alignment and SSIM. |
| **Compare** | `GET` | `/api/v1/comparison/{id}` | `analyst` | Retrieves comparison diff mask, SSIM score, and regions. |
| **Report** | `POST` | `/api/v1/reports` | `analyst` | Generates structured, signed forensic PDF investigation dossier. |
| **Report** | `GET` | `/api/v1/reports/{id}` | `analyst` | Retrieves report metadata, generation status, and SHA-256 hash. |
| **Report** | `GET` | `/api/v1/reports/{id}/download` | `analyst` | Streams signed PDF document with `X-Report-SHA256` header. |
| **Admin** | `GET` | `/api/v1/admin/audit-logs` | `admin` | Queries append-only security audit trail (logins, IDOR blocks). |
| **Health** | `GET` | `/api/v1/health` | Public | Healthcheck verifying database and pipeline readiness. |

---

## 3. Detailed Endpoint Specifications

### 3.1 Document Ingestion & Pipeline Execution (`POST /api/v1/upload`)

Uploads a document exhibit (TIFF, PNG, JPG, PDF), computes its initial SHA-256 hash, and synchronously executes the 11-stage forensic pipeline.

- **Request Format:** `multipart/form-data`
- **Form Parameters:**
  - `file`: Binary file stream (max 50 MB).
- **Rate Limit:** 10 requests per minute per IP address.

#### Example Request:
```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@exhibit_01_aut_drvlic.tif;type=image/tiff"
```

#### Example Response (`HTTP 201 Created`):
```json
{
  "document_id": "c8342634-6f59-4466-abed-0e6f37bdd16b",
  "filename": "exhibit_01_aut_drvlic.tif",
  "file_type": "image/tiff",
  "file_size": 4219488,
  "file_hash": "fa0b24486beb85b1c554581f1e967a23c0bf10e4a7810a9cf181512da5e0fa0c",
  "status": "COMPLETED",
  "created_at": "2026-11-01T11:22:21.492015Z",
  "analysis": {
    "document_id": "c8342634-6f59-4466-abed-0e6f37bdd16b",
    "unified_risk_tier": "LOW_RISK",
    "overall_verdict": "LOW_RISK / AUTHENTIC",
    "track_1_ml": {
      "forgery_probability": 0.2058,
      "predicted_class": "AUTHENTIC",
      "operational_threshold": 0.40,
      "feature_completeness": 1.0,
      "top_contributing_features": {
        "img_ela_max_difference_mean": 18.0,
        "img_laplacian_variance_mean": 163.19,
        "cm_inlier_matches": 28.0
      }
    },
    "pages_ml": [
      {
        "page_index": 0,
        "forgery_probability": 0.2058,
        "predicted_class": "AUTHENTIC",
        "risk_tier": "LOW_RISK",
        "status": "SUCCESS",
        "feature_completeness": 1.0,
        "top_contributing_features": {
          "img_ela_max_difference_mean": 18.0,
          "img_laplacian_variance_mean": 163.19,
          "cm_inlier_matches": 28.0
        }
      }
    ],
    "track_3_visual": {
      "available": true,
      "detected_clusters": 0,
      "max_cluster_confidence": 0.0,
      "total_inlier_matches": 28,
      "copy_move_confirmed": false,
      "visual_tier": "LOW_RISK",
      "evidence_items": []
    },
    "compression_qualification": {
      "is_jpeg": false,
      "estimated_quality": null,
      "is_heavily_compressed": false,
      "compression_notice": null
    },
    "detected_regions": [],
    "processing_time_ms": 1281.2
  }
}
```

---

### 3.2 Two-Document Differential Comparison (`POST /api/v1/comparison`)

Compares a suspect exhibit against an authentic reference standard. Aligns geometries, computes Structural Similarity Index (SSIM), and isolates differential regions.

#### Example Request (`POST /api/v1/comparison`):
```json
{
  "document_a_id": "c8342634-6f59-4466-abed-0e6f37bdd16b",
  "document_b_id": "1c795ad7-ac3a-4df2-b2f2-bccf49425a38",
  "page_a": 0,
  "page_b": 0,
  "align_images": true
}
```

#### Example Response (`HTTP 200 OK`):
```json
{
  "comparison_id": "a08beb3b-c5ad-4663-a9e5-02ddfbbde6f1",
  "similarity_score": 0.3078,
  "alignment": {
    "status": "FALLBACK_DIRECT_RESIZE",
    "confidence": 0.5,
    "transform_matrix": null
  },
  "metrics": {
    "ssim": 0.3078,
    "normalized_cross_correlation": 0.412,
    "mean_squared_error": 142.8
  },
  "differential_regions": [
    {
      "region_id": "DIFF-01",
      "bounding_box": [342, 110, 480, 165],
      "area_pixels": 7590,
      "severity": 85.0,
      "description": "Text altered: Expiration date and demographic field mismatch"
    }
  ],
  "latency_sec": 0.69
}
```

---

### 3.3 Forensic PDF Report Generation & Export (`POST /api/v1/reports`)

Generates a tamper-evident, multi-page forensic PDF dossier encapsulating investigation metadata, ML metrics, visual overlays, and custody logs.

#### Example Request (`POST /api/v1/reports`):
```json
{
  "document_id": "c8342634-6f59-4466-abed-0e6f37bdd16b",
  "title": "Forensic Examination — California Driving License Baseline",
  "analyst_notes": "Routine authentic baseline screening. All physical forensics within natural tolerance."
}
```

#### Example Response (`HTTP 201 Created`):
```json
{
  "report_id": "400b119f-df61-44bb-b3c9-6c95867aa59b",
  "report_number": "VF-REP-20261101-400B119F",
  "document_id": "c8342634-6f59-4466-abed-0e6f37bdd16b",
  "title": "Forensic Examination — California Driving License Baseline",
  "file_size": 8487,
  "sha256_hash": "5e38496333781652f1462057d0eb009257e849931ad95932a3922f2cfba5f435",
  "created_at": "2026-11-01T11:22:43.109281Z"
}
```

#### Downloading Verified PDF (`GET /api/v1/reports/{id}/download`):
- Returns binary stream (`Content-Type: application/pdf`).
- Appends cryptographic response header:
  ```http
  X-Report-SHA256: 5e38496333781652f1462057d0eb009257e849931ad95932a3922f2cfba5f435
  ```

---

## 4. Standard Error Codes & Forensic Exceptions

| HTTP Status Code | Forensic Condition | Error Payload Example |
| :---: | :--- | :--- |
| **`400 Bad Request`** | Unsupported MIME type or corrupted image header. | `{"detail": "Unsupported file format. Supported: TIFF, PNG, JPEG, PDF."}` |
| **`401 Unauthorized`** | Missing, expired, or invalid JWT Bearer token. | `{"detail": "Could not validate credentials."}` |
| **`403 Forbidden`** | IDOR enforcement: Cross-analyst exhibit access attempted. | `{"detail": "Access forbidden: Document owned by another investigator."}` |
| **`404 Not Found`** | Unknown document ID or report ID. | `{"detail": "Exhibit not found."}` |
| **`409 Conflict`** | **TAMPERING ALARM:** Stored exhibit bytes failed SHA-256 check. | `{"detail": "TAMPERING_ALARM: Physical exhibit hash mismatch on disk."}` |
| **`429 Too Many Requests`** | Ingestion rate limiter exceeded (max 10 uploads/min). | `{"detail": "Rate limit exceeded. Please wait 60 seconds."}` |
