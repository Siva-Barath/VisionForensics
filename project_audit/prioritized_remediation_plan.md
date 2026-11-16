# Remediation order and phase gates

The detailed findings and source references are in `executive_audit.md`. This plan does not authorize changes to frozen governance.

1. Preserve `baseline_manifest.json`. All ten phase-one reports must exist before source edits. No historical evaluator or training script is run.
2. ML and algorithm source audits are in their reports. Add negative tests for tampered model/schema, missing original, persistence failure, corrupt PDF rendering, unavailable OCR and unknown risk explanations.
3. Safe P0 repairs: hash before deserialization; require authentication; remove URL credentials while retaining functional asset access; fail closed for missing original; surface failed persistence. Never delete orphaned exhibit bytes.
4. Back up PostgreSQL and relevant source before additive snapshot/transaction migrations. List/verify backup contents and hash. Test on an isolated database first. Do not invent historical snapshots or rewrite ledgers.
5. P0-06 governance decision: current multi-page/JPEG gates contradict a raw T=.40 decision. Preserve approved unified risk definitions and frozen threshold. Any decision-policy change requires approval and a new version; separate raw outputs from document-level heuristic presentation.
6. P1: stop inference on generated PDF error pages; bound raster dimensions; close native resources; truthful OCR capability; exact page mapping. Do not change frozen feature extraction or tune thresholds against locked data.
7. P2: correct report score/version/region contracts; actual case submission and ownership; server-side counts and module execution status; user-management UI backed by existing admin authorization.
8. P3: remove sensitive logging, real readiness/health, resource/concurrency controls, verify isolated localhost HTTPS, restart/backup restore.
9. Run the directive's 25 controlled workflows with known provenance in isolated storage/database. Record PASS/PARTIAL/FAIL/NOT IMPLEMENTED. No feature is verified because a card exists.
10. Only after critical verification passes, begin the complete results/UI redesign. Preserve all forensic details and original/derived distinction.
11. Final handover reports must state measured results and unexecuted/failed checks. Do not issue a completed final release report while gates remain open.

No routine technical decision is delegated back to the user. Approval is needed only for an actual conflict with model governance, security, evidence integrity or historical results. Current material conflict: raw-vs-document-level classification semantics in P0-06.
