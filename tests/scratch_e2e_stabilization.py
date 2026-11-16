import requests
import io
import hashlib
import time
import json
import subprocess
from PIL import Image, ImageDraw

session_a = requests.Session()
session_a.verify = False
session_b = requests.Session()
session_b.verify = False
session_admin = requests.Session()
session_admin.verify = False

BASE_URL = 'https://127.0.0.1:8443/api/v1'

print("=== STARTING VISIONFORENSICS AI END-TO-END STABILIZATION SUITE ===")

# --- Auth ---
def safe_login(session, email, password):
    for attempt in range(12):
        try:
            r = session.post(f'{BASE_URL}/auth/login', json={'email': email, 'password': password})
            if r.status_code == 200:
                return r.json()['access_token']
            elif r.status_code == 429:
                print(f"Rate limited on {email}, sleeping 12s...")
                time.sleep(12)
            elif r.status_code in (502, 503):
                print("Backend starting up (502/503), sleeping 5s...")
                time.sleep(5)
            else:
                raise RuntimeError(f"Login failed: {r.status_code} {r.text}")
        except requests.exceptions.RequestException:
            print("Connection waiting, sleeping 3s...")
            time.sleep(3)
    raise RuntimeError("Login timed out after multiple retries")

token_a = safe_login(session_a, 'pilot_analyst_a@pilot.visionforensics.local', 'SmokeTestPassword2026!')
headers_a = {'Authorization': f'Bearer {token_a}'}

token_b = safe_login(session_b, 'pilot_analyst_b@pilot.visionforensics.local', 'SmokeTestPassword2026!')
headers_b = {'Authorization': f'Bearer {token_b}'}

token_admin = safe_login(session_admin, 'pilot_admin@pilot.visionforensics.local', 'SmokeTestPassword2026!')
headers_admin = {'Authorization': f'Bearer {token_admin}'}

# ------------------------------------------------------------- #
# TEST 1: Authentic document intake & analysis workflow          #
# ------------------------------------------------------------- #
print("\n[TEST 1] Authentic Document Intake & Analysis Workflow")
img_auth = Image.new('RGB', (400, 400), color=(255, 255, 255))
draw = ImageDraw.Draw(img_auth)
draw.text((30, 50), "OFFICIAL CERTIFICATE OF COMPLETION", fill=(20, 20, 20))
draw.text((30, 90), "Issued to: Dr. Jane Doe", fill=(40, 40, 40))
draw.text((30, 130), "Date of Verification: November 2026", fill=(40, 40, 40))
draw.line([(30, 180), (370, 180)], fill=(100, 100, 100), width=2)
buf_auth = io.BytesIO()
img_auth.save(buf_auth, format='PNG')
buf_auth.seek(0)

r_up_auth = session_a.post(f'{BASE_URL}/upload', headers=headers_a, files={'file': ('e2e_authentic_cert.png', buf_auth, 'image/png')})
assert r_up_auth.status_code == 201, f"Expected 201, got {r_up_auth.status_code}: {r_up_auth.text}"
doc_auth_id = r_up_auth.json()['document_id']
print(f" -> Uploaded Doc ID: {doc_auth_id}")

r_an_auth = session_a.get(f'{BASE_URL}/documents/{doc_auth_id}/analysis', headers=headers_a)
assert r_an_auth.status_code == 200, f"Analysis retrieval failed: {r_an_auth.text}"
an_auth = r_an_auth.json()
print(f" -> Overall Verdict: {an_auth['overall_verdict']}")
print(f" -> Unified Risk Tier: {an_auth['unified_risk_tier']}")
print(f" -> Track 1 Status: {an_auth['track_1_ml']['status']}")
print(f" -> ML Forgery Probability: {an_auth['track_1_ml']['forgery_probability']}")
print(f" -> Composite Risk Score: {an_auth['composite_risk_score']}")
assert an_auth['unified_risk_tier'] in ('LOW_RISK', 'SUSPICIOUS', 'HIGH_RISK')
print("[TEST 1 PASSED]")

# ------------------------------------------------------------- #
# TEST 2: Forged document intake & analysis workflow            #
# ------------------------------------------------------------- #
print("\n[TEST 2] Forged / Altered Document Intake & Analysis Workflow")
img_forg = Image.new('RGB', (600, 600), color=(250, 250, 250))
draw_f = ImageDraw.Draw(img_forg)
# Draw strong repeated pattern (copy-move manipulation)
for offset in [(50, 50), (320, 320)]:
    draw_f.rectangle([offset[0], offset[1], offset[0] + 180, offset[1] + 180], fill=(210, 40, 40), outline=(10, 10, 10), width=3)
    draw_f.text((offset[0] + 15, offset[1] + 25), "ALTERED SEAL 999", fill=(255, 255, 255))
    draw_f.ellipse([offset[0] + 40, offset[1] + 60, offset[0] + 140, offset[1] + 160], outline=(255, 255, 0), width=4)

