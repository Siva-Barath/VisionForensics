# Source change inventory

The baseline was captured after initial UI polish and before directive remediation. Digests are in final_verification.json. No Git repository exists.

## Changed baseline files

- `backend/app/__init__.py`
- `backend/app/api/auth.py`
- `backend/app/api/documents.py`
- `backend/app/api/health.py`
- `backend/app/api/upload.py`
- `backend/app/api/__init__.py`
- `backend/app/core/auth.py`
- `backend/app/database/session.py`
- `backend/app/evaluation/deployment_validator.py`
- `backend/app/evaluation/evaluation_runner.py`
- `backend/app/ml/feature_vector.py`
- `backend/app/models/analysis.py`
- `backend/app/pipeline/artifact.py`
- `backend/app/pipeline/context.py`
- `backend/app/pipeline/stages/explainability_stage.py`
- `backend/app/pipeline/stages/ml_inference_stage.py`
- `backend/app/pipeline/stages/preprocessing_stage.py`
- `backend/app/repositories/document_repository.py`
- `backend/app/schemas/analysis.py`
- `backend/app/services/audit_service.py`
- `backend/app/services/document_service.py`
- `backend/app/services/report_service.py`
- `backend/app/services/evidence_fusion/fusion_service.py`
- `backend/app/services/forensics/copy_move_region_analyzer.py`
- `backend/app/services/forensics/forgery_service.py`
- `backend/app/services/forensics/image_artifact_detector.py`
- `backend/app/services/forensics/logo_region_analyzer.py`
- `backend/app/services/forensics/signature_region_analyzer.py`
- `backend/app/services/forensics/logo_analyzers/base_logo_analyzer.py`
- `backend/app/services/ml_inference/inference_service.py`
- `backend/app/services/ml_inference/models.py`
- `backend/app/services/ocr/ocr_service.py`
- `backend/app/services/ocr/postprocessor.py`
- `backend/app/services/ocr/engines/easyocr_engine.py`
- `backend/app/services/ocr/engines/paddleocr_engine.py`
- `backend/app/services/ocr/engines/tesseract_engine.py`
- `backend/app/services/preprocessing/pdf_converter.py`
- `backend/app/services/preprocessing/operations/base_operation.py`
- `backend/app/services/preprocessing/operations/contrast.py`
- `backend/app/services/preprocessing/operations/normalize.py`
- `backend/app/services/report_generation/pdf_generator.py`
- `backend/app/services/report_generation/report_service.py`
- `backend/app/utils/file_validator.py`
- `backend/tests/test_api.py`
- `backend/tests/test_deskew.py`
- `backend/tests/test_evaluation.py`
- `backend/tests/test_evidence_fusion.py`
- `backend/tests/test_feature_extractor.py`
- `backend/tests/test_forensics_framework.py`
- `backend/tests/test_image_forensics.py`
- `backend/tests/test_logo_forensics.py`
- `backend/tests/test_milestone_7b.py`
- `backend/tests/test_milestone_7b_remediation.py`
- `backend/tests/test_paddleocr_engine.py`
- `backend/tests/test_phase5_e2e.py`
- `backend/tests/test_preprocessing.py`
- `backend/tests/test_report_generation.py`
- `frontend/src/features/comparison/pages/DocumentComparisonPage.tsx`
- `frontend/src/features/explainability/components/DocumentViewer.tsx`
- `frontend/src/features/explainability/pages/InvestigationDashboardPage.tsx`
- `frontend/src/pages/AnalyticsPage.tsx`
- `frontend/src/pages/CasesPage.tsx`
- `frontend/src/pages/HomePage.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/NewInvestigationPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/types/analysis.ts`
- `frontend/src/types/index.ts`

## New implementation and harness files

- `backend/.dockerignore`
- `backend/alembic/versions/a61000000005_005_analysis_context_snapshot.py`
- `backend/app/api/cases.py`
- `backend/app/core/exhibit_integrity.py`
- `backend/app/services/case_service.py`
- `backend/app/services/context_snapshot.py`
- `backend/app/services/module_status.py`
- `backend/tests/conftest.py`
- `backend/tests/test_engine_stabilization.py`
- `frontend/.dockerignore`
- `frontend/scripts/run-tests.mjs`
- `frontend/security-headers.conf`
- `frontend/src/components/ServiceHealthPanel.tsx`
- `frontend/src/components/UserManagement.tsx`
- `frontend/src/features/explainability/components/ForensicModules.tsx`
- `frontend/src/utils/analysisPresentation.ts`
- `frontend/tests/ui.test.tsx`
- `scripts/run_isolated_backend_tests.py`

## Other edited delivery files

- `frontend/package.json`, `frontend/package-lock.json`: compatible security updates and test/runtime scripts.
- `frontend/index.html`, `frontend/Dockerfile`, `frontend/nginx.pilot.conf`: CSP-compatible UI, production headers and delivery.
- `frontend/src/index.css`, `frontend/tailwind.config.js`, layouts/navigation/auth/UI components and `frontend/public/favicon.svg`: initial UI work predating baseline; hashes do not imply unchanged original UI.

See change_log.md for root causes, scope and validation; final reports distinguish unavailable capabilities.
