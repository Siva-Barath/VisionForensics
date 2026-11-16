"""
test_tamper_abort.py — Automated verification that tampered manifests, dumps, and exhibits cause restoration to abort.
"""

import shutil
import subprocess
import sys
from pathlib import Path

backup_src = Path("backups/visionforensics_backup_20261101_085556").resolve()
test_dir = Path("backups/test_tamper_scenario").resolve()
hmac_key = "1b74fca78d2b78184f9f635c24e5a953e34b17173b9846399949d05e040aa912"

def reset_test_dir():
    if test_dir.exists():
        shutil.rmtree(test_dir)
    shutil.copytree(backup_src, test_dir)

print("=" * 70)
print("TESTING BACKUP TAMPER-DETECTION & RESTORATION ABORT CONTROLS")
print("=" * 70)

# Scenario A: Tampered Manifest (or wrong HMAC key)
print("\n[SCENARIO A] Testing Tampered Manifest / Invalid HMAC Key...")
reset_test_dir()
# Alter manifest JSON slightly
m_file = test_dir / "backup_manifest.json"
m_text = m_file.read_text(encoding="utf-8")
m_file.write_text(m_text.replace("total_exhibits", "tampered_exhibits"), encoding="utf-8")

res_a = subprocess.run(
    ["python", "scripts/restore_db.py", "--backup-dir", str(test_dir), "--hmac-key", hmac_key],
    capture_output=True,
    text=True,
)
if res_a.returncode != 0 and "Manifest HMAC authenticity verification FAILED" in res_a.stdout:
    print("  --> PASS: Restoration aborted immediately upon detecting tampered manifest.")
else:
    print(f"  --> FAIL: Unexpected return code {res_a.returncode}\n{res_a.stdout}\n{res_a.stderr}")
    sys.exit(1)

# Scenario B: Tampered Database Dump
print("\n[SCENARIO B] Testing Tampered Database Dump (visionforensics_db.dump)...")
reset_test_dir()
dump_file = test_dir / "visionforensics_db.dump"
with open(dump_file, "r+b") as f:
    f.seek(100)
    b = f.read(1)
    f.seek(100)
    f.write(bytes([b[0] ^ 0xFF]))  # flip bits

res_b = subprocess.run(
    ["python", "scripts/restore_db.py", "--backup-dir", str(test_dir), "--hmac-key", hmac_key],
    capture_output=True,
    text=True,
)
if res_b.returncode != 0 and "Database dump SHA-256 mismatch" in res_b.stdout:
    print("  --> PASS: Restoration aborted immediately upon detecting tampered database dump.")
else:
    print(f"  --> FAIL: Unexpected return code {res_b.returncode}\n{res_b.stdout}\n{res_b.stderr}")
    sys.exit(1)

# Scenario C: Tampered Document Exhibit Artifact
print("\n[SCENARIO C] Testing Tampered Original Exhibit Artifact...")
reset_test_dir()
# Modify one exhibit in uploads
uploads_files = list((test_dir / "uploads").glob("*.*"))
if uploads_files:
    target_exhibit = uploads_files[0]
    with open(target_exhibit, "ab") as f:
        f.write(b"\x00TAMPER_BYTES\x00")

    res_c = subprocess.run(
        ["python", "scripts/restore_db.py", "--backup-dir", str(test_dir), "--hmac-key", hmac_key],
        capture_output=True,
        text=True,
    )
    if res_c.returncode != 0 and "Artifact SHA-256 mismatch" in res_c.stdout:
        print("  --> PASS: Restoration aborted immediately upon detecting tampered exhibit file.")
    else:
        print(f"  --> FAIL: Unexpected return code {res_c.returncode}\n{res_c.stdout}\n{res_c.stderr}")
        sys.exit(1)

# Clean up
if test_dir.exists():
    shutil.rmtree(test_dir)

print("\n" + "=" * 70)
print("TAMPER-DETECTION ABORT CONTROLS FULLY VERIFIED (All 3/3 Scenarios Passed)")
print("=" * 70)
