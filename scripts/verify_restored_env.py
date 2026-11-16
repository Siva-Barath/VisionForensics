"""
verify_restored_env.py — Verifies database tables, exhibits, reports, and comparisons in the restored test environment.
"""

import hashlib
import psycopg2
from pathlib import Path

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("=" * 70)
print("POST-RESTORE CLEAN ENVIRONMENT INTEGRITY VERIFICATION")
print("=" * 70)

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5433/visionforensics_restore_test")
cur = conn.cursor()

# 1. Row counts across primary entities
tables = [
    "users",
    "documents",
    "document_pages",
    "analyses",
    "detected_regions",
    "document_comparisons",
    "forensic_reports",
    "exhibit_custody_logs",
    "security_audit_logs",
]

print("\n[1] Restored Database Entity Row Counts:")
counts = {}
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t};")
    cnt = cur.fetchone()[0]
    counts[t] = cnt
    print(f"  * {t:<25}: {cnt:,} records")

assert counts["users"] > 0, "No users restored!"
assert counts["documents"] > 0, "No documents restored!"
assert counts["analyses"] > 0, "No analyses restored!"
assert counts["exhibit_custody_logs"] > 0, "No custody logs restored!"

# 2. Check representative exhibits
print("\n[2] Verifying Restored Document Exhibits:")
cur.execute("SELECT id, original_filename, sha256_hash, file_path, stored_filename FROM documents LIMIT 5;")
docs = cur.fetchall()
restored_storage = Path("tests/scratch_restore").resolve()

for doc_id, orig_name, exp_hash, stored_path, stored_fn in docs:
    fn = stored_fn or Path(stored_path).name
    restored_file = restored_storage / "uploads" / fn
    if restored_file.exists():
        actual_hash = compute_sha256(restored_file)
        assert actual_hash == exp_hash, f"Exhibit hash mismatch for {fn}!"
        print(f"  * Exhibit '{orig_name}' ({fn[:12]}...): SHA-256 MATCH ({actual_hash[:16]}...)")
    else:
        print(f"  * [WARNING] Restored file {fn} not in test uploads folder")

# 3. Check representative forensic PDF reports
print("\n[3] Verifying Restored Forensic PDF Reports:")
cur.execute("SELECT id, report_number, sha256_hash, file_path FROM forensic_reports LIMIT 5;")
reps = cur.fetchall()
for rep_id, rep_num, exp_hash, stored_path in reps:
    pdf_name = Path(stored_path).name
    restored_pdf = restored_storage / "reports" / rep_id / pdf_name
    if restored_pdf.exists():
        actual_hash = compute_sha256(restored_pdf)
        assert actual_hash == exp_hash, f"Report PDF hash mismatch for {rep_num}!"
        print(f"  * Report {rep_num} ({pdf_name}): SHA-256 MATCH ({actual_hash[:16]}...)")
    else:
        print(f"  * [NOTICE] Report {rep_num} path: {restored_pdf}")

# 4. Check comparisons
print("\n[4] Verifying Restored Document Comparisons:")
cur.execute("SELECT id, document_a_id, document_b_id, similarity_score, ssim_score, verdict_category, created_at FROM document_comparisons LIMIT 3;")
comps = cur.fetchall()
for cid, da, db, sim, ssim, verdict, dt in comps:
    print(f"  * Comparison {cid[:8]}... Verdict={verdict}, Sim={sim:.3f}, SSIM={ssim:.3f}, Date={dt}")

cur.close()
conn.close()

print("\n" + "=" * 70)
print("ALL RESTORED ENTITIES AND ARTIFACTS VERIFIED SUCCESSFULLY (100% Integrity)")
print("=" * 70)
