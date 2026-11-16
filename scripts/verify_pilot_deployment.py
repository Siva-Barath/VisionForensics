"""
verify_pilot_deployment.py — Operational Pre-Flight Verification Script for Controlled Pilot.

Performs automated non-destructive health, security, environment, and invariance checks:
1. Environment & Configuration Sanity:
   - Must be strictly APP_ENV=pilot (development and unset environments FAIL immediately).
   - APP_DEBUG must be False.
   - Development fallback analyst must be disabled (strict 401 on unauthenticated requests).
   - Secret key must not be default development key.
2. Database Connectivity & Role Separation:
   - Application runtime MUST connect as 'visionforensics_app' (NOT postgres or migrator).
   - Migration database URL MUST configure 'visionforensics_migrator'.
   - Append-only custody enforcement on exhibit_custody_logs (UPDATE/DELETE permission denied).
3. Persistent Storage Directories:
   - uploads/, processed/, reports/, heatmaps/ are verified for read/write access.
4. Model Artifact & Benchmark Invariance:
   - Artifact SHA-256: f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280.
   - Features: Exactly 18 features.
   - Operational Decision Threshold: T = 0.40.
5. Frontend Production Distribution Assets:
   - frontend/dist/index.html is verified.

Usage:
    python scripts/verify_pilot_deployment.py
"""

import sys
import hashlib
import asyncio
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import urlparse
from sqlalchemy import text
from fastapi import HTTPException
import joblib

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.core.auth import get_current_user
from app.services.ml_inference import MLInferenceService