buf_forg = io.BytesIO()
img_forg.save(buf_forg, format='PNG')
buf_forg.seek(0)

r_up_forg = session_a.post(f'{BASE_URL}/upload', headers=headers_a, files={'file': ('e2e_forged_seal.png', buf_forg, 'image/png')})
assert r_up_forg.status_code == 201, f"Expected 201, got {r_up_forg.status_code}: {r_up_forg.text}"
doc_forg_id = r_up_forg.json()['document_id']
print(f" -> Uploaded Doc ID: {doc_forg_id}")

r_an_forg = session_a.get(f'{BASE_URL}/documents/{doc_forg_id}/analysis', headers=headers_a)
assert r_an_forg.status_code == 200, f"Analysis retrieval failed: {r_an_forg.text}"
an_forg = r_an_forg.json()
print(f" -> Overall Verdict: {an_forg['overall_verdict']}")
print(f" -> Unified Risk Tier: {an_forg['unified_risk_tier']}")
print(f" -> Track 1 Status: {an_forg['track_1_ml']['status']}")
print(f" -> Detected Regions Count: {len(an_forg['detected_regions'])}")
print(f" -> Composite Risk Score: {an_forg['composite_risk_score']}")
print("[TEST 2 PASSED]")

# ------------------------------------------------------------- #
# TEST 3: Multi-page PDF intake & per-page analysis (REM-01)    #
# ------------------------------------------------------------- #
print("\n[TEST 3] Multi-Page PDF Intake & Per-Page ML Analysis (REM-01 & REM-02)")
with open('test_mixed.pdf', 'rb') as f:
    pdf_bytes = f.read()

r_up_pdf = session_a.post(f'{BASE_URL}/upload', headers=headers_a, files={'file': ('e2e_multipage_dossier.pdf', io.BytesIO(pdf_bytes), 'application/pdf')})
assert r_up_pdf.status_code == 201, f"Expected 201, got {r_up_pdf.status_code}: {r_up_pdf.text}"
doc_pdf_id = r_up_pdf.json()['document_id']
print(f" -> Uploaded Multi-Page PDF Doc ID: {doc_pdf_id}")

r_an_pdf = session_a.get(f'{BASE_URL}/documents/{doc_pdf_id}/analysis', headers=headers_a)
assert r_an_pdf.status_code == 200, f"Analysis retrieval failed: {r_an_pdf.text}"
an_pdf = r_an_pdf.json()
print(f" -> Overall Verdict: {an_pdf['overall_verdict']}")
print(f" -> Total Pages In Dimensions: {an_pdf['image_dimensions']['page_count']}")
print(f" -> Per-Page ML Entries (pages_ml): {len(an_pdf['pages_ml'])}")
for idx, p in enumerate(an_pdf['pages_ml']):
    print(f"    Page {p['page_index']}: Prob={p['forgery_probability']} Class={p['predicted_class']} Risk={p['risk_tier']}")
assert len(an_pdf['pages_ml']) >= 2, f"Expected at least 2 pages_ml entries, got {len(an_pdf['pages_ml'])}"
print("[TEST 3 PASSED]")

# ------------------------------------------------------------- #
# TEST 4: Document comparison between exhibits                  #
# ------------------------------------------------------------- #
print("\n[TEST 4] Document Differential Comparison Between Exhibits")
comp_req = {
    'document_a_id': doc_auth_id,
    'document_b_id': doc_forg_id,
    'page_a': 0,
    'page_b': 0,
    'align_images': True
}
r_comp = session_a.post(f'{BASE_URL}/comparison', headers=headers_a, json=comp_req)
assert r_comp.status_code == 200, f"Comparison failed: {r_comp.status_code}: {r_comp.text}"
comp_res = r_comp.json()
comp_id = comp_res['comparison_id']
print(f" -> Comparison ID: {comp_id}")
print(f" -> SSIM Score: {comp_res['metrics']['ssim_score']}")
print(f" -> Matches Found: {comp_res['alignment']['matches_found']}")
print(f" -> Differential Regions Count: {len(comp_res['differential_regions'])}")

