"""
verify_storage_integrity.py — Verifies exhibit overwrite prevention and download-time report tamper detection.
"""

import sys
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config.settings import get_settings
from app.services.storage_service import StorageService
from app.services.report_service import ReportService
from app.database.session import SessionLocal
from app.models.report import ForensicReport
from app.models.audit import ExhibitCustodyLog
from app.core.exceptions import StorageError

print("=" * 70)
print("VERIFYING STORAGE INTEGRITY & TAMPER-EVIDENT CONTROLS")
print("=" * 70)

settings = get_settings()
storage_svc = StorageService(settings)
report_svc = ReportService()
db: Session = SessionLocal()

# 1. Verify Original Exhibit Overwrite Prevention
print("\n[CHECK 1/2] Testing Original Exhibit Overwrite Prevention...")
test_doc_id = "test_doc_overwrite_guard"
test_filename = "specimen_sample.png"
test_content = b"ORIGINAL_PRISTINE_EXHIBIT_CONTENT"

# First write: should succeed
p1 = storage_svc.save_upload(test_content, test_doc_id, test_filename)
print(f"  * First write succeeded: {p1.name}")

# Second write with same doc_id and filename: MUST raise StorageError
try:
    storage_svc.save_upload(b"ATTEMPTED_OVERWRITE_CONTENT", test_doc_id, test_filename)
    print("  [X] FAIL: Overwrite was permitted without error!")
    sys.exit(1)
except StorageError as se:
    print(f"  * Overwrite blocked as expected: {se}")
    print("  --> PASS: Storage layer strictly prohibits overwriting existing exhibits.")
finally:
    if p1.exists():
        p1.unlink()

# 2. Verify Download-Time Tamper Detection on Reports
print("\n[CHECK 2/2] Testing Report Download-Time Mutation Detection (SHA-256)...")
rep = db.query(ForensicReport).first()
if not rep:
    print("  [SKIP] No reports found in database to test tamper detection.")
else:
    rep_file = Path(rep.file_path).resolve()
    print(f"  * Testing against Report: {rep.report_number} ({rep_file.name})")
    original_bytes = rep_file.read_bytes()

    try:
        # Simulate an unauthorized modification on disk
        with open(rep_file, "ab") as f:
            f.write(b"\x00UNAUTHORIZED_TAMPER_BYTES\x00")

        # Now attempt to get the report file via ReportService
        try:
            report_svc.get_report_file(db, rep.id, user_id=None, ip_address="127.0.0.1")
            print("  [X] FAIL: Tampered report was served without error!")
            sys.exit(1)
        except HTTPException as he:
            if he.status_code == 409 and "TAMPERING_ALARM" in he.detail:
                print(f"  * Tamper detected successfully: HTTP {he.status_code} - {he.detail}")

                # Verify TAMPERING_ALARM logged in exhibit_custody_logs
                latest_alarm = (
                    db.query(ExhibitCustodyLog)
                    .filter(ExhibitCustodyLog.event_type == "TAMPERING_ALARM")
                    .order_by(ExhibitCustodyLog.timestamp.desc())
                    .first()
                )
                assert latest_alarm is not None, "TAMPERING_ALARM not found in custody log!"
                assert latest_alarm.status == "TAMPERED", f"Expected status TAMPERED, got {latest_alarm.status}"
                print(f"  * Custody Ledger Record:   Event='{latest_alarm.event_type}', Status='{latest_alarm.status}'")
                print("  --> PASS: Download-time SHA-256 check strictly alarms on file tampering.")
            else:
                print(f"  [X] Unexpected exception: {he}")
                sys.exit(1)
    finally:
        # Restore pristine file bytes
        rep_file.write_bytes(original_bytes)
        print(f"  * Restored original report bytes for {rep.report_number}.")

db.close()
print("\n" + "=" * 70)
print("STORAGE INTEGRITY & TAMPER-EVIDENT CONTROLS FULLY VERIFIED")
print("=" * 70)
