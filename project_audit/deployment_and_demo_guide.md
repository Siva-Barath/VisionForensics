# Deployment and demonstration guide

13 November 2026. The canonical browser URL is **https://localhost:8443**. The development preview is **http://localhost:5173**. Use localhost in the browser because the existing allowed-origin policy names localhost; the numeric loopback address is used for separate direct API checks. They use separate databases; accounts and uploaded exhibits do not automatically transfer between them.

Use an existing account for the chosen environment or register through its normal interface. The email shortcut fills only an email, never a password. No account password was changed. Controlled validation accounts/exhibits are labeled and retained; the latest generated validation account password was intentionally not retained.

The pilot uses the existing private CA. See `ca/README_CA_GOVERNANCE.md` for the established trust process. Verify the certificate through that process rather than bypassing browser warnings. Automated checks used `ca/pilot_ca.crt` with hostname verification for both loopback hostnames. Eleven additional canonical browser-origin checks verified cookie refresh/logout and rejected cross-origin requests; the trust policy was not broadened. Never share the CA/private server keys or commit environment secrets.

## Start the existing pilot

From `D:\Forgery Detection ML`, with Docker Desktop running:

```powershell
docker compose --env-file .env.pilot -f docker-compose.pilot.yml up -d
```

Only frontend ports 8080/8443 bind to localhost. HTTP redirects to HTTPS. Backend and database ports remain internal. Persistent volumes hold PostgreSQL, uploads, processed pages, reports and heatmaps. Do not use volume-reset commands or delete evidence to fix an error.

## Build an update

Frontend requires Node >=20.19, tested with Node 24.12.0. The frozen inference runtime uses Python 3.10, NumPy 1.26.4 and scikit-learn 1.3.2 in the existing backend image. Do not upgrade those packages to repair optional OCR without a separately evaluated environment plan.

```powershell
Set-Location 'D:\Forgery Detection ML\frontend'
npm ci
npm test
npm run build
Set-Location ..
docker compose --env-file .env.pilot -f docker-compose.pilot.yml build backend frontend
```

Before any further database migration, make and verify a custom-format PostgreSQL backup and test the change on an isolated restored database. This delivery already applied revision `a61000000005` to the native and pilot databases. It only adds nullable `analyses.context_snapshot`. The original migrator lacks table ownership; the existing owner was used for that specific migration, with runtime grants unchanged. Do not broaden runtime permissions. The migration intentionally refuses destructive downgrade of forensic snapshots.

After migrations and checks, update the existing containers:

```powershell
docker compose --env-file .env.pilot -f docker-compose.pilot.yml up -d --no-deps backend frontend
python project_audit/verify_final_state.py
```

`deploy_stabilized_pilot.py` records the migration/update procedure and requires its verified pre-migration backup. It reads credentials into child environments without printing them. Compose run is unsuitable for the migration because the backend uses a fixed occupied IP; the script uses a temporary container with an automatically assigned address.

## Run verification safely

```powershell
python scripts/run_isolated_backend_tests.py
Set-Location frontend
npm test
npm run build
npm audit
```

The backend harness creates a new `vf_test_*` database and dedicated file directories from the verified schema backup, then applies migrations. Never run older live-mutating test scripts against historical data. Keep test databases/files until reviewed; this delivery does not automatically delete evidence. Restricted Windows environments must allow scikit-learn worker resources and esbuild subprocesses for these checks.

`verify_isolated_workflows.py` uses the restored clone named in its source and retained controlled fixtures. `verify_live_pilot.py` creates a fresh controlled account and synthetic cases/exhibits, generates a report, and restarts all three existing pilot containers. Run it only when this temporary service interruption and retained test artifacts are intended. It is not a read-only health check. Use `verify_final_state.py` for read-only final deployment checks.

## Demonstration sequence

1. Sign in or register in the chosen environment. Show live health and actual case/document totals. OCR should say unavailable in the pilot.
2. Start **New investigation**. Choose `project_audit/controlled_evidence/baseline.png`, add a clearly labeled demo title/notes/priority, then execute. These files are synthetic workflow controls, not certified authentic documents.
3. Show the document assessment and **Unmodified raw model result** separately. Explain T=.40, source page and maximum-page selection caveat. Neither proves authenticity.
4. Inspect the nine module cards. Follow **Inspect evidence** to genuine measurements. Show all 18 input values and imputed fields; an unavailable legacy field must remain unavailable.
5. Zoom the page, click a highlighted region if one exists, and inspect its explanation. If the control yields no regions, explain that result rather than inventing one. Toggle the actual ELA map. Download the original and compare SHA-256 with `controlled_provenance.json`.
6. Upload `two_pages.pdf`, navigate both pages and inspect per-page scores and page-local regions. The preview is a derived raster; the original PDF remains downloadable.
7. Upload `modified.jpg`, then compare it with the baseline using the filename suggestions. Show alignment status, visual differences and limitations. JPEG and PNG differences include encoding effects, so this is a workflow demonstration, not calibrated edit localization accuracy.
8. Export a PDF with analyst notes. Open it from Reports; check actual page count, analysis version, limitations and stored/download hash. Case ID is included; full case narrative integration remains partial.
9. Open Cases and Analytics. Show persisted notes/priority and actual counts. Format charts and lists disclose their 100-exhibit window.
10. With an authorized administrator account, open Settings → User management. Review roles/status; create or deactivate only intended demo accounts. No automatic historical account changes were performed.
11. Explain restart verification from `live_pilot_verification.json`: original hashes, raw vectors, ELA maps and report all survived PostgreSQL/backend/frontend restart. Demonstrate again only on controlled evidence if an interruption is acceptable.

## Troubleshooting and recovery

A 500 response alone does not identify its cause. Inspect the matching backend log without exposing credentials. During initial startup, stopped backend/database services caused proxy connection failures. Both services are now running; deeper ingestion/persistence/report issues were repaired and verified separately.

For 503, check database connectivity and frozen-model health. For 410, preserve records and investigate a missing original. For 409, preserve the exhibit and custody history; inspect the ingestion digest and storage mismatch. Never overwrite bytes to silence a tamper alarm. A missing old snapshot cannot be recovered by inventing its values.

Backups and manifests are under `project_audit/backups`. The native archive was restored into an isolated database before migration testing. The pilot archive listing/hash was verified; a full independent pilot disaster-recovery restore drill was not completed. Restore to a new isolated database/volume first, verify evidence storage and hashes, and obtain operational review before any replacement of an active evidence store.
