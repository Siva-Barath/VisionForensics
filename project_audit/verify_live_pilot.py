"""CA-verified HTTPS workflow checks on controlled, retained pilot exhibits."""
from pathlib import Path
import hashlib
import io
import json
import re
import ssl
import sys
import secrets
import subprocess
import time
import uuid
import httpx
from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'project_audit/live_pilot_verification.json'
restart_only = '--readback' in sys.argv
if restart_only:
    raise SystemExit('Standalone readback requires the non-retained controlled credentials. Use verify_final_state.py for read-only checks; the default workflow already verifies restart readback in-process.')
previous = json.loads(OUT.read_text()) if restart_only else None
results = []
documents = previous['documents'] if previous else []
def check(name, condition):
    results.append({'check': name, 'status': 'PASS' if condition else 'FAIL'})
    if not condition:
        raise RuntimeError('Check failed: ' + name)

context = ssl.create_default_context(cafile=str(ROOT/'ca/pilot_ca.crt'))
email = 'controlled_pilot_' + uuid.uuid4().hex[:12] + '@visionforensics.local'
password = 'Controlled!' + secrets.token_urlsafe(28) + '7'
with httpx.Client(base_url='https://127.0.0.1:8443', verify=context, timeout=180, trust_env=False) as client:
    health = client.get('/api/v1/health')
    check('HTTPS trusted by pilot CA, backend healthy', health.status_code == 200 and health.json()['status'] == 'healthy')
    check('Frozen model integrity and threshold', health.json()['modules']['ml_engine']['integrity_verified'] and health.json()['modules']['ml_engine']['operational_threshold'] == .40)
    check('Unavailable OCR reported honestly', health.json()['modules']['ocr_engine']['status'] == 'unavailable')
    html = client.get('/')
    check('Production UI served', html.status_code == 200 and 'VisionForensics AI' in html.text)
    for asset in re.findall(r'(?:src|href)="(/assets/[^\"]+)"', html.text):
        data = client.get(asset)
        check('Built asset matches deployed bytes: ' + asset, data.status_code == 200 and data.content == (ROOT/'frontend/dist'/asset.lstrip('/')).read_bytes())
    check('Unauthenticated exhibit access denied', client.get('/api/v1/documents').status_code == 401)
    registered = client.post('/api/v1/auth/register', json={'email':email,'password':password,'full_name':'Controlled pilot workflow validation'})
    check('Controlled analyst registration', registered.status_code == 201)
    login = client.post('/api/v1/auth/login', json={'email':email, 'password':password})
    check('Cookie authentication', login.status_code == 200)
    cookies = login.headers.get_list('set-cookie')
    check('Secure HttpOnly access and refresh cookies', len(cookies) >= 2 and all('httponly' in cookie.lower() and 'secure' in cookie.lower() for cookie in cookies))
    if not restart_only:
        for filename in ['baseline.png','modified.jpg','two_pages.pdf']:
            content = (ROOT/'project_audit/controlled_evidence'/filename).read_bytes()
            upload = client.post('/api/v1/upload', files={'file':('CONTROLLED_PILOT_'+filename,content)}, data={'case_title':'Controlled pilot validation: '+filename, 'case_notes':'Synthetic workflow validation, retained with provenance. Not benchmark evidence.', 'priority':'routine'})
            check('Upload/pipeline ' + filename, upload.status_code == 201 and upload.json()['processing_status'] == 'completed')
            documents.append({'id':upload.json()['document_id'], 'filename':filename, 'sha256':hashlib.sha256(content).hexdigest()})
    for doc in documents:
        prefix = '/api/v1/documents/'+doc['id']
        response = client.get(prefix+'/analysis')
        check('Persisted full analysis '+doc['filename'], response.status_code == 200)
        analysis = response.json()
        check('Raw 18 feature result '+doc['filename'], len(analysis['raw_ml']['feature_vector']) == 18 and analysis['raw_ml']['is_document_probability'] is False)
        check('Per-page results '+doc['filename'], len(analysis['pages_ml']) == (2 if doc['filename'].endswith('.pdf') else 1))
        original = client.get(prefix+'/original')
        check('Original bytes SHA256 '+doc['filename'], original.status_code == 200 and hashlib.sha256(original.content).hexdigest() == doc['sha256'])
        preview = client.get(prefix+'/image')
        check('Real derived preview '+doc['filename'], preview.status_code == 200)
        dims = analysis['image_dimensions']['pages'][0]
        with Image.open(io.BytesIO(preview.content)) as image:
            check('Region coordinate frame '+doc['filename'], image.size == (dims['width'],dims['height']))
        heatmap = client.get(prefix+'/heatmap')
        check('Real ELA artifact '+doc['filename'], heatmap.status_code == 200 and heatmap.headers['content-type'].startswith('image/'))
        custody = client.get(prefix+'/custody-logs')
        check('Custody retained '+doc['filename'], custody.status_code == 200 and len(custody.json()) > 0)
    if not restart_only:
        compare = client.post('/api/v1/comparison', json={'document_a_id':documents[0]['id'], 'document_b_id':documents[1]['id'], 'page_a':0,'page_b':0,'align_images':True})
        check('Live comparison',compare.status_code == 200)
        report = client.post('/api/v1/reports', json={'document_id':documents[-1]['id'], 'title':'Controlled pilot validation', 'analyst_notes':'Synthetic evidence; workflow verification only.'})
        check('Actual report generated', report.status_code in (200,201))
        info = report.json()
        pdf = client.get(info['download_url'])
        check('Report download hash',pdf.status_code == 200 and hashlib.sha256(pdf.content).hexdigest() == info['sha256_hash'])
        check('Real PDF page count',len(PdfReader(io.BytesIO(pdf.content)).pages) == info['page_count'])
        report_metadata = {'report_id':info['report_id'],'download_url':info['download_url'],'sha256':info['sha256_hash']}
    else:
        report_metadata = previous['report']
        pdf=client.get(report_metadata['download_url'])
        check('Report persists after container restart',pdf.status_code == 200 and hashlib.sha256(pdf.content).hexdigest() == report_metadata['sha256'])
    check('Scoped cases available',client.get('/api/v1/cases').status_code == 200)
    check('Exact scoped counts available',client.get('/api/v1/workspace/stats').status_code == 200)
    print('HTTPS workflow complete; restarting pilot database, backend and frontend for persistence verification.', flush=True)
    restarted = subprocess.run(['docker','restart','visionforensics-pilot-postgres','visionforensics-pilot-backend','visionforensics-pilot-frontend'],capture_output=True,text=True)
    check('Container restart completed without volume reset',restarted.returncode == 0)
    for attempt in range(30):
        try:
            if client.get('/api/v1/health').status_code == 200:
                break
        except httpx.TransportError:
            pass
        time.sleep(1)
    check('Healthy after container restart',client.get('/api/v1/health').status_code == 200)
    for doc in documents:
        prefix='/api/v1/documents/'+doc['id']
        analysis=client.get(prefix+'/analysis')
        check('Full raw snapshot survives restart '+doc['filename'],analysis.status_code == 200 and len(analysis.json()['raw_ml']['feature_vector']) == 18)
        original=client.get(prefix+'/original')
        check('Original survives restart '+doc['filename'],original.status_code == 200 and hashlib.sha256(original.content).hexdigest() == doc['sha256'])
        check('ELA artifact survives restart '+doc['filename'],client.get(prefix+'/heatmap').status_code == 200)
    pdf=client.get(report_metadata['download_url'])
    check('Report survives restart',pdf.status_code == 200 and hashlib.sha256(pdf.content).hexdigest() == report_metadata['sha256'])
    check('Logout',client.post('/api/v1/auth/logout').status_code == 200)
    check('Cookie revoked after logout',client.get('/api/v1/documents').status_code == 401)

target = OUT.with_name('live_pilot_restart.json') if restart_only else OUT
target.write_text(json.dumps({'base_url':'https://127.0.0.1:8443','certificate_verification':'pilot CA, hostname verification enabled','controlled_account':email,'password_retained':False,'documents':documents,'report':report_metadata,'results':results},indent=2))
print('Live HTTPS checks:',len(results),'passed; controlled exhibits retained:',len(documents))
