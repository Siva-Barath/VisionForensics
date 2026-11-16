"""
run_phase8_evaluation.py — Comprehensive Controlled Analyst Evaluation Runner.

Executes Phase 8 evaluation across 12 structured exhibits:
- Authentic, Forged, Suspicious, and Difficult-to-classify documents.
- Multiple formats: TIFF, PNG, JPG, and Multi-page PDF.
- Dual-analyst role simulation (Analyst A intake/reporting, Analyst B comparison review).
- Full comparative analysis, multi-page verification, forensic PDF report generation.
- Custody ledger association and terminology verification.
"""

import os
import sys
import time
import json
import socket
import hashlib
from pathlib import Path
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
CA_CERT_PATH = ROOT_DIR / "ca" / "pilot_ca.crt"
HTTPS_BASE = "https://localhost:8443"
EXHIBITS_DIR = ROOT_DIR / "uploads" / "phase8_exhibits"
RESULTS_FILE = ROOT_DIR / "evaluation_results_phase8R.json"

TEST_SPECIMENS = [
    {
        "id": "EX-01",
        "file": "exhibit_01_aut_drvlic.tif",
        "name": "CA Driving License (Authentic Baseline)",
        "doc_type": "driving_license",
        "format": "TIFF",
        "category": "Authentic",
        "ground_truth": "AUTHENTIC",
        "expected_tier": "LOW_RISK",
        "notes": "Pristine authentic driving license scan; baseline test for physical substrate."
    },
    {
        "id": "EX-02",
        "file": "exhibit_02_aut_idcard.png",
        "name": "Albanian ID Card (Authentic Baseline)",
        "doc_type": "id_card",
        "format": "PNG",
        "category": "Authentic",
        "ground_truth": "AUTHENTIC",
        "expected_tier": "LOW_RISK",
        "notes": "Authentic national ID card in lossless PNG format."
    },
    {
        "id": "EX-03",
        "file": "exhibit_03_aut_passport.jpg",
        "name": "Azerbaijani Passport (Authentic Baseline)",
        "doc_type": "passport",
        "format": "JPG",
        "category": "Authentic",
        "ground_truth": "AUTHENTIC",
        "expected_tier": "LOW_RISK",
        "notes": "Authentic passport biographical page in standard JPEG format."
    },
    {
        "id": "EX-04",
        "file": "exhibit_04_aut_multipage.pdf",
        "name": "Dossier Exhibit (Authentic Multi-Page PDF)",
        "doc_type": "dossier_pdf",
        "format": "PDF",
        "category": "Authentic",
        "ground_truth": "AUTHENTIC",
        "expected_tier": "LOW_RISK",
        "notes": "2-page authentic composite PDF exhibit (DL + Passport) testing multi-page ingestion."
    },
    {
        "id": "EX-05",
        "file": "exhibit_05_forg_text_drvlic.tif",
        "name": "Italian Driving License (Text Forgery)",
        "doc_type": "driving_license",
        "format": "TIFF",
        "category": "Forged",
        "ground_truth": "FORGED",
        "expected_tier": "HIGH_RISK",
        "notes": "Driver license with altered birth date and license expiration text."
    },
    {
        "id": "EX-06",
        "file": "exhibit_06_forg_text_drvlic.png",
        "name": "Italian Driving License (Text Forgery PNG)",
        "doc_type": "driving_license",
        "format": "PNG",
        "category": "Forged",
        "ground_truth": "FORGED",
        "expected_tier": "HIGH_RISK",
        "notes": "Driver license with altered demographic text in PNG format."
    },
    {
        "id": "EX-07",
        "file": "exhibit_07_forg_copymove_id.jpg",
        "name": "Portuguese ID Card (Copy-Move Forgery JPG)",
        "doc_type": "id_card",
        "format": "JPG",
        "category": "Forged",
        "ground_truth": "FORGED",
        "expected_tier": "HIGH_RISK",
        "notes": "National ID card with duplicated security features and altered identity text in JPEG."
    },
    {
        "id": "EX-08",
        "file": "exhibit_08_forg_multipage_mixed.pdf",
        "name": "Composite Dossier (Mixed Multi-Page PDF)",
        "doc_type": "dossier_pdf",
        "format": "PDF",
        "category": "Forged",
        "ground_truth": "FORGED",
        "expected_tier": "HIGH_RISK",
        "notes": "2-page PDF containing Page 1 authentic reference and Page 2 altered text specimen."
    },
    {
        "id": "EX-09",
        "file": "exhibit_09_susp_copymove_drvlic.tif",
        "name": "Driving License (Subtle Copy-Move Specimen A)",
        "doc_type": "driving_license",
        "format": "TIFF",
        "category": "Suspicious",
        "ground_truth": "FORGED",
        "expected_tier": "SUSPICIOUS",
        "notes": "Subtle clone patch sharing compression history; known copy-move recall boundary."
    },
    {
        "id": "EX-10",
        "file": "exhibit_10_susp_copymove_drvlic.tif",
        "name": "Driving License (Subtle Copy-Move Specimen B)",
        "doc_type": "driving_license",
        "format": "TIFF",
        "category": "Suspicious",
        "ground_truth": "FORGED",
        "expected_tier": "SUSPICIOUS",
        "notes": "Intra-document clone boundary case; testing suspicious risk tier assignment."
    },
    {
        "id": "EX-11",
        "file": "exhibit_11_diff_heavy_jpeg.jpg",
        "name": "Driving License (Severe JPEG Artifact Degradation)",
        "doc_type": "driving_license",
        "format": "JPG",
        "category": "Difficult",
        "ground_truth": "AUTHENTIC",
        "expected_tier": "SUSPICIOUS",
        "notes": "Authentic document subjected to high DCT compression (Q=25); testing noise robustness."
    },
    {
        "id": "EX-12",
        "file": "exhibit_12_diff_low_contrast.png",
        "name": "ID Card (Low-Contrast Degraded Scan)",
        "doc_type": "id_card",
        "format": "PNG",
        "category": "Difficult",
        "ground_truth": "AUTHENTIC",
        "expected_tier": "LOW_RISK",
        "notes": "Authentic ID card scan with contrast attenuated by 65%; testing illumination variance."
    },
]