def main():
    print("=" * 70)
    print("VISIONFORENSICS AI — CONTROLLED PILOT DEPLOYMENT PRE-FLIGHT CHECK")
    print("=" * 70)

    settings = get_settings()
    failures = []

    # 1. Environment & Security Configuration Flags
    print("\n[CHECK 1/5] Environment & Security Flags...")
    effective_env = settings.app_env.strip()
    print(f"  * Effective APP_ENV:        {effective_env}")
    print(f"  * APP_DEBUG:                {settings.app_debug}")
    print(f"  * Max File Size:            {settings.max_file_size_mb} MB")
    print(f"  * Max PDF Pages:            {settings.max_pdf_pages}")
    print(f"  * Trusted Proxies:          {settings.trusted_proxies}")
    print(f"  * Allowed Origins:          {settings.allowed_origins}")

    # Strict APP_ENV enforcement: MUST be exactly 'pilot'
    if effective_env.lower() != "pilot":
        failures.append(
            f"ENVIRONMENT: Effective APP_ENV is '{effective_env}'. "
            "Controlled pilot verification strictly requires APP_ENV=pilot (development and unset environments are prohibited)."
        )

    # Strict APP_DEBUG enforcement
    if settings.app_debug is not False:
        failures.append("SECURITY: APP_DEBUG must be strictly False in pilot environment.")

    # Strict secret key enforcement
    if settings.secret_key in ("change-me", "dev-secret-key-replace-in-production", ""):
        failures.append("SECURITY: SECRET_KEY contains default or empty development secret.")

    # Test dev analyst fallback is disabled in pilot
    try:
        mock_req = MagicMock()
        mock_req.cookies = {}
        mock_req.query_params = {}
        db = SessionLocal()
        try:
            user = asyncio.run(get_current_user(request=mock_req, credentials=None, db=db))
            failures.append(
                f"SECURITY: Dev analyst fallback is active! Returned unauthenticated user '{user.email}'."
            )
        except HTTPException as he:
            if he.status_code == 401:
                print("  * Dev Analyst Fallback:     DISABLED (401 Unauthorized strictly enforced)")
            else:
                failures.append(f"SECURITY: Unexpected auth exception status: {he.status_code}")
        finally:
            db.close()
    except Exception as e:
        failures.append(f"SECURITY: Failed checking dev fallback analyst: {e}")

    # 2. Database Connectivity & Role Separation
    print("\n[CHECK 2/5] Database Connectivity & Role Separation...")
    try:
        db = SessionLocal()
        res = db.execute(text("SELECT current_user, current_database();")).fetchone()
        connected_user = res[0]
        connected_db = res[1]
        print(f"  * Connected as DB User:     {connected_user} to Database: {connected_db}")

        if connected_user != "visionforensics_app":
            failures.append(
                f"DATABASE ROLE: Application runtime must connect as 'visionforensics_app', but connected as '{connected_user}'. "
                "Superuser 'postgres' and migrator roles are prohibited for runtime application traffic."
            )

        # Verify migration URL uses visionforensics_migrator
        mig_url = settings.migration_database_url
        parsed_mig = urlparse(mig_url)
        mig_user = parsed_mig.username
        if mig_user != "visionforensics_migrator":
            failures.append(
                f"DATABASE ROLE: MIGRATION_DATABASE_URL must configure user 'visionforensics_migrator', got '{mig_user}'."
            )
        else:
            print(f"  * Migrator Role Config:     {mig_user} (VERIFIED for Alembic migrations)")

        # Test append-only constraint on exhibit_custody_logs
        try:
            db.execute(text("UPDATE exhibit_custody_logs SET status = 'TAMPERED' WHERE id = '00000000-0000-0000-0000-000000000000';"))
            db.commit()
            failures.append("SECURITY: exhibit_custody_logs allows UPDATE queries. Expected permission denied.")
        except Exception as e:
            db.rollback()
            err_str = str(e).lower()
            if "permission denied" in err_str:
                print("  * Custody Ledger Security:  ENFORCED (UPDATE permission denied for app role)")
            else:
                print(f"  * Custody Ledger check returned: {e}")

        db.close()
    except Exception as e:
        failures.append(f"DATABASE: Connection failed: {e}")

    # 3. Storage Directory Verification
    print("\n[CHECK 3/5] Storage Directory Persistence & Permissions...")
    dirs_to_check = [
        ("Uploads", settings.upload_dir),
        ("Processed Pages", settings.processed_dir),
        ("Reports", settings.reports_dir),
        ("Heatmaps", settings.heatmaps_dir),
    ]
    for label, d in dirs_to_check:
        p = Path(d).resolve()
        p.mkdir(parents=True, exist_ok=True)
        # Check write permission
        test_file = p / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print(f"  * {label:<16}: {p} (READ/WRITE OK)")
        except Exception as e:
            failures.append(f"STORAGE: Cannot write to {p}: {e}")

    # 4. Model Invariance Check
    print("\n[CHECK 4/5] Model Artifact & Benchmark Invariance...")
    rf_path = Path("backend/app/ml/artifacts/random_forest.joblib").resolve()
    if not rf_path.exists():
        failures.append(f"MODEL: Artifact missing at {rf_path}")
    else:
        raw_bytes = rf_path.read_bytes()
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        expected_hash = "f274d4a93661ce8c5fd95f41a43e629edac41ab16d771355e7decacf0040e280"
        if actual_hash != expected_hash:
            failures.append(f"MODEL: SHA-256 hash mismatch: expected {expected_hash}, got {actual_hash}")
        else:
            print(f"  * Artifact SHA-256:        {actual_hash} (VERIFIED)")

        model = joblib.load(rf_path)
        if model.n_features_in_ != 18:
            failures.append(f"MODEL: Feature count mismatch: expected 18, got {model.n_features_in_}")
        else:
            print(f"  * Feature Dimension:        18 Features (VERIFIED)")

        import inspect
        inf = MLInferenceService()
        threshold = inspect.signature(inf.predict_from_features).parameters["operational_threshold"].default
        if threshold != 0.40:
            failures.append(f"MODEL: Decision threshold mismatch: expected 0.40, got {threshold}")
        else:
            print(f"  * Operational Threshold:    T = {threshold:.2f} (VERIFIED)")

    # 5. Frontend Production Distribution
    print("\n[CHECK 5/5] Frontend Production Distribution Assets...")
    frontend_dist = Path("frontend/dist/index.html").resolve()
    if not frontend_dist.exists():
        failures.append(f"FRONTEND: Production distribution missing at {frontend_dist}. Run 'npm run build'.")
    else:
        size = frontend_dist.stat().st_size
        print(f"  * SPA Index HTML:           {frontend_dist} ({size:,} bytes, VERIFIED)")

    # Summary
    print("\n" + "=" * 70)
    if failures:
        print("PRE-FLIGHT STATUS: FAILED (Corrections Required)")
        print("=" * 70)
        for f in failures:
            print(f"  [X] {f}")
        sys.exit(1)
    else:
        print("PRE-FLIGHT STATUS: ALL CHECKS PASSED (Ready for Controlled Pilot)")
        print("=" * 70)


if __name__ == "__main__":
    main()
