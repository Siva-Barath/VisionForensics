"""
backup_db.py — Automated Database & Exhibit Storage Backup Utility with Authenticated HMAC & SHA-256 Verification.

Creates an authenticated, tamper-evident backup snapshot containing:
1. PostgreSQL database dump (custom archive format via pg_dump).
2. Primary document exhibits (uploads/).
3. Generated forensic reports (reports/).
4. Integrity Checksum: backup_manifest.json.sha256 (SHA-256 integrity digest).
5. Authenticity Signature: backup_manifest.json.hmac (HMAC-SHA256 digital signature).

NOTE ON ARTIFACT STORAGE POLICIES:
- uploads/ (raw original exhibits): Preserved in backup.
- reports/ (signed PDF investigation reports): Preserved in backup.
- processed/ (derived PNG page renderings): Ephemeral, omitted to prevent bloat; regenerated on-demand.
- heatmaps/ (derived differential comparison masks): Ephemeral, omitted to prevent bloat; regenerated on-demand.

AUTHENTICATION NOTE:
Plain SHA-256 checksums verify data integrity against accidental corruption or bit-rot, but DO NOT
provide authenticity against malicious tampering. An adversary with filesystem write access to the backup
directory could modify exhibits or database dumps and simply recompute the SHA-256 manifest.
Therefore, VisionForensics AI requires an HMAC-SHA256 signature generated with a secret key
(BACKUP_HMAC_KEY) stored in a secure secrets manager OUTSIDE the backup directory.

Usage:
    python scripts/backup_db.py [--output-dir backups] [--hmac-key <HEX_KEY> | --key-file <PATH>]
"""

import sys
import os
import shutil
import hashlib
import hmac
import json
import argparse
import subprocess
from datetime import datetime, timezone
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


def find_pg_dump() -> str:
    """Locates pg_dump executable in PATH or standard installation directories."""
    sh_path = shutil.which("pg_dump")
    if sh_path:
        return sh_path

    for ver in ["17", "16", "15"]:
        cand = Path(f"C:/Program Files/PostgreSQL/{ver}/bin/pg_dump.exe")
        if cand.exists():
            return str(cand)

    return "pg_dump"


