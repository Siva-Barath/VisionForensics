# API integration audit

13 November 2026. Registered routers from `backend/app/api/__init__.py`; all paths below start `/api/v1`. Exact declarations/file/line/function inventory is in `baseline_manifest.json`.

| API | Frontend consumer | Storage/service | Concerns |
|---|---|---|---|
| POST /auth/register,/auth/login,/auth/refresh,/auth/logout; GET /auth/me | AuthContext/Login/Register/Sidebar | UserRepository, JWT, Argon2, refresh_tokens | Dev anonymous fallback; URL-token paths; read-only audit did not execute sessions |
| POST /upload | NewInvestigationPage | DocumentService/pipeline/PostgreSQL | Case inputs not submitted; generic success despite persistence errors |
| GET /documents | Home/Cases/Analytics | DocumentRepository/current ownership query | Client limits 50/100 produce incomplete counts |
| GET /documents/{id}/analysis | InvestigationDashboardPage | Cache/reconstructed AnalysisContext | Restart loss, missing-original verification bypass, raw/unified tier conflation |
| GET /documents/{id}/image?page=N | DocumentViewer | Processed/page paths; PDF fallback | Derived preview labeled exhibit; query token; no dedicated original route |
| GET /documents/{id}/custody-logs | Custody tab | AuditService | Verify ledger runtime behavior on isolated DB |
| POST /comparison; GET /comparison/{id}; GET artifacts/{type} | Comparison page/dual viewer | ComparisonService/repository | Dual-document authorization present; fallback alignment caveats; URL token |
| POST /reports; GET /reports; GET /reports/{id}; GET download | Reports/GenerateReportModal | ReportService/FPDF/repository | Score/version/fallback geometry bugs; query-token downloads |
| POST/GET /admin/users; PUT /admin/users/{id}/status; GET /admin/audit-logs | No dedicated user-management UI | Admin auth routes/repositories | Backend role checks present; frontend feature absent |
| GET /health | Home; partial use only | SELECT 1/filesystem/model/OCR imports | Hardcoded model hash/status; expensive imports in async request; reports healthy despite subsystem errors |

`api/endpoints/reports.py` contains a mock `/generate` declaration that is not registered. Case-specific CRUD, server aggregate analytics, original retrieval and full module execution contracts are absent.

Frontend Axios base URL is `/api/v1`, refresh mutex retries authenticated requests. Asset helper URLs carry Bearer access tokens in query parameters. Vite proxies to localhost:8000; configured Nginx uses Docker backend:8000 and HTTPS. Frontend timeout 60s vs Nginx proxy read 120s; CPU/native work is synchronous inside async routes. Generic Axios errors hide proxy vs application failure. get_context turns all database errors into not found.

API presence is only partial verification. Production runtime schemas, error contracts, ownership, large files, timeout/recovery, restart persistence and report readback require isolated workflow tests. No mutation was performed in phase one.
