# Engineering change log

13 November 2026. No Git metadata exists at the workspace root. `baseline_manifest.json` preserves the directive's initial source hashes, protected file hashes and route inventory. `final_verification.json` records before/after digests for changed baseline files. `source_change_inventory.md` lists them; new source files are separately inventoried there. Audit reports remain the read-only initial findings.

## P0: Integrity, authentication and persistence

| Root cause | Change and scope | Validation |
|---|---|---|
| Executable model loading trusted an arbitrary path before digest verification | Verify frozen model/schema bytes, exact ordered names/count/classes; deserialize verified byte stream | Mismatch/valid artifact tests, live health/inference, all protected hashes unchanged |
| Development fallback bypassed authentication; asset URLs carried tokens | Require active authenticated users everywhere, remove query-token auth, HttpOnly access cookie, cookie-backed asset URLs | Auth/role/ownership/session tests; HTTPS Secure HttpOnly cookie and logout checks |
| Missing exhibit silently passed; mutable document hash was sole anchor | Original guard uses earliest ingestion ledger digest; 410 missing and 409 unverifiable/tampered; protected original endpoint | Missing/mutated original/digest tests on disposable data; live original SHA retrieval |
| Ingestion performed multiple commits and swallowed failure | Repository flush option and custody commit control; one database commit for case/document/pages/analysis/ingestion event; persistence errors fail without cache success | Transaction rollback and failure tests; actual persisted upload/restart checks |
| Database reconstruction lost forensic fields | Add nullable versioned JSON snapshot, typed restore, reject NaN; no historical backfill | Isolated backup restore/migration, full vector/per-page/metadata restoration; actual process/container restart |
| Raw model decisions were overwritten by document heuristics | User-approved separate raw result, source page and selection method; preserve existing document policy and thresholds | Raw/qualified result tests; UI presentation and live persistence checks |
| Startup/SQL logs could expose secrets | Remove DB URL startup output and SQL echo; redacted verification logs | Source review and retained output checks |

## P1: Forensic processing and honest capability boundaries

- PDF conversion now returns real bounded rasters or explicit failure, closes resources and never sends generated error graphics into inference. PDF preprocessing aborts on render failure; content validation rejects empty/corrupt PDFs.
- EasyOCR/Tesseract mocks are unavailable. Paddle initialization/extraction failures propagate; only actual OCR results can count as extraction success. No frozen NumPy/model upgrade was made to hide the native dependency incompatibility.
- Detector telemetry records completed/partial/failed/prerequisite-unavailable outcomes. Internal copy/image failures issue warnings rather than empty apparent success. Signature authenticity is explicitly unimplemented.
- Real ELA maps are stored once with document/job/page provenance and artifact digest; the protected heatmap endpoint verifies original and derived bytes. Scalar measurements and detector thresholds were not tuned.
- Stored dimensions now use actual derived page rasters for coordinate mapping. Signature/logo bounding-box inputs and integer crops are normalized. Logo geometry determines background polarity instead of measuring the page rectangle.
- Contrast handles a single-channel 3D input; normalization and base-operation warnings propagate. The canonical feature export separates supplemental fusion/outcome values without changing frozen 18-feature inputs.
- UNKNOWN explanations no longer claim low-risk authenticity. Unregistered legacy benchmark/fusion/report scaffolding that fabricated scores/custody/archive results now raises unsupported errors. Actual registered risk synthesis and PDF generation remain active.

Validation: meaningful algorithm/negative tests and the complete 339-test suite; actual PNG/JPEG/PDF controls; ELA/hash readback and restart. False-positive/negative and runtime limits are recorded in the forensic and limitation reports.

## P2: API, cases and reports

- Document authorization is applied in SQL before pagination. Case list/detail/create and exact authorization-scoped workspace totals use existing case/document models and roles.
- Upload case details are persisted inside the ingestion transaction. Case notes/priority are no longer discarded. UI counts are actual database aggregates rather than a 50/100-row sample.
- Actual ReportService uses the right composite key, analysis version and normalized region fallback, separates raw ML in report data, and counts real generated PDF pages. Existing report hash verification remains.
- Health probes real database/model load state and clearly distinguishes optional OCR availability from successful execution. Required failures produce a degraded/503 response.

Validation: isolated case/count/ownership/report tests, 70 controlled API checks, 57 actual HTTPS and restart checks. Full case narrative integration, sparse report pagination and broad concurrency remain explicit limitations.

## UI and deployment

- Shared navy/cyan visual system, typography/spacing, cards/badges, responsive sidebar/topbar, authentication shell, forms, upload flow, focus/skip navigation and password visibility. These first cosmetic edits occurred before the directive's read-only baseline and are described here even where their hashes already appear in that baseline.
- Real health panels replace fabricated capability/TLS status. Raw ML and heuristic composite are separate. Feature values, neutral UNKNOWN state, nine execution-driven module cards, true ELA overlay, original download and advanced forensic tabs preserve examiner access.
- Cases show real case details and recent exhibits; analytics separates exact totals from the disclosed recent format sample; comparison adds filename suggestions; Settings includes correct governance digest and actual admin account management.
- Frontend dependency upgrades fix observed advisories (Vite 6, React Router 7 with React 18 retained, compatible transitive patches). Final npm audit: zero known vulnerabilities. Node >=20.19 is documented. Eight meaningful frontend tests were added.
- Docker build contexts exclude environment/data/test caches and local dependencies. Existing persistent pilot volumes and localhost-only mappings are preserved.
- Additive migration used existing owner only after backup/isolated testing; no ownership/runtime grant changes. A migration helper container avoids the existing backend fixed-IP collision.
- Deployed Nginx cache-setting locations now include security headers; a live header check proved the original inheritance defect. External font links were removed for self-origin CSP/offline compatibility.
- Native preview/backend restarted with the final source, and final production UI bytes verified over trusted HTTPS. All three pilot containers are healthy.

## Test repairs and evidence handling

The test harness now refuses database integration tests without a matching `vf_test_*` target. Each full run creates a fresh schema-only database and isolated file directories. Per-test limiter state resets between independent scenarios; enforcement within scenarios remains intact. Unrelated auto-loaded external pytest plugins were disabled because of local DLL policy; pytest-asyncio is explicitly loaded.

Tests now authenticate explicitly rather than relying on development bypass. The trusted-proxy fixture respects declared hop trust. Canonical/supplemental feature assertions follow the preserved input contract. Raster-circle tolerance, resolvable texture stripes, a genuinely unshadowed thin-line page and controlled maximum-deskew-guard fixtures replace invalid assumptions. The fixed risk weights were preserved; expectations use their actual total of 115. Native Paddle unit tests inject the adapter dependency, with actual runtime unavailability separately recorded. Zero-width separator/BOM cleaning retains meaningful joiners. None of these changes tunes frozen weights, threshold, historical benchmarks or production risk rules to obtain a pass.

One restricted post-UI test run failed scikit-learn worker creation. The same complete suite passed with required resources permitted: 339 passed. Test artifacts are retained. New synthetic files, controlled databases/accounts and reports are not deleted or relabeled as historical evidence. No existing account password was changed.

See `final_test_report.md` for exact counts and `backups/` for archive hashes. No destructive live ledger tests, historical benchmark rewrites or model retraining occurred.

Final browser-origin verification: 11 checks passed for https://localhost:8443, including cookie refresh/logout and hostile-origin rejection. The canonical browser link uses the existing localhost allowlist; no CSRF trust policy was widened.
