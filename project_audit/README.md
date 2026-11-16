# VisionForensics engineering handover

13 November 2026. Open the application at **https://localhost:8443**. Development preview: **http://localhost:5173**. Accounts/data are separate between these environments. Use the established pilot CA trust process.

Start with the [deployment and demonstration guide](deployment_and_demo_guide.md).

- [Final architecture](final_architecture.md)
- [Final feature matrix](final_feature_matrix.md)
- [Frozen ML validation](final_ml_validation.md)
- [Forensic validation](final_forensic_validation.md)
- [Security report](final_security_report.md)
- [UI/UX report](final_ui_ux_report.md)
- [Test report](final_test_report.md)
- [Known limitations](known_limitations.md)
- [Change log](change_log.md) and [source inventory](source_change_inventory.md)

Verified: 339 backend tests, 8 frontend tests, 70 isolated workflow checks, 57 actual HTTPS/restart checks, 11 browser-origin/CSRF checks, 6 final deployed page/assets/header checks, and 21 protected files unchanged. TypeScript/production build pass; npm audit reports zero known frontend vulnerabilities at verification time.

OCR is unavailable in the deployed container. Signature authenticity verification is not implemented. Browser visual/accessibility acceptance and broader operational/security validation remain outstanding. This is a verified controlled pilot, not a claim of universal accuracy, guaranteed authenticity or independent industry certification.

The ten initial audit reports and `baseline_manifest.json` preserve the original findings. Final reports supersede their open-item status. Test databases, controlled files, reports and backups are retained for review. One-time editing scripts named `finish_ui.py` and `finish_workspace_ui.py` document source transformations; do not rerun them. Verification scripts have the scopes documented in the deployment guide.
