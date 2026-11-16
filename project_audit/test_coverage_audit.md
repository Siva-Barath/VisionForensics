# Test coverage audit

13 November 2026. Test existence does not prove execution. No full or mutating test suite ran during read-only phase one.

27 backend test files (~6,448 lines) cover preprocessing/deskew, features/dataset, image/copy-move/logo/signature detectors, OCR/PaddleOCR/layout/classification, ML service/stage, evidence fusion, evaluation/report scaffolding, phase5 E2E, milestone7B auth/security/remediation, 7C PDF, 7D comparison, 7E reports, phase8R remediation.

Frontend package declares `build: tsc && vite build` but no test script/testing framework. Lint command references eslint without a declared eslint dependency; no successful frontend lint run is assumed. Earlier frontend build success predates this directive.

Safety/validity concerns:

- Several milestone tests use configured SessionLocal and commit users/documents/audits, or tamper files/ledgers. Running against live database risks historical evidence. Isolate DB and storage first.
- test_api assumes anonymous development auth. HealthResponse supplies version=1.0.0 by default; that field is supported.
- test_milestone_7c_pdf explicitly expects generated corrupt-page placeholders; that expectation conflicts with truthful forensic processing.
- test_phase8r has repository-root relative paths. Test working directory matters.
- Evaluation/report framework tests can assert fixed mock metrics; they do not establish frozen-model accuracy or live integration.
- No unified database isolation fixture is present. No complete browser/accessibility or deploy/restart suite is established.

Read-only checks completed: exact model/schema digests, model structure/names/classes/feature importance; AST/routes/source inventory; PostgreSQL catalogs/counts/grants/triggers. Dataset path exists. No fresh held-out accuracy, OCR execution, Docker health, report export, browser QA, restart equality or backup restore is claimed.

Next verification: deterministic negative unit tests for P0 defects; isolated PostgreSQL and storage harness; focused regressions; complete backend suite with precise pass/fail/skip/dependency reporting; frontend build and meaningful UI/API contract tests; controlled authentic/modified PNG/JPEG/multi-page PDF with provenance; authorization/ownership/integrity; comparison/report readback; actual restart and restore. Record PASS, PARTIAL, FAIL or NOT IMPLEMENTED for all 25 requested workflows. Critical failures block cosmetic phase six.
