"""Final read-only checks: frozen files, deployed assets, headers and bindings."""
from pathlib import Path
import hashlib
import json
import re
import ssl
import subprocess
import httpx

ROOT = Path(__file__).resolve().parents[1]
baseline = json.loads((ROOT/'project_audit/baseline_manifest.json').read_text())
protected = []
for name, expected in baseline['protected_sha256'].items():
    actual = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    assert actual == expected, 'Protected file changed: '+name
    protected.append({'file':name,'sha256':actual,'unchanged':True})
context=ssl.create_default_context(cafile=str(ROOT/'ca/pilot_ca.crt'))
checks=[]
with httpx.Client(verify=context,trust_env=False,timeout=30) as client:
    base='https://127.0.0.1:8443'
    html=client.get(base+'/')
    assert html.content == (ROOT/'frontend/dist/index.html').read_bytes()
    targets=['/','/login','/cases']+re.findall(r'(?:src|href)="(/assets/[^\"]+)"',html.text)+['/api/v1/health']
    for target in targets:
        response=client.get(base+target)
        assert response.status_code == 200, target
        for header in ['strict-transport-security','content-security-policy','x-content-type-options','x-frame-options']:
            assert header in response.headers, target+' missing '+header
        if target.startswith('/assets/'):
            assert response.content == (ROOT/'frontend/dist'/target.lstrip('/')).read_bytes()
        checks.append({'path':target,'status':'PASS','sha256':hashlib.sha256(response.content).hexdigest(),'security_headers':'PASS'})
    health=client.get(base+'/api/v1/health').json()
    redirect=client.get('http://127.0.0.1:8080/')
    assert redirect.status_code == 301 and redirect.headers['location'].startswith('https://127.0.0.1:8443/')
    check_native=client.get('http://127.0.0.1:5173/api/v1/health')
    assert check_native.status_code == 200
    native_health=check_native.json()
names=['visionforensics-pilot-postgres','visionforensics-pilot-backend','visionforensics-pilot-frontend']
containers=json.loads(subprocess.check_output(['docker','inspect',*names],text=True))
safe=[]
for item in containers:
    ports=item['NetworkSettings']['Ports'] or {}
    for bindings in ports.values():
        for binding in bindings or []:
            assert binding['HostIp'] == '127.0.0.1'
    assert item['State']['Running']
    safe.append({'name':item['Name'].lstrip('/'),'image_id':item['Image'],'running':True,'health':item['State'].get('Health',{}).get('Status'),'ports':ports})
changed=[]
for name, oldhash in baseline['source_sha256'].items():
    path=ROOT/name
    newhash=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if newhash != oldhash:
        changed.append({'file':name,'before':oldhash,'after':newhash})
result={'protected_files':protected,'source_changes':changed,'deployed_checks':checks,'https_health':health,'native_preview_health':native_health,'http_redirect':'PASS','containers':safe}
(ROOT/'project_audit/final_verification.json').write_text(json.dumps(result,indent=2))
print('Protected files unchanged:',len(protected),'; deployed page/assets/header checks:',len(checks),'; all 3 pilot containers running; native preview healthy.')
