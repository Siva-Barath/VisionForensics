"""Verify persisted controlled results from a separate Python application process."""
import asyncio
import hashlib
import json
import re
import httpx

from verify_isolated_workflows import app, ROOT, isolated


async def run():
    previous = json.loads((ROOT / 'project_audit/isolated_workflows.json').read_text())
    assert previous['database'] == isolated
    source = (ROOT / 'scripts/verify_disposable_exhibit_tampering.py').read_text()
    password = re.search(r'"password":\s*"([^"]+)"', source).group(1)
    results = []
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost:5173') as client:
        login = await client.post('/api/v1/auth/login', json={'email': 'pilot_analyst_a@pilot.visionforensics.local', 'password': password})
        assert login.status_code == 200
        for doc in previous['documents']:
            response = await client.get('/api/v1/documents/' + doc['id'] + '/analysis')
            assert response.status_code == 200
            data = response.json()
            assert len(data['raw_ml']['feature_vector']) == 18
            assert data['raw_ml']['is_document_probability'] is False
            assert len(data['pages_ml']) == (2 if doc['filename'].endswith('.pdf') else 1)
            original = await client.get('/api/v1/documents/' + doc['id'] + '/original')
            assert original.status_code == 200
            assert hashlib.sha256(original.content).hexdigest() == doc['sha256']
            heatmap = await client.get('/api/v1/documents/' + doc['id'] + '/heatmap')
            assert heatmap.status_code == 200
            results.append({'filename': doc['filename'], 'separate_process_persistence': 'PASS', 'original_sha256': 'PASS', 'heatmap': 'PASS'})
    (ROOT / 'project_audit/isolated_restart.json').write_text(json.dumps({'database': isolated, 'results': results}, indent=2))
    print('Separate-process persistence, original hashes and heatmaps verified for', len(results), 'controlled documents')


if __name__ == '__main__':
    asyncio.run(run())