def get_hmac_key(args) -> bytes:
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
    
    # Generate default ephemeral session key if none provided and warn operator
    ephemeral = hashlib.sha256(os.urandom(32)).hexdigest()
    print("\n[WARNING] No --hmac-key or BACKUP_HMAC_KEY provided.")
    print(f"Generated ephemeral HMAC key for this backup session:")
    print(f"  --> {ephemeral}")
    print("Store this key securely outside the backup folder. It is required for restoration.\n")
    return ephemeral.encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="VisionForensics AI Backup Utility")
    parser.add_argument("--output-dir", default="backups", help="Target backups root directory")
    parser.add_argument("--hmac-key", default=None, help="Secret HMAC-SHA256 key for authenticating the manifest")
    parser.add_argument("--key-file", default=None, help="Path to secret HMAC key file outside backup storage")
    args = parser.parse_args()

    settings = get_settings()
    hmac_key = get_hmac_key(args)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_root = Path(args.output_dir).resolve()
    dest_dir = backup_root / f"visionforensics_backup_{ts}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("VISIONFORENSICS AI — AUTHENTICATED DATABASE & STORAGE BACKUP")
    print("=" * 70)
    print(f"Timestamp:       {ts} UTC")
    print(f"Destination:     {dest_dir}")

    manifest = {
        "timestamp_utc": ts,
        "database": {},
        "files": [],
        "summary": {},
        "artifact_policy": {
            "uploads": "Backed up (raw original exhibits)",
            "reports": "Backed up (generated tamper-evident PDF dossiers)",
            "processed": "Ephemeral (omitted; regenerated on-demand)",
            "heatmaps": "Ephemeral (omitted; regenerated on-demand)",
        },
    }

    # 1. PostgreSQL Database Dump
    pg_dump_bin = find_pg_dump()
    dump_file = dest_dir / "visionforensics_db.dump"
    db_name = "visionforensics"
    db_port = "5433"
    db_user = "postgres"

    print(f"\n[1/3] Executing PostgreSQL database dump via {pg_dump_bin}...")
    env = os.environ.copy()
    env["PGPASSWORD"] = "postgres"

    cmd = [
        pg_dump_bin,
        "-h", "127.0.0.1",
        "-p", db_port,
        "-U", db_user,
        "-F", "c",
        "-b",
        "-v",
        "-f", str(dump_file),
        db_name,
    ]

    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"[ERROR] pg_dump failed:\n{proc.stderr}")
            sys.exit(proc.returncode)
        dump_hash = compute_sha256(dump_file)
        (dest_dir / "visionforensics_db.dump.sha256").write_text(f"{dump_hash}  visionforensics_db.dump\n")
        manifest["database"] = {
            "file": "visionforensics_db.dump",
            "size_bytes": dump_file.stat().st_size,
            "sha256_hash": dump_hash,
            "status": "COMPLETED",
        }
        print(f"  * Database dump completed: {dump_file.name} ({dump_file.stat().st_size:,} bytes)")
        print(f"  * Dump SHA-256 Checksum:  {dump_hash}")
    except Exception as e:
        print(f"[ERROR] Database dump execution exception: {e}")
        sys.exit(1)

    # 2. Back up Document Exhibits (uploads/)
    print("\n[2/3] Backing up original document exhibits...")
    uploads_src = Path(settings.upload_dir).resolve()
    uploads_dest = dest_dir / "uploads"
    uploads_dest.mkdir(exist_ok=True)
    file_count = 0

    if uploads_src.exists():
        for f in uploads_src.glob("*.*"):
            if f.is_file():
                dest_f = uploads_dest / f.name
                shutil.copy2(f, dest_f)
                h = compute_sha256(dest_f)
                manifest["files"].append({
                    "category": "exhibit",
                    "filename": f.name,
                    "size_bytes": dest_f.stat().st_size,
                    "sha256_hash": h,
                })
                file_count += 1
    print(f"  * Backed up {file_count} original exhibit files into {uploads_dest.name}/")

    # 3. Back up Generated Reports (reports/)
    print("\n[3/3] Backing up generated forensic reports...")
    reports_src = Path(settings.reports_dir).resolve()
    reports_dest = dest_dir / "reports"
    reports_dest.mkdir(exist_ok=True)
    report_count = 0

    if reports_src.exists():
        for r_dir in reports_src.iterdir():
            if r_dir.is_dir():
                target_r_dir = reports_dest / r_dir.name
                target_r_dir.mkdir(exist_ok=True)
                for pdf in r_dir.glob("*.pdf"):
                    dest_pdf = target_r_dir / pdf.name
                    shutil.copy2(pdf, dest_pdf)
                    h = compute_sha256(dest_pdf)
                    manifest["files"].append({
                        "category": "report",
                        "report_id": r_dir.name,
                        "filename": pdf.name,
                        "size_bytes": dest_pdf.stat().st_size,
                        "sha256_hash": h,
                    })
                    report_count += 1
    print(f"  * Backed up {report_count} forensic PDF reports into {reports_dest.name}/")

    # 4. Manifest Integrity Digest & HMAC Authentication Signature
    manifest["summary"] = {
        "total_exhibits": file_count,
        "total_reports": report_count,
        "total_manifest_items": len(manifest["files"]) + 1,
    }
    manifest_file = dest_dir / "backup_manifest.json"
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_file.write_bytes(manifest_bytes)

    # 4a. Integrity Checksum (SHA-256)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    (dest_dir / "backup_manifest.json.sha256").write_text(f"{manifest_hash}  backup_manifest.json\n")

    # 4b. Authenticity Signature (HMAC-SHA256)
    manifest_hmac = hmac.new(hmac_key, manifest_bytes, hashlib.sha256).hexdigest()
    (dest_dir / "backup_manifest.json.hmac").write_text(f"{manifest_hmac}  backup_manifest.json\n")

    print("\n" + "=" * 70)
    print("BACKUP COMPLETED WITH INTEGRITY CHECKSUM & HMAC AUTHENTICITY")
    print("=" * 70)
    print(f"Manifest Path:     {manifest_file}")
    print(f"Manifest SHA-256:  {manifest_hash} (Integrity)")
    print(f"Manifest HMAC:     {manifest_hmac} (Authenticity)")
    print("=" * 70)


if __name__ == "__main__":
    main()
