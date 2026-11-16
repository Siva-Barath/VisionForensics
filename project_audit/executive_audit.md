# Executive engineering audit

13 November 2026, Asia/Calcutta. This investigation treats historical reports as claims, not proof. Only audit deliverables were written in phase one; source, model artifacts, database rows and benchmarks were not modified. Earlier UI and service startup work predates this directive.

The platform contains substantial real image-forensic, inference, PostgreSQL, comparison, PDF reporting and authorization implementations. It is not currently defensible to describe every feature as verified or industry ready.

| Priority / ID | Finding | Evidence | Required outcome |
|---|---|---|---|
| P0-01 | No enforced model/schema digest before deserialization | `backend/app/services/ml_inference/inference_service.py:load_artifacts` | Check expected bytes before joblib; exact schema/model input names and classes |
| P0-02 | Analysis changes after restart | `document_service.py:get_context`, `models/analysis.py` | Persist versioned full snapshot, retain per-page/raw ML/metadata/quality/execution evidence |
| P0-03 | Upload can succeed after persistence failure; partial commits | `document_service.py:_persist_to_database`, `document_repository.py`, `audit_service.py` | Surface failure, atomic transaction, no successful cache entry before commit |
| P0-04 | Missing original bypasses integrity verification | `api/documents.py:get_document_analysis/get_document_image` | Fail closed; protected original retrieval; never log missing original as verified |
| P0-05 | Development anonymous fallback and URL tokens | `core/auth.py`, `frontend/src/services/api.ts` | Require auth, preserve authenticated assets without URL credentials |
| P0-06 | Heuristic gates overwrite raw ML decisions | `ml_inference_stage.py`, `risk_stage.py` | Governance decision: preserve T=.40 raw outputs separately from approved unified policy |
| P1-01 | Failed PDF pages become synthetic evidence graphics | `services/preprocessing/pdf_converter.py` | No inference on error graphics; bounded rendering and native resource cleanup |
| P1-02 | OCR import availability selects mock implementations | `ocr_stage.py`, `ocr/engines/easyocr_engine.py`, `tesseract_engine.py` | Unsupported engines unavailable; only actual extraction produces results |
| P2-01 | Reports use incorrect score key, fixed version, invalid fallback region fields | `services/report_service.py` | Report and persisted analysis agree before/after restart |
| P2-02 | Case title/notes/priority discarded | `NewInvestigationPage.tsx`, `api/upload.py`, `models/case.py` | Actual case creation, ownership, API submission, true case counts |
| P2-03 | UI service statuses and some evaluation metrics hardcoded | `HomePage.tsx`, `SettingsPage.tsx`, `AnalyticsPage.tsx`, `evaluation/metrics_calculator.py` | Actual statuses/counts; no fabricated performance |
| P3-01 | Current preview differs from required pilot deployment | Compose/Nginx/settings and prior startup checks | Verify localhost HTTPS deployment, health, recovery, secrets handling |

Positive verification: frozen model SHA-256 matches the directive; model input names/order match the actual 18-feature schema. Read-only PostgreSQL catalog checks found SELECT/INSERT-only runtime grants on both ledgers and enabled triggers blocking UPDATE/DELETE. Those checks do not establish end-to-end correctness or complete security.

Scope: targeted source inspection, AST/route inventory, model inspection, read-only database catalog/count queries. No full workflow suite, destructive tests, retraining or benchmark reevaluation ran in this phase. See the other nine reports and `baseline_manifest.json` for the inspection baseline. Some secondary implementations remain only structurally inventoried; no claim of line-by-line exhaustive correctness review is made.

Immediate plan: safe P0/P1 negative regressions and fixes; verified backup and isolated testing before migrations; explicit governance decision for P0-06; feature verification; only then further cosmetic redesign. Critical gates remain open.