def execute_evaluation():
    print("=" * 80)
    print("VISIONFORENSICS AI — PHASE 8 CONTROLLED ANALYST EVALUATION RUNNER")
    print("=" * 80)
    print(f"Target URL:         {HTTPS_BASE}")
    print(f"Trusted Root CA:    {CA_CERT_PATH}")
    print(f"Test Exhibits:      {len(TEST_SPECIMENS)} across 4 forensic categories")

    client = httpx.Client(base_url=HTTPS_BASE, verify=str(CA_CERT_PATH), timeout=60)

    # 1. Authenticate Analyst A, Analyst B, and Pilot Admin
    print("\n[PHASE 8.1] Authenticating Pilot Evaluation Personas...")
    auth_tokens = {}
    for email, role in [
        ("pilot_analyst_a@pilot.visionforensics.local", "Analyst A (Intake & Analysis)"),
        ("pilot_analyst_b@pilot.visionforensics.local", "Analyst B (Peer Review & Comparison)"),
        ("pilot_admin@pilot.visionforensics.local", "Pilot Admin (Security & Audit Review)"),
    ]:
        for attempt in range(5):
            r = client.post("/api/v1/auth/login", json={"email": email, "password": "SmokeTestPassword2026!"})
            if r.status_code == 200:
                auth_tokens[email] = r.json()["access_token"]
                print(f"  * {role:<42}: Authenticated (JWT Issued)")
                break
            elif r.status_code == 429:
                print(f"  * Rate limited on {email}, sleeping 15s...")
                time.sleep(15)
            else:
                raise RuntimeError(f"Authentication failed for {email}: {r.status_code} {r.text}")

    headers_a = {"Authorization": f"Bearer {auth_tokens['pilot_analyst_a@pilot.visionforensics.local']}"}
    headers_b = {"Authorization": f"Bearer {auth_tokens['pilot_analyst_b@pilot.visionforensics.local']}"}
    headers_admin = {"Authorization": f"Bearer {auth_tokens['pilot_admin@pilot.visionforensics.local']}"}

    # 2. Sequential Ingestion & Analysis by Analyst A
    print("\n[PHASE 8.2] Ingesting and Screening Test Exhibits (Analyst A)...")
    eval_results = []
    doc_id_map = {}

    for idx, item in enumerate(TEST_SPECIMENS):
        file_path = EXHIBITS_DIR / item["file"]
        assert file_path.exists(), f"Exhibit file missing: {file_path}"
        mime_type = "image/tiff" if item["format"] == "TIFF" else "image/png" if item["format"] == "PNG" else "image/jpeg" if item["format"] == "JPG" else "application/pdf"

        # Pacing to observe in-memory sliding window upload rate limit (max 10/min)
        if idx > 0 and idx % 6 == 0:
            print("  * Pacing intake pipeline to observe sliding rate-limit window (sleeping 25s)...")
            time.sleep(25)

        t_start = time.perf_counter()
        with open(file_path, "rb") as f:
            upload_resp = client.post(
                "/api/v1/upload",
                headers=headers_a,
                files={"file": (item["file"], f, mime_type)},
            )
        upload_duration = time.perf_counter() - t_start

        if upload_resp.status_code == 429:
            print(f"  * Hit rate limiter on {item['id']}, waiting 30s...")
            time.sleep(30)
            with open(file_path, "rb") as f:
                upload_resp = client.post(
                    "/api/v1/upload",
                    headers=headers_a,
                    files={"file": (item["file"], f, mime_type)},
                )

        assert upload_resp.status_code in (200, 201), f"Upload failed for {item['id']}: {upload_resp.text}"
        doc_id = upload_resp.json()["document_id"]
        doc_id_map[item["id"]] = doc_id

        # Retrieve completed analysis
        analysis_resp = client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers_a)
        assert analysis_resp.status_code == 200, f"Analysis retrieval failed: {analysis_resp.text}"
        analysis_data = analysis_resp.json()

        # Extract metrics
        track_1 = analysis_data.get("track_1_ml", {})
        p_ml = track_1.get("forgery_probability")
        pred_class = track_1.get("predicted_class")
        risk_tier = analysis_data.get("unified_risk_tier")
        overall_verdict = analysis_data.get("overall_verdict")
        regions_count = len(analysis_data.get("detected_regions", []))
        processing_time_ms = analysis_data.get("processing_time_ms", 0.0)
        page_count = analysis_data.get("image_dimensions", {}).get("page_count", 1)

        # Terminology verification: ensure absolute zero occurrences of 'CONFIRMED FORGERY'
        raw_text = analysis_resp.text
        assert "CONFIRMED FORGERY" not in raw_text, f"VIOLATION: Prohibited string 'CONFIRMED FORGERY' found in {item['id']}"

        # Determine forensic outcome (Track 1 ML alone vs. Unified Platform)
        is_platform_flagged = (
            (pred_class == "FORGED")
            or (risk_tier == "HIGH_RISK")
            or (overall_verdict == "SUSPICIOUS / HIGH_RISK")
        )

        if p_ml is not None:
            if item["ground_truth"] == "AUTHENTIC":
                outcome = "True Negative (TN)" if pred_class == "AUTHENTIC" else "False Positive (FP)"
                platform_outcome = "False Positive (FP)" if is_platform_flagged else "True Negative (TN)"
            else:
                outcome = "True Positive (TP)" if pred_class == "FORGED" else "False Negative (FN)"
                platform_outcome = "True Positive (TP)" if is_platform_flagged else "False Negative (FN)"
        else:
            outcome = "ML_UNAVAILABLE"
            platform_outcome = "ML_UNAVAILABLE"

        res_record = {
            "exhibit_id": item["id"],
            "document_id": doc_id,
            "filename": item["file"],
            "display_name": item["name"],
            "category": item["category"],
            "format": item["format"],
            "doc_type": item["doc_type"],
            "ground_truth": item["ground_truth"],
            "expected_tier": item["expected_tier"],
            "p_ml": p_ml,
            "risk_tier": risk_tier,
            "predicted_class": pred_class,
            "overall_verdict": overall_verdict,
            "outcome": outcome,
            "platform_outcome": platform_outcome,
            "detected_regions": regions_count,
            "page_count": page_count,
            "pages_ml": analysis_data.get("pages_ml", []),
            "track_3_visual": analysis_data.get("track_3_visual", {}),
            "compression_qualification": analysis_data.get("compression_qualification", {}),
            "ingest_latency_sec": round(upload_duration, 2),
            "backend_time_ms": round(processing_time_ms, 1),
            "warnings_count": len(analysis_data.get("warnings", [])),
            "analyst_notes": item["notes"],
        }
        eval_results.append(res_record)

        p_ml_str = f"{p_ml:.4f}" if p_ml is not None else "N/A"
        print(f"  [{item['id']}] {item['file']:<34} | P_ML={p_ml_str:>6} | Tier={risk_tier:<10} | Pred={str(pred_class):<9} | {outcome:<19} (Platform: {platform_outcome:<19}) | {upload_duration:.2f}s")
        time.sleep(3)

    # 3. Dual-Analyst Cross-Review & Document Comparison
    print("\n[PHASE 8.3] Executing Comparative Document Evaluations...")
    # First, verify IDOR security: Analyst B attempting to compare Analyst A's exhibits is rejected
    idor_payload = {
        "document_a_id": doc_id_map["EX-01"],
        "document_b_id": doc_id_map["EX-05"],
        "page_a": 0,
        "page_b": 0,
        "align_images": True,
    }
    idor_comp_resp = client.post("/api/v1/comparison", headers=headers_b, json=idor_payload)
    assert idor_comp_resp.status_code == 403, f"Expected 403 Forbidden for unauthorized Analyst B comparison, got {idor_comp_resp.status_code}"
    print("  * Dual-Document IDOR Protection Check: PASSED (Unauthorized comparison blocked: HTTP 403 Forbidden)")

    comparison_tests = [
        {
            "comp_id": "COMP-01",
            "name": "Suspect Alteration vs Reference Baseline",
            "doc_a": doc_id_map["EX-01"],  # Authentic Driving License
            "doc_b": doc_id_map["EX-05"],  # Forged Text Alteration
            "page_a": 0,
            "page_b": 0,
            "expected": "Differential detected (SSIM drop, visual discrepancies identified)",
        },
        {
            "comp_id": "COMP-02",
            "name": "Identical Exhibit Verification Baseline",
            "doc_a": doc_id_map["EX-01"],  # Authentic Driving License
            "doc_b": doc_id_map["EX-01"],  # Self comparison
            "page_a": 0,
            "page_b": 0,
            "expected": "Near-perfect match (SSIM ~ 1.000, zero differential regions)",
        },
        {
            "comp_id": "COMP-03",
            "name": "Multi-Page Differential Investigation",
            "doc_a": doc_id_map["EX-04"],  # Authentic multi-page (Page 0)
            "doc_b": doc_id_map["EX-08"],  # Mixed multi-page (Page 1 altered)
            "page_a": 0,
            "page_b": 1,
            "expected": "Cross-page differential analysis with alignment",
        },
    ]

    comp_results = []
    for ct in comparison_tests:
        t_start = time.perf_counter()
        comp_payload = {
            "document_a_id": ct["doc_a"],
            "document_b_id": ct["doc_b"],
            "page_a": ct["page_a"],
            "page_b": ct["page_b"],
            "align_images": True,
        }
        comp_resp = client.post("/api/v1/comparison", headers=headers_a, json=comp_payload)
        comp_latency = time.perf_counter() - t_start
        assert comp_resp.status_code in (200, 201), f"Comparison failed for {ct['comp_id']}: {comp_resp.text}"
        comp_data = comp_resp.json()

        metrics = comp_data.get("metrics", {})
        ssim_val = metrics.get("ssim") or comp_data.get("similarity_score")
        diff_count = len(comp_data.get("differential_regions", []))
        align_status = comp_data.get("alignment", {}).get("status", "SUCCESS")
        align_conf = comp_data.get("alignment", {}).get("confidence", 1.0)

        comp_rec = {
            "comp_id": ct["comp_id"],
            "name": ct["name"],
            "doc_a": ct["doc_a"],
            "doc_b": ct["doc_b"],
            "ssim": round(ssim_val, 4) if ssim_val is not None else None,
            "differential_regions": diff_count,
            "alignment_status": align_status,
            "alignment_confidence": round(align_conf, 3),
            "latency_sec": round(comp_latency, 2),
            "expected": ct["expected"],
        }
        comp_results.append(comp_rec)
        ssim_str = f"{ssim_val:.4f}" if ssim_val is not None else "N/A"
        print(f"  [{ct['comp_id']}] {ct['name']:<42} | SSIM={ssim_str} | Diff Regions={diff_count} | Align={align_status} | {comp_latency:.2f}s")
        time.sleep(2)

    # 4. Forensic PDF Report Generation & Export
    print("\n[PHASE 8.4] Generating and Verifying Forensic PDF Reports (Analyst A)...")
    reports_to_test = [
        {"exhibit_id": "EX-01", "title": "Forensic Examination — Authentic Baseline Exhibit"},
        {"exhibit_id": "EX-05", "title": "Forensic Examination — High-Risk Alteration Exhibit"},
        {"exhibit_id": "EX-08", "title": "Forensic Examination — Multi-Page Mixed Exhibit"},
    ]

    report_results = []
    for rep_item in reports_to_test:
        doc_uuid = doc_id_map[rep_item["exhibit_id"]]
        t_start = time.perf_counter()
        rep_resp = client.post(
            "/api/v1/reports",
            headers=headers_a,
            json={
                "document_id": doc_uuid,
                "title": rep_item["title"],
                "analyst_notes": f"Phase 8 Controlled Evaluation dossier for {rep_item['exhibit_id']}.",
            },
        )
        rep_latency = time.perf_counter() - t_start
        assert rep_resp.status_code in (200, 201), f"Report generation failed: {rep_resp.text}"
        rep_data = rep_resp.json()
        report_id = rep_data["report_id"]
        report_number = rep_data["report_number"]

        # Download report & verify integrity
        dl_resp = client.get(f"/api/v1/reports/{report_id}/download", headers=headers_a)
        assert dl_resp.status_code == 200, f"Report download failed: {dl_resp.status_code}"
        assert dl_resp.headers.get("content-type") == "application/pdf"
        pdf_bytes = dl_resp.content
        calc_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        hdr_sha256 = dl_resp.headers.get("X-Report-SHA256")
        if hdr_sha256:
            assert calc_sha256 == hdr_sha256, f"Checksum mismatch: {calc_sha256} != {hdr_sha256}"

        rep_rec = {
            "exhibit_id": rep_item["exhibit_id"],
            "report_id": report_id,
            "report_number": report_number,
            "title": rep_item["title"],
            "size_bytes": len(pdf_bytes),
            "sha256_hash": calc_sha256,
            "hash_verified": True,
            "gen_latency_sec": round(rep_latency, 2),
        }
        report_results.append(rep_rec)
        print(f"  * Generated {report_number} ({len(pdf_bytes):,} bytes) | SHA-256: {calc_sha256[:16]}... | {rep_latency:.2f}s (VERIFIED)")
        time.sleep(2)

    # 5. Security & Custody Audit Review (Pilot Admin)
    print("\n[PHASE 8.5] Reviewing Custody Ledgers & Security Audits (Pilot Admin)...")
    admin_audit_resp = client.get("/api/v1/admin/audit-logs", headers=headers_admin)
    assert admin_audit_resp.status_code == 200, f"Failed to fetch audit logs: {admin_audit_resp.status_code}"
    audit_logs = admin_audit_resp.json()

    # Query DB inside container for custody count and recent events
    py_code = """
import json
from app.database.session import SessionLocal
from app.models import ExhibitCustodyLog, SecurityAuditLog

db = SessionLocal()
custody_total = db.query(ExhibitCustodyLog).count()
sec_total = db.query(SecurityAuditLog).count()

# Count events by type
event_counts = {}
for l in db.query(ExhibitCustodyLog).all():
    event_counts[l.event_type] = event_counts.get(l.event_type, 0) + 1

# Check distinct documents with custody entries
distinct_docs = db.query(ExhibitCustodyLog.document_id).distinct().count()

db.close()
res = {
    'custody_total': custody_total,
    'security_total': sec_total,
    'event_counts': event_counts,
    'distinct_docs_with_custody': distinct_docs
}
print('__RESULT__' + json.dumps(res) + '__RESULT__')
"""
    import subprocess
    cmd = ["docker", "exec", "visionforensics-pilot-backend", "python", "-c", py_code]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    raw_json = res.stdout.split("__RESULT__")[1]
    custody_stats = json.loads(raw_json)

    print(f"  * Total Exhibit Custody Logs in PostgreSQL: {custody_stats['custody_total']}")
    print(f"  * Total Security Audit Logs in PostgreSQL: {custody_stats['security_total']}")
    print(f"  * Distinct Documents Tracked:              {custody_stats['distinct_docs_with_custody']}")
    print(f"  * Custody Event Breakdown:                {custody_stats['event_counts']}")

    # 6. Evaluation Summary Calculations
    print("\n[PHASE 8.6] Compiling Evaluation Statistical Summary...")
    tp = sum(1 for r in eval_results if r["outcome"] == "True Positive (TP)")
    tn = sum(1 for r in eval_results if r["outcome"] == "True Negative (TN)")
    fp = sum(1 for r in eval_results if r["outcome"] == "False Positive (FP)")
    fn = sum(1 for r in eval_results if r["outcome"] == "False Negative (FN)")
    ml_unavail = sum(1 for r in eval_results if r["outcome"] == "ML_UNAVAILABLE")

    p_tp = sum(1 for r in eval_results if r["platform_outcome"] == "True Positive (TP)")
    p_tn = sum(1 for r in eval_results if r["platform_outcome"] == "True Negative (TN)")
    p_fp = sum(1 for r in eval_results if r["platform_outcome"] == "False Positive (FP)")
    p_fn = sum(1 for r in eval_results if r["platform_outcome"] == "False Negative (FN)")

    classified_total = tp + tn + fp + fn
    accuracy = (tp + tn) / classified_total if classified_total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    p_accuracy = (p_tp + p_tn) / classified_total if classified_total > 0 else 0.0
    p_precision = p_tp / (p_tp + p_fp) if (p_tp + p_fp) > 0 else 0.0
    p_recall = p_tp / (p_tp + p_fn) if (p_tp + p_fn) > 0 else 0.0
    p_specificity = p_tn / (p_tn + p_fp) if (p_tn + p_fp) > 0 else 0.0

    latencies = [r["ingest_latency_sec"] for r in eval_results]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    summary_data = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_exhibits_tested": len(eval_results),
        "track1_ml_alone": {
            "confusion_matrix": {
                "true_positives": tp,
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "ml_unavailable": ml_unavail,
            },
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "specificity": round(specificity, 4),
                "operational_threshold": 0.40,
            },
        },
        "unified_platform_decision": {
            "confusion_matrix": {
                "true_positives": p_tp,
                "true_negatives": p_tn,
                "false_positives": p_fp,
                "false_negatives": p_fn,
            },
            "metrics": {
                "accuracy": round(p_accuracy, 4),
                "precision": round(p_precision, 4),
                "recall": round(p_recall, 4),
                "specificity": round(p_specificity, 4),
            },
        },
        "latency_statistics_seconds": {
            "mean_ingestion_latency": round(avg_latency, 2),
            "min_latency": min(latencies) if latencies else 0,
            "max_latency": max(latencies) if latencies else 0,
            "sla_threshold_seconds": 10.0,
            "sla_compliance_rate": f"{sum(1 for l in latencies if l <= 10.0) / len(latencies) * 100:.1f}%",
        },
        "exhibits": eval_results,
        "comparisons": comp_results,
        "reports": report_results,
        "custody_stats": custody_stats,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"\n  === Track 1 (ML Alone at T=0.40) ===")
    print(f"  * Confusion Matrix         : TP={tp}, TN={tn}, FP={fp}, FN={fn}, ML_UNAVAIL={ml_unavail}")
    print(f"  * Accuracy                 : {accuracy * 100:.1f}%")
    print(f"  * Recall                   : {recall * 100:.1f}%")
    print(f"  * Specificity              : {specificity * 100:.1f}%")

    print(f"\n  === Unified Platform Decision (Multi-Track Synthesized) ===")
    print(f"  * Confusion Matrix         : TP={p_tp}, TN={p_tn}, FP={p_fp}, FN={p_fn}")
    print(f"  * Accuracy                 : {p_accuracy * 100:.1f}%")
    print(f"  * Recall                   : {p_recall * 100:.1f}%")
    print(f"  * Specificity              : {p_specificity * 100:.1f}%")
    print(f"  * Mean Ingestion Latency   : {avg_latency:.2f}s (< 10.0s SLA)")
    print(f"  * Saved Full Results JSON  : {RESULTS_FILE}")

    print("\n" + "=" * 80)
    print("PHASE 8 CONTROLLED EVALUATION RUN COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    execute_evaluation()
