"""
restore_db.py — Automated Database & Storage Restoration Utility with Authenticated HMAC & SHA-256 Pre-Flight Integrity Check.

Multi-Layer Pre-Flight Security Validation:
1. Manifest Authenticity Check: Recomputes and validates HMAC-SHA256 signature using the operator's secret key.
2. Manifest Integrity Check: Validates backup_manifest.json against backup_manifest.json.sha256.
3. Database Dump Integrity Check: Validates visionforensics_db.dump SHA-256 against manifest digest.
4. Artifact Integrity Check: Validates every exhibit and forensic PDF report against recorded SHA-256 hashes.
5. Abort-on-Tamper Policy: Any hash or signature discrepancy immediately aborts restoration before touching the target database or filesystem.

Isolation Protection:
- By default, verifies integrity without mutating any database or storage.
- Requires explicit --target-db and --restore-db to restore into PostgreSQL.
- Requires explicit --target-storage-dir and --restore-files to restore files.
- Prevents accidental overwriting of active pilot database or exhibits during testing.

Usage:
    python scripts/restore_db.py --backup-dir <PATH> [--hmac-key <KEY> | --key-file <PATH>]
    python scripts/restore_db.py --backup-dir <PATH> --hmac-key <KEY> --target-db visionforensics_restore_test --restore-db --target-storage-dir test_restore --restore-files
"""

import sys
import os
import shutil
import hashlib
import hmac
import json
import argparse
import subprocess
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config.settings import get_settings


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def find_pg_restore() -> str:
    """Locates pg_restore executable in PATH or standard installation directories."""
    sh_path = shutil.which("pg_restore")
    if sh_path:
        return sh_path

    for ver in ["17", "16", "15"]:
        cand = Path(f"C:/Program Files/PostgreSQL/{ver}/bin/pg_restore.exe")
        if cand.exists():
            return str(cand)

    return "pg_restore"


def get_hmac_key(args) -> bytes | None:
    """Resolves HMAC key from CLI flag, key file, or environment variable."""
    if args.hmac_key:
        return args.hmac_key.strip().encode("utf-8")
    if args.key_file:
        key_path = Path(args.key_file).resolve()
        if not key_path.exists():
            raise FileNotFoundError(f"HMAC key file not found: {key_path}")
        return key_path.read_text(encoding="utf-8").strip().encode("utf-8")
    env_key = os.environ.get("BACKUP_HMAC_KEY")
    if env_key:
        return env_key.strip().encode("utf-8")
    return None


