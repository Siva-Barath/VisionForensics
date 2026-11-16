# Final test report

13 November 2026. Tests were run against separate retained databases/files or clearly labeled synthetic pilot exhibits. Historical evidence was not used for destructive testing.

| Validation | Result | Evidence |
|---|---|---|
| Complete backend suite after UI implementation | **339 passed**, 127.48 seconds | `full_backend_tests.xml`, `full_backend_tests.log` |
| Fresh backend test database | `vf_test_a5221a043f65`, initially zero records | `test_environment.json`; schema restored and upgraded before tests |
| Earlier complete core gate | 339 passed before UI phase | Recorded in `feature_verification_matrix.md` |
| Frontend interaction/presentation suite | **8 passed** | `frontend_tests.log`, `frontend/tests/ui.test.tsx` |
| TypeScript + production build | PASS, Vite 6.4.6 | `frontend_build.log`, final `dist` assets checked against deployed responses |
| Frontend dependency advisory audit | 0 known vulnerabilities | `frontend_dependency_audit.json` |
| Isolated API workflows | **70 PASS, 0 FAIL** | `isolated_workflows.json`, `controlled_provenance.json` |
| Separate application process readback | PASS for PNG, JPEG and two-page PDF | `isolated_restart.json` |
| Actual HTTPS workflows and full container restart | **57 PASS** | `live_pilot_verification.json` |
| Browser-style Origin / cookie CSRF | **11 PASS** | `browser_origin_verification.json`; canonical https://localhost:8443 |
| Final deployed routes/assets/headers | 6 PASS | `final_verification.json` |
| Protected model/schema/benchmark files | **21 unchanged** | `baseline_manifest.json`, `final_verification.json` |
| Native development preview and backend | Healthy | `final_verification.json` |

The 57 live checks verify CA/hostname validation, frozen threshold/integrity, unavailable OCR status, production assets, registration/authentication, Secure HttpOnly cookies, PNG/JPEG/PDF upload, genuine 18-feature raw inference, per-page results, original hashes, preview dimensions, actual ELA maps, custody, comparison, actual PDF generation/hash/page count, cases/stats, logout, and retrieval after restarting PostgreSQL/backend/frontend without resetting volumes. Three synthetic exhibits and the generated PDF remain stored with provenance. The generated account's password was not retained.

Isolated negative tests include unauthorized and cross-user access, non-admin restrictions, inactive accounts, refresh/logout behavior, ledger mutation prevention, missing/tampered original and heatmap rejection, persistence rollback, corrupt PDF failure, nonfinite features, model/schema mismatch, unavailable OCR, case ownership and exact counts beyond a single list page.

Important test-history disclosures:

- One post-UI run inside the restricted Windows sandbox had 328 passes and 11 inference failures because scikit-learn worker resources returned Access denied. No model/threshold changes were made; the complete isolated suite passed when required resources were allowed.
- Initial collection failures exposed unregistered legacy fake evaluation/fusion/report APIs. They now raise explicit unsupported errors and their guard tests pass. They are not counted as implemented application features.
- Some fixture expectations were invalid for their raster inputs or existing weight policy. Corrections and limitations are documented in `change_log.md` and `final_forensic_validation.md`.
- React's MemoryRouter SSR compatibility test emits a useLayoutEffect warning; this app is a client-rendered SPA. The test passes; no SSR support is claimed.

No new held-out accuracy evaluation, model retraining, benchmark rewrite, comprehensive browser visual audit, load/concurrency certification or independent penetration test was performed. No unverified capability is promoted to PASS in the feature matrix.

Repeatable commands and the demonstration sequence are in [deployment_and_demo_guide.md](deployment_and_demo_guide.md).
