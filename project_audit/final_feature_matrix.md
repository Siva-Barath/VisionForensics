# Final feature verification matrix

13 November 2026. PASS is limited to the tested behavior described below. PARTIAL is an explicit product limitation, not a concealed success. This supersedes the pre-UI verification matrix for final status.

| Feature | Status | Verified behavior / boundary |
|---|---|---|
| 1. Registration/login/logout | PASS | Real isolated and HTTPS account flow, cookie/session behavior; no password resets |
| 2. Case creation | PASS | Real title, notes, priority and lead; transaction and ownership; case cards and exact counts |
| 3. Authentic-document processing | PARTIAL | Historical specimen unit workflow and clean synthetic controls; no new real-world authenticity validation |
| 4. Modified-document processing | PASS | Controlled edit passes actual processing and integrity workflow; not a new detection-accuracy claim |
| 5. PDF upload | PASS | Actual rasterization, limits, per-page inference and failure behavior |
| 6. PNG/JPEG upload | PASS | Live analysis, snapshots, previews and original bytes |
| 7. Invalid file rejection | PASS | Authenticated content/magic validation |
| 8. Oversized rejection | PASS | Bounded reads and configured size controls |
| 9. Frozen ML inference | PASS | Hash/schema/class validation, 18 inputs, T=.40, approved raw-result separation |
| 10. ELA | PASS | Actual recompression metrics/map artifacts; artifact/original integrity; real UI overlay |
| 11. Image quality | PASS | Actual supported quality metrics retained; no capture-quality/authenticity equivalence |
| 12. Copy-move | PASS | Actual geometry/pipeline/summary/regions under tested fixtures; repeated-pattern limits |
| 13. OCR/text | PARTIAL | Honest unavailable/failed state and adapter guards pass; deployed extraction unavailable |
| 14. Metadata | PARTIAL | Real EXIF/PDF extraction; comprehensive timestamp/semantic checks absent |
| 15. JPEG compression | PASS | DQT estimate and applicability; no exact encoder recovery claim |
| 16. Multi-page analysis | PASS | Real per-page vectors/results, navigation, dimensions, bounds and persistence; heuristic synthesis disclosed |
| 17. Region inspection | PARTIAL | API geometry and DOM click/page/zoom tests pass; browser visual/accessibility QA unavailable |
| 18. Document comparison | PASS | Actual alignment/difference API and live HTTPS workflow; protected parents; view retained |
| 19. PDF reports | PASS | Actual generation/download/hash/page count/version and restart; full case narrative integration partial |
| 20. SHA-256 integrity | PASS | Original ingestion anchor; missing/changed original and ELA artifact fail-closed tests |
| 21. Custody | PASS | Genuine events and append-only database protections; transactional ingestion |
| 22. Security logs | PASS | Real events, ledger negative tests and runtime grants |
| 23. Role restrictions | PASS | Admin/analyst/inactive tests; administrator UI with protected actions and self-status guard |
| 24. Ownership | PASS | Case/exhibit/comparison access boundaries and visibility before document pagination |
| 25. Restart/persistence | PASS | Separate-process readback and live database/backend/frontend restart: raw vectors, originals, maps, report preserved |
| Dashboard / analytics | PASS | Real scoped totals, runtime health, disclosed recent-list/sample limits |
| User management | PASS | Existing admin endpoints integrated; DOM test uses controlled mocked transport, backend role tests use isolated DB |
| Signature authenticity | NOT IMPLEMENTED | Appearance analysis is separate; no validated reference verification |
| Legacy benchmark service / Bayesian fusion / legacy archive scaffold | NOT IMPLEMENTED | Fabricated outputs blocked; registered inference/RiskStage/PDF routes unaffected |
| Browser visual / accessibility acceptance | PARTIAL | Responsive implementation and DOM checks delivered; no screenshot/screen-reader/cross-browser sign-off |

Evidence: 339 backend tests; 8 frontend tests; 70 isolated workflow checks; 57 actual HTTPS/restart checks; 11 browser-origin/CSRF checks; 6 final routes/assets/header checks; 21 protected files unchanged. These functional checks do not constitute accuracy calibration, legal proof or complete operational/security certification. See [test report](final_test_report.md), [forensic validation](final_forensic_validation.md) and [limitations](known_limitations.md).
