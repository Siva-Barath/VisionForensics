"""Controlled integration checks against ONLY the restored audit database.

No historical files are modified. Generated evidence and result JSON are retained.
Run from the repository root. Credentials are read from existing local config and
never printed or written into result artifacts.
"""
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys

from dotenv import dotenv_values
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
isolated = json.loads((ROOT / 'project_audit/backups/isolated_restore.json').read_text())['database']
assert isolated.startswith('vf_stabilization_')
url = urlsplit(dotenv_values(ROOT / 'backend/.env')['DATABASE_URL'])
os.environ['DATABASE_URL'] = urlunsplit(url._replace(path='/' + isolated))
os.environ['APP_ENV'] = 'development'
os.environ['APP_DEBUG'] = 'false'
os.environ['ALLOWED_ORIGINS'] = 'http://localhost:5173'
evidence_root = ROOT / 'project_audit/controlled_evidence'
for key, folder in [('UPLOAD_DIR', 'uploads'), ('PROCESSED_DIR', 'processed'),
                    ('REPORTS_DIR', 'reports'), ('HEATMAPS_DIR', 'heatmaps')]:
    os.environ[key] = str(evidence_root / folder)
    (evidence_root / folder).mkdir(parents=True, exist_ok=True)

from PIL import Image, ImageDraw
import httpx
from app import app, document_service
from app.services.context_snapshot import snapshot_context

results = []
provenance = []
created_documents = []


def record(name, passed, detail=''):
    results.append({'workflow': name, 'status': 'PASS' if passed else 'FAIL', 'detail': detail})


