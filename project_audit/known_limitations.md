# Known limitations

13 November 2026. The delivered state is a tested local controlled pilot. “Industry ready” would additionally require operational, browser, security, scale and validation acceptance beyond this session.

1. OCR is unavailable in the deployed container; native PaddleX/Faiss is incompatible with the frozen environment. EasyOCR/Tesseract adapters are unimplemented and explicitly unavailable. No text authenticity or comprehensive field verification is claimed.
2. Signature appearance/region analysis is heuristic. There is no validated reference-backed signature authenticity or signer identity verification.
3. Metadata extraction works, but comprehensive timestamp/semantic consistency is partial. Missing metadata and editing-tool markers are not proof of forgery.
4. Historical analyses lack full snapshots. Their raw vectors, per-page or module execution values may be unavailable; no invented backfill was made. Missing historical originals return explicit errors.
5. JPEG and maximum-page qualification remain existing heuristics under preserved governance. Composite scores are not calibrated probabilities. No new benchmark, calibration or real-world accuracy study was performed.
6. Preprocessing can influence forensic measurements. Full original-to-derived transformation provenance is not retained. Extreme skew, glare/perspective, highly compressed inputs and repetitive patterns remain difficult.
7. Comparison alignment/resize fallback and illumination differences affect SSIM and region interpretation. Similarity does not prove authenticity.
8. UI lists show recent windows; cases/exhibit search and format analytics disclose 100-item limits. Workspace totals are exact and authorization scoped. Report listing still applies its visibility filter after the repository page, so an analyst may receive a sparse page. There is no general case editing/assignment workflow.
9. Actual PDFs contain exhibit and case ID, analysis, notes, limitations, hashes and custody. Full case narrative/notes integration in the PDF template remains partial.
10. Eight DOM/presentation tests and deployed asset verification passed. No connected browser was available for screenshot, responsive-layout, screen-reader, cross-browser or complete manual UX acceptance. No visual QA claim is inferred from DOM tests.
11. Browser bearer tokens remain in localStorage in the existing authentication design. Cookie protection for assets does not remove XSS token exposure. CSP still permits inline styles. Existing credential/certificate governance requires review before wider deployment.
12. Single-worker process cache/rate limiting and synchronous CPU work are unsuitable for unreviewed horizontal scale. Reanalysis version allocation and concurrent ingestion need broader load/concurrency work. Filesystem/database writes cannot commit as one atomic distributed transaction; retained orphan files may need controlled recovery.
13. Zero known npm advisories is not a complete supply-chain/security certification. Backend/container scanning and independent penetration testing remain outstanding. The existing internal frontend health probe skips CA validation; external delivery checks verified the CA and hostname normally.
14. The native backup was restored and used for isolated testing. The pilot backup archive/hash/listing was verified, but a full independent pilot disaster-recovery drill was not completed. No exhaustive rehash of every historical original on disk was performed.
15. Legacy experimental evaluation metrics, Bayesian fusion and legacy archive/report scaffolding are NOT IMPLEMENTED. Fabricated results are blocked explicitly. The registered RiskStage and actual PDF/SSIM routes are separate, functional implementations.
16. Use canonical browser URLs https://localhost:8443 and http://localhost:5173; numeric loopback browser origins are outside the existing allowlist. The browser preview and pilot use separate databases/accounts. A previous native demo credential may not authenticate to the pilot; use the normal account flow. No password reset or credential disclosure was performed.

Retained controlled databases/accounts/files are review artifacts. They were not silently deleted or mixed into historical benchmark claims. See the feature and test reports for exact PASS/PARTIAL boundaries.