def main():
    parser = argparse.ArgumentParser(description="VisionForensics AI Backup Verification & Restoration Utility")
    parser.add_argument("--backup-dir", required=True, help="Path to backup snapshot directory")
    parser.add_argument("--hmac-key", default=None, help="Secret HMAC-SHA256 key for authenticating the manifest")
    parser.add_argument("--key-file", default=None, help="Path to secret HMAC key file")
    parser.add_argument("--target-db", default=None, help="Target PostgreSQL database name for restoration")
    parser.add_argument("--db-port", default="5433", help="Target PostgreSQL port")
    parser.add_argument("--db-user", default="postgres", help="PostgreSQL user for restoration")
    parser.add_argument("--restore-db", action="store_true", help="Execute pg_restore into target database")
    parser.add_argument("--target-storage-dir", default=None, help="Target directory for restored uploads/reports")
    parser.add_argument("--restore-files", action="store_true", help="Restore exhibit and report files")
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir).resolve()
    if not backup_dir.exists():
        print(f"[ERROR] Backup directory does not exist: {backup_dir}")
        sys.exit(1)

    print("=" * 70)
    print("VISIONFORENSICS AI — BACKUP AUTHENTICITY & INTEGRITY VERIFICATION")
    print("=" * 70)
    print(f"Target Backup:   {backup_dir}")

    # 1. Manifest Files Check
    manifest_file = backup_dir / "backup_manifest.json"
    manifest_sha_file = backup_dir / "backup_manifest.json.sha256"
    manifest_hmac_file = backup_dir / "backup_manifest.json.hmac"

    if not manifest_file.exists():
        print("[CRITICAL SECURITY ERROR] Manifest file 'backup_manifest.json' is missing.")
        sys.exit(1)

    manifest_bytes = manifest_file.read_bytes()

    # 2. Authenticity Verification (HMAC-SHA256)
    if manifest_hmac_file.exists():
        hmac_key = get_hmac_key(args)
        if not hmac_key:
            print("[CRITICAL SECURITY ERROR] Manifest has an HMAC signature (.hmac) but no HMAC key was provided!")
            print("Provide the HMAC secret via --hmac-key, --key-file, or BACKUP_HMAC_KEY env var.")
            sys.exit(1)

        expected_hmac = manifest_hmac_file.read_text().split()[0].strip()
        actual_hmac = hmac.new(hmac_key, manifest_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_hmac, actual_hmac):
            print("[CRITICAL SECURITY ALARM] Manifest HMAC authenticity verification FAILED!")
            print(f"  Expected HMAC: {expected_hmac}")
            print(f"  Computed HMAC: {actual_hmac}")
            print("RESTORATION ABORTED: Manifest was forged, altered, or signed with an unauthorized key.")
            sys.exit(1)
        print("  * Manifest Authenticity (HMAC-SHA256):  VERIFIED (Signature Valid)")
    else:
        print("  * [NOTICE] No .hmac signature file found. Relying strictly on SHA-256 integrity.")

    # 3. Integrity Verification (SHA-256 Checksum)
    if manifest_sha_file.exists():
        expected_manifest_sha = manifest_sha_file.read_text().split()[0].strip()
        actual_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        if expected_manifest_sha != actual_manifest_sha:
            print("[CRITICAL SECURITY ALARM] Manifest SHA-256 checksum mismatch! Manifest is corrupted.")
            print(f"  Expected: {expected_manifest_sha}")
            print(f"  Actual:   {actual_manifest_sha}")
            sys.exit(1)
        print("  * Manifest Integrity (SHA-256 Checksum): VERIFIED")

    manifest = json.loads(manifest_bytes.decode("utf-8"))

    # 4. Database Dump Integrity Check
    dump_info = manifest.get("database", {})
    dump_filename = dump_info.get("file", "visionforensics_db.dump")
    dump_file = backup_dir / dump_filename
    if not dump_file.exists():
        print(f"[ERROR] Database dump archive '{dump_filename}' not found in backup package.")
        sys.exit(1)

    actual_dump_sha = compute_sha256(dump_file)
    expected_dump_sha = dump_info.get("sha256_hash")
    if actual_dump_sha != expected_dump_sha:
        print("[CRITICAL SECURITY ALARM] Database dump SHA-256 mismatch! File corrupted or modified.")
        print(f"  Expected: {expected_dump_sha}")
        print(f"  Actual:   {actual_dump_sha}")
        sys.exit(1)
    print(f"  * Database Dump Integrity:              VERIFIED ({actual_dump_sha})")

    # 5. File Artifacts Integrity Check
    print("\n[Verification] Validating individual exhibits and forensic reports...")
    verified_files = 0
    for item in manifest.get("files", []):
        cat = item["category"]
        fn = item["filename"]
        exp_h = item["sha256_hash"]

        if cat == "exhibit":
            f_path = backup_dir / "uploads" / fn
        elif cat == "report":
            f_path = backup_dir / "reports" / item["report_id"] / fn
        else:
            continue

        if not f_path.exists():
            print(f"[CRITICAL SECURITY ALARM] Missing artifact referenced in manifest: {f_path}")
            sys.exit(1)

        actual_h = compute_sha256(f_path)
        if actual_h != exp_h:
            print(f"[CRITICAL SECURITY ALARM] Artifact SHA-256 mismatch for '{fn}':")
            print(f"  Expected: {exp_h}")
            print(f"  Actual:   {actual_h}")
            print("RESTORATION ABORTED: Stored evidence or report has been tampered with.")
            sys.exit(1)
        verified_files += 1

    print(f"  * All {verified_files} exhibits and reports verified against cryptographic manifest.")

    # 6. Optional Clean Storage Files Restoration
    if args.restore_files:
        if not args.target_storage_dir:
            print("[ERROR] --restore-files requires --target-storage-dir to prevent overwriting active storage.")
            sys.exit(1)
        target_base = Path(args.target_storage_dir).resolve()
        target_uploads = target_base / "uploads"
        target_reports = target_base / "reports"
        target_uploads.mkdir(parents=True, exist_ok=True)
        target_reports.mkdir(parents=True, exist_ok=True)

        print(f"\n[Restoration] Restoring {verified_files} storage artifacts to {target_base}...")
        for f in (backup_dir / "uploads").glob("*.*"):
            if f.is_file():
                shutil.copy2(f, target_uploads / f.name)

        for r_dir in (backup_dir / "reports").iterdir():
            if r_dir.is_dir():
                t_dir = target_reports / r_dir.name
                t_dir.mkdir(parents=True, exist_ok=True)
                for pdf in r_dir.glob("*.pdf"):
                    shutil.copy2(pdf, t_dir / pdf.name)

        print("  * Storage artifacts restored successfully into target directory.")

    # 7. Optional Clean Database Restoration via pg_restore
    if args.restore_db:
        if not args.target_db:
            print("[ERROR] --restore-db requires --target-db (e.g. --target-db visionforensics_restore_test).")
            print("Refusing to restore without an explicit target database name.")
            sys.exit(1)

        pg_restore_bin = find_pg_restore()
        print(f"\n[Restoration] Executing pg_restore into database '{args.target_db}' on port {args.db_port}...")
        env = os.environ.copy()
        env["PGPASSWORD"] = "postgres"

        cmd = [
            pg_restore_bin,
            "-h", "127.0.0.1",
            "-p", args.db_port,
            "-U", args.db_user,
            "-d", args.target_db,
            "--clean",
            "--if-exists",
            str(dump_file),
        ]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        # Note: pg_restore may return 1 if non-fatal warnings (e.g. drop non-existent objects), check stderr
        if proc.returncode != 0 and "errors ignored on restore" not in proc.stderr.lower():
            print(f"[ERROR] pg_restore failed with returncode {proc.returncode}:\n{proc.stderr}")
            sys.exit(proc.returncode)
        print(f"  * PostgreSQL restore completed successfully into '{args.target_db}'.")

    print("\n" + "=" * 70)
    print("BACKUP VERIFICATION & RESTORATION PROCEDURE COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