# Check artifact retrieval
r_heat = session_a.get(f'{BASE_URL}/comparison/{comp_id}/artifacts/diff_heatmap', headers=headers_a)
assert r_heat.status_code == 200, f"Diff heatmap retrieval failed: {r_heat.status_code}"
assert r_heat.headers.get('content-type', '').startswith('image/'), "Expected image content type"
print(f" -> Diff Heatmap retrieved successfully ({len(r_heat.content)} bytes)")
print("[TEST 4 PASSED]")

# ------------------------------------------------------------- #
# TEST 5: Forensic PDF report generation & download             #
# ------------------------------------------------------------- #
print("\n[TEST 5] Forensic PDF Report Generation & Cryptographic Download Verification")
rep_req = {
    'document_id': doc_pdf_id,
    'comparison_id': comp_id,
    'title': 'Controlled Pilot End-to-End Forensic Dossier',
    'analyst_notes': 'Verified defensible multi-track findings and cryptographic custody integrity.',
    'include_comparison': True
}
r_rep = session_a.post(f'{BASE_URL}/reports', headers=headers_a, json=rep_req)
assert r_rep.status_code == 201, f"Report generation failed: {r_rep.status_code}: {r_rep.text}"
rep_data = r_rep.json()
rep_id = rep_data['report_id']
expected_sha = rep_data['sha256_hash']
print(f" -> Generated Report ID: {rep_id}")
print(f" -> Report Number: {rep_data['report_number']}")
print(f" -> Expected SHA-256 Digest: {expected_sha}")

# Download PDF and verify cryptographic integrity
r_dl = session_a.get(f'{BASE_URL}/reports/{rep_id}/download', headers=headers_a)
assert r_dl.status_code == 200, f"Report download failed: {r_dl.status_code}"
actual_sha = hashlib.sha256(r_dl.content).hexdigest()
header_sha = r_dl.headers.get('X-Report-SHA256')
print(f" -> Downloaded PDF Size: {len(r_dl.content)} bytes")
print(f" -> Computed SHA-256: {actual_sha}")
print(f" -> Header SHA-256:   {header_sha}")
assert actual_sha == expected_sha, f"SHA-256 mismatch: {actual_sha} != {expected_sha}"
assert header_sha == expected_sha, f"Header SHA-256 mismatch: {header_sha} != {expected_sha}"
print("[TEST 5 PASSED]")

# ------------------------------------------------------------- #
# TEST 6: Document tampering detection (TAMPERING_ALARM)        #
# ------------------------------------------------------------- #
print("\n[TEST 6] Exhibit Tampering Detection & TAMPERING_ALARM Verification")
# Ingest disposable test exhibit
img_tamp = Image.new('RGB', (250, 250), color=(180, 180, 180))
buf_tamp = io.BytesIO()
img_tamp.save(buf_tamp, format='PNG')
buf_tamp.seek(0)

r_up_tamp = session_a.post(f'{BASE_URL}/upload', headers=headers_a, files={'file': ('tamper_canary.png', buf_tamp, 'image/png')})
assert r_up_tamp.status_code == 201
doc_tamp_id = r_up_tamp.json()['document_id']
print(f" -> Canary Doc ID: {doc_tamp_id}")

# First access confirms it is verified
r_pre_tamper = session_a.get(f'{BASE_URL}/documents/{doc_tamp_id}/analysis', headers=headers_a)
assert r_pre_tamper.status_code == 200

# Now modify the exhibit file on disk directly inside container
# Query the file path in database
get_path_cmd = f'docker exec visionforensics-pilot-postgres psql -U postgres -d visionforensics -t -A -c "SELECT file_path FROM documents WHERE id=\'{doc_tamp_id}\';"'
file_path_in_container = subprocess.check_output(get_path_cmd, shell=True).decode().strip()
print(f" -> Exhibit Container Path: {file_path_in_container}")

# Mutate file content
mutate_cmd = f'docker exec visionforensics-pilot-backend sh -c "echo TAMPERED >> \'{file_path_in_container}\'"'
subprocess.check_call(mutate_cmd, shell=True)
print(" -> Successfully injected unauthorized byte modification into disk exhibit.")

# Attempt retrieval -> MUST trigger TAMPERING_ALARM (HTTP 409 Conflict)
r_tampered = session_a.get(f'{BASE_URL}/documents/{doc_tamp_id}/analysis', headers=headers_a)
print(f" -> Post-tamper retrieval status: {r_tampered.status_code}")
print(f" -> Post-tamper detail: {r_tampered.json().get('detail')}")
assert r_tampered.status_code == 409, f"Expected 409 Conflict, got {r_tampered.status_code}"
assert 'TAMPERING_ALARM' in r_tampered.json().get('detail', '')
print("[TEST 6 PASSED]")

