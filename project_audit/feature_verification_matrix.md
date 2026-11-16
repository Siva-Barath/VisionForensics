# Core verification gate before UI redesign

13 November 2026. Full isolated backend suite: **339 passed**, no failures/skips or collection errors. XML: `full_backend_tests.xml`. Controlled ASGI/API checks: **70 passed** in `isolated_workflows.json`. A second Python application process retrieved all three controlled exhibits, full per-page results, original SHA-256 matches and real ELA maps (`isolated_restart.json`). Tests used isolated databases and retained generated evidence. Frozen artifacts and 21 protected artifact/Phase4/Phase9 files match the baseline.

Legacy evaluation/readiness, Bayesian fusion and mock report/archive entrypoints are explicitly NOT IMPLEMENTED and guarded. Passing their boundary tests establishes that they reject fabricated output, not that those optional features work. Registered three-track assessment and forensic PDF workflows are separate and verified.

| Requested workflow | Result | Evidence / limit |
|---|---|---|
| 1 Login/logout | PASS | Session, cookie-only access, post-logout rejection and security suite |
| 2 New case | PASS | Case API, ownership, intake title/notes/priority persistence, exact totals |
| 3 Authentic document upload | PARTIAL | Historical training specimen workflow plus generated clean control; no new real-world accuracy claim |
| 4 Modified upload | PASS | Provenance-labeled controlled pixel edit; functional processing, not accuracy certification |
| 5 PDF upload | PASS | Controlled PDFs and limits tests |
| 6 PNG/JPEG | PASS | Full analysis/readback/original verification |
| 7 Invalid file rejection | PASS | Magic/content rejection under authenticated access |
| 8 Oversized rejection | PASS | Bounded-read and >20MB checks |
| 9 ML inference | PASS | Frozen hash/schema/classes/T=.40, raw result separation, all 18 genuine inputs |
| 10 ELA | PASS | Real recompression error maps, hashes, dimensions, artifact access |
| 11 Quality | PASS | Unit/pipeline measurements and corrected channel handling; capture quality is not authenticity |
| 12 Copy-move | PASS | Geometry/unit and pipeline execution; repetitive-pattern limitations remain |
| 13 OCR/text | PARTIAL | Availability/failure handling verified; real PaddleOCR execution unavailable in current native runtime/container |
| 14 Metadata | PARTIAL | Actual EXIF/PDF extraction; comprehensive timestamp/semantic verification not implemented |
| 15 JPEG compression | PASS | DQT estimates and non-JPEG qualification tests; estimates not exact encoder recovery |
| 16 Multi-page analysis | PASS | Per-page input/results, navigation APIs, bounds, snapshots; max-page selection labeled heuristic |
| 17 Region inspection | PARTIAL | Server geometry tested; browser click/visual QA pending frontend phase |
| 18 Comparison | PASS | Real SSIM/differences/alignment and dual-parent authorization tests |
| 19 PDF reports | PASS | Actual PDF generation/download/hash, authoritative score/version/page count |
| 20 SHA-256 | PASS | Immutable ingestion anchor, missing/tampered original and altered map rejection |
| 21 Custody | PASS | Genuine events, append-only PostgreSQL guards, transactional rollback |
| 22 Security logs | PASS | Actual events and least-privilege/trigger tests |
| 23 Role restrictions | PASS | Admin/analyst/inactive and negative security checks |
| 24 Ownership | PASS | Case/exhibit/dual-document boundaries; filtering precedes pagination |
| 25 Restart/persistence | PARTIAL | Separate-process readback and backup restore pass; full deployed container restart verification pending |

Critical ingestion, inference, persistence, evidence-integrity and authorization gates pass. Optional unavailable functions remain visibly unavailable. Phase six may proceed with those explicit limitations; no fake module success or fabricated historical backfill is permitted. Final deployment/browser checks remain outstanding.