async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost:5173', timeout=120) as client:
        response = await client.get('/api/v1/documents')
        record('Unauthenticated access rejected', response.status_code == 401)
        # Existing documented demo account in isolated restored DB; no credential changes.
        reference = (ROOT / 'scripts/verify_disposable_exhibit_tampering.py').read_text()
        password = re.search(r'"password":\s*"([^"]+)"', reference).group(1)
        response = await client.post('/api/v1/auth/login', json={'email': 'pilot_analyst_a@pilot.visionforensics.local', 'password': password})
        record('Login', response.status_code == 200)
        if response.status_code != 200:
            return
        record('Asset cookie is HttpOnly', 'HttpOnly' in response.headers.get_list('set-cookie')[1])
        token = response.json()['access_token']
        client.headers['Authorization'] = 'Bearer ' + token
        response = await client.get('/api/v1/documents')
        record('Authenticated document listing', response.status_code == 200)
        case_response = await client.post('/api/v1/cases', json={'title': 'Controlled case creation', 'notes': 'Provenance-preserved test', 'priority': 'urgent'})
        record('New case creation', case_response.status_code == 201)
        case_id = case_response.json().get('id')
        if case_id:
            case_read = await client.get('/api/v1/cases/' + case_id)
            record('Case details persistence', case_read.status_code == 200 and case_read.json()['notes'] == 'Provenance-preserved test')

        image = Image.new('RGB', (640, 480), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((25, 25, 615, 455), outline='black', width=2)
        for line in range(12):
            draw.text((50, 60 + line * 24), f'CONTROLLED SYNTHETIC EXHIBIT - FIELD {line}: ORIGINAL', fill='black')
        edited = image.copy()
        ImageDraw.Draw(edited).rectangle((280, 120, 450, 175), fill=(210, 215, 225))
        fixtures = []
        for filename, fmt, pages in [('baseline.png', 'PNG', None), ('modified.jpg', 'JPEG', None), ('two_pages.pdf', 'PDF', [edited])]:
            buf = io.BytesIO()
            current = edited if fmt == 'JPEG' else image
            if pages:
                current.save(buf, format=fmt, save_all=True, append_images=pages)
            else:
                current.save(buf, format=fmt)
            content = buf.getvalue()
            source = evidence_root / filename
            if source.exists():
                # Reuse retained originals; PDF creation timestamps can differ
                # across runs. Never overwrite an existing controlled exhibit.
                content = source.read_bytes()
            else:
                source.write_bytes(content)
            provenance.append({'filename': filename, 'sha256': hashlib.sha256(content).hexdigest(),
                               'origin': 'Pillow deterministic synthetic fixture; no real identity or benchmark data',
                               'ground_truth': 'pixel edit' if filename.startswith('modified') else 'synthetic control',
                               'limitation': 'workflow control, not authentic-document accuracy evaluation'})
            fixtures.append((filename, content))

        docs = []
        for filename, content in fixtures:
            upload = await client.post('/api/v1/upload', files={'file': (filename, content)},
                data={'case_title': 'Controlled intake ' + filename, 'case_notes': 'Persist these case notes', 'priority': 'urgent'})
            record('Upload ' + filename, upload.status_code == 201, str(upload.status_code))
            if upload.status_code != 201:
                continue
            body = upload.json()
            doc_id = body['document_id']
            docs.append(doc_id)
            created_documents.append({'id': doc_id, 'filename': filename, 'sha256': hashlib.sha256(content).hexdigest()})
            record('Pipeline ' + filename, body['processing_status'] == 'completed', body['processing_status'])
            analysis = await client.get(f'/api/v1/documents/{doc_id}/analysis')
            record('Analysis retrieval ' + filename, analysis.status_code == 200)
            if analysis.status_code != 200:
                continue
            payload = analysis.json()
            record('Raw ML separated ' + filename, payload.get('raw_ml') is not None and payload['raw_ml']['is_document_probability'] is False)
            record('All 18 genuine inputs ' + filename, len(payload.get('raw_ml', {}).get('feature_vector', {})) == 18)
            record('Actual module execution ' + filename, bool(payload.get('module_statuses')) and payload['module_statuses']['file_integrity']['status'] == 'COMPLETED')
            record('Frozen ML execution ' + filename, payload['track_1_ml']['status'] in ['SUCCESS', 'DEGRADED'], payload['track_1_ml']['status'])
            record('T=.40 preserved ' + filename, payload['track_1_ml']['operational_threshold'] == .40)
            record('Page count ' + filename, payload['image_dimensions']['page_count'] == (2 if filename.endswith('.pdf') else 1))
            original = await client.get(f'/api/v1/documents/{doc_id}/original')
            record('Original bytes/SHA ' + filename, original.status_code == 200 and original.content == content)
            preview = await client.get(f'/api/v1/documents/{doc_id}/image?page=0')
            record('Derived preview ' + filename, preview.status_code == 200 and preview.headers.get('content-type', '').startswith('image/'))
            if preview.status_code == 200:
                with Image.open(io.BytesIO(preview.content)) as raster:
                    record('Preview coordinate dimensions ' + filename, raster.size == (payload['image_dimensions']['pages'][0]['width'], payload['image_dimensions']['pages'][0]['height']))
            if 0 in payload.get('heatmap_available_pages', []):
                heatmap = await client.get(f'/api/v1/documents/{doc_id}/heatmap?page=0')
                record('Real ELA heatmap ' + filename, heatmap.status_code == 200 and heatmap.headers.get('content-type') == 'image/png')
            else:
                record('Real ELA heatmap ' + filename, False, 'Derived error map unavailable')
            before = snapshot_context(document_service.get_context(doc_id))
            document_service._analysis_cache.pop(doc_id)
            after = snapshot_context(document_service.get_context(doc_id))
            record('Database round-trip ' + filename, before == after)
            after_api = await client.get(f'/api/v1/documents/{doc_id}/analysis')
            record('API equality after cache loss ' + filename, after_api.json() == payload)
            if filename.endswith('.pdf'):
                last = await client.get(f'/api/v1/documents/{doc_id}/image?page=1')
                beyond = await client.get(f'/api/v1/documents/{doc_id}/image?page=2')
                record('Multi-page last/bounds', last.status_code == 200 and beyond.status_code == 404)
            custody = await client.get(f'/api/v1/documents/{doc_id}/custody-logs')
            record('Custody events ' + filename, custody.status_code == 200 and len(custody.json()) >= 3)

        invalid = await client.post('/api/v1/upload', files={'file': ('disguised.png', b'THIS IS NOT AN IMAGE ' * 4)})
        record('Invalid content rejected', invalid.status_code == 415)
        oversized = await client.post('/api/v1/upload', files={'file': ('controlled-oversized.pdf', b'0' * (21 * 1024 * 1024))})
        record('Oversized file rejected', oversized.status_code == 413)
        cases = await client.get('/api/v1/cases')
        record('Intake metadata retained', cases.status_code == 200 and any(case['notes'] == 'Persist these case notes' and case['document_count'] == 1 for case in cases.json()))
        stats = await client.get('/api/v1/workspace/stats')
        record('Exact workspace totals endpoint', stats.status_code == 200 and stats.json()['total_cases'] >= 4)
        if len(docs) >= 2:
            comp = await client.post('/api/v1/comparison', json={'document_a_id': docs[0], 'document_b_id': docs[1], 'align_images': True})
            record('Document comparison', comp.status_code == 200, str(comp.status_code))
            report = await client.post('/api/v1/reports', json={'document_id': docs[0], 'analyst_notes': 'Controlled synthetic workflow verification; not an authenticity evaluation.'})
            record('Report generation', report.status_code == 201, str(report.status_code))
            if report.status_code == 201:
                download = await client.get(report.json()['download_url'])
                record('Report hash/download', download.status_code == 200 and hashlib.sha256(download.content).hexdigest() == report.json()['sha256_hash'])

        # Cookie-only access must work for browser image/download elements.
        client.headers.pop('Authorization', None)
        if docs:
            asset = await client.get(f'/api/v1/documents/{docs[0]}/image')
            record('Cookie-only asset authentication', asset.status_code == 200)
        logout = await client.post('/api/v1/auth/logout')
        record('Logout', logout.status_code == 200)
        denied = await client.get('/api/v1/documents')
        record('Post-logout cookie access rejected', denied.status_code == 401)
        other_password = 'IsolatedGenerated123!'
        import uuid
        other_email = 'isolated_' + uuid.uuid4().hex[:10] + '@visionforensics.local'
        registered = await client.post('/api/v1/auth/register', json={'email': other_email, 'password': other_password, 'full_name': 'Controlled other analyst'})
        record('Controlled analyst registration', registered.status_code == 201)
        other_login = await client.post('/api/v1/auth/login', json={'email': other_email, 'password': other_password})
        record('Other analyst login', other_login.status_code == 200)
        if other_login.status_code == 200 and docs:
            denied = await client.get(f'/api/v1/documents/{docs[0]}/analysis')
            record('Cross-user exhibit restriction', denied.status_code == 403)
            denied_case = await client.get('/api/v1/cases/' + case_id)
            record('Cross-user case restriction', denied_case.status_code == 404)
            denied_admin = await client.get('/api/v1/admin/users')
            record('Role-based administrator restriction', denied_admin.status_code == 403)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    finally:
        (ROOT / 'project_audit/controlled_provenance.json').write_text(json.dumps(provenance, indent=2))
        (ROOT / 'project_audit/isolated_workflows.json').write_text(json.dumps({'database': isolated, 'documents': created_documents, 'results': results}, indent=2))
        print('Controlled checks:', len(results), 'failed:', sum(r['status'] == 'FAIL' for r in results), flush=True)