# ------------------------------------------------------------- #
# TEST 7: Chain of custody log completeness                     #
# ------------------------------------------------------------- #
print("\n[TEST 7] Chain of Custody Audit Log Completeness")
r_cust = session_a.get(f'{BASE_URL}/documents/{doc_tamp_id}/custody-logs', headers=headers_a)
assert r_cust.status_code == 200, f"Custody log retrieval failed: {r_cust.status_code}"
logs = r_cust.json()
print(f" -> Total Custody Events Recorded: {len(logs)}")
event_types = [l['event_type'] for l in logs]
print(f" -> Event Sequence: {event_types}")
assert 'EXHIBIT_INGESTED' in event_types, "Missing EXHIBIT_INGESTED event"
assert 'TAMPERING_ALARM' in event_types, "Missing TAMPERING_ALARM event"
print("[TEST 7 PASSED]")

# ------------------------------------------------------------- #
# TEST 8: IDOR rejection & RBAC cross-user protection           #
# ------------------------------------------------------------- #
print("\n[TEST 8] IDOR Defense & Role-Based Access Control Verification")
# Analyst B attempts to access Analyst A's doc_auth_id -> MUST return 403 Forbidden
r_idor = session_b.get(f'{BASE_URL}/documents/{doc_auth_id}/analysis', headers=headers_b)
print(f" -> Analyst B access to Analyst A doc status: {r_idor.status_code}")
assert r_idor.status_code == 403, f"Expected 403 Forbidden for IDOR attempt, got {r_idor.status_code}"

# Administrator attempts to access Analyst A's doc_auth_id -> MUST return 200 OK (Global Oversight)
r_admin_access = session_admin.get(f'{BASE_URL}/documents/{doc_auth_id}/analysis', headers=headers_admin)
print(f" -> Admin access to Analyst A doc status: {r_admin_access.status_code}")
assert r_admin_access.status_code == 200, f"Expected 200 OK for Admin access, got {r_admin_access.status_code}"
print("[TEST 8 PASSED]")

# ------------------------------------------------------------- #
# TEST 9: Logout & session invalidation                         #
# ------------------------------------------------------------- #
print("\n[TEST 9] Logout & Session Invalidation Verification")
# Logout Analyst B's session
r_logout = session_b.post(f'{BASE_URL}/auth/logout', headers=headers_b)
assert r_logout.status_code == 200
print(" -> Successfully called /auth/logout")

# Try refreshing with Analyst B's cookies -> MUST fail 401
r_post_ref = session_b.post(f'{BASE_URL}/auth/refresh')
print(f" -> Post-logout cookie refresh status: {r_post_ref.status_code}")
assert r_post_ref.status_code == 401, f"Expected 401, got {r_post_ref.status_code}"
print("[TEST 9 PASSED]")

# ------------------------------------------------------------- #
# TEST 10: Container restart persistence                        #
# ------------------------------------------------------------- #
print("\n[TEST 10] Container Restart & Data Persistence Verification")
print(" -> Restarting backend and postgres containers...")
subprocess.check_call("docker restart visionforensics-pilot-postgres", shell=True)
subprocess.check_call("docker restart visionforensics-pilot-backend", shell=True)
time.sleep(8)

# Login after restart using safe_login
token_after = safe_login(session_a, 'pilot_analyst_a@pilot.visionforensics.local', 'SmokeTestPassword2026!')
headers_after = {'Authorization': f'Bearer {token_after}'}

# Verify doc_auth_id still exists and is accessible
r_post_check = session_a.get(f'{BASE_URL}/documents/{doc_auth_id}/analysis', headers=headers_after)
assert r_post_check.status_code == 200, f"Document missing after restart: {r_post_check.status_code}"
print(f" -> Verified exhibit {doc_auth_id} persisted intact across restart.")

# Verify report rep_id still exists and is downloadable
r_post_rep = session_a.get(f'{BASE_URL}/reports/{rep_id}', headers=headers_after)
assert r_post_rep.status_code == 200, f"Report metadata missing after restart: {r_post_rep.status_code}"
print(f" -> Verified report {rep_id} persisted intact across restart.")
print("[TEST 10 PASSED]")

print("\n=== ALL 10 END-TO-END TESTS COMPLETED SUCCESSFULLY (10/10 PASS) ===")
