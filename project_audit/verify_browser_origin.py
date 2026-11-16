"""Verify canonical browser-origin cookie flows without changing trust policy."""
from pathlib import Path
import json
import secrets
import ssl
import uuid
import httpx

ROOT=Path(__file__).resolve().parents[1]
base='https://localhost:8443'
context=ssl.create_default_context(cafile=str(ROOT/'ca/pilot_ca.crt'))
results=[]
def check(name, ok):
    results.append({'check':name,'status':'PASS' if ok else 'FAIL'})
    assert ok, name
email='controlled_origin_'+uuid.uuid4().hex[:10]+'@visionforensics.local'
password='Controlled!'+secrets.token_urlsafe(25)+'7'
with httpx.Client(base_url=base,verify=context,headers={'Origin':base,'Sec-Fetch-Site':'same-origin'},trust_env=False,timeout=30) as client:
    response=client.get('/')
    check('Canonical localhost TLS certificate and production UI',response.status_code == 200 and response.content == (ROOT/'frontend/dist/index.html').read_bytes())
    registered=client.post('/api/v1/auth/register',json={'email':email,'password':password,'full_name':'Controlled browser-origin validation'})
    check('Registration from canonical browser origin',registered.status_code == 201)
    login=client.post('/api/v1/auth/login',json={'email':email,'password':password})
    check('Login from canonical browser origin',login.status_code == 200)
    check('Both cookies Secure and HttpOnly',len(login.headers.get_list('set-cookie')) >= 2 and all('secure' in x.lower() and 'httponly' in x.lower() for x in login.headers.get_list('set-cookie')))
    check('Cookie-only account access',client.get('/api/v1/auth/me').status_code == 200)
    refresh=client.post('/api/v1/auth/refresh',json={})
    check('Cookie refresh with canonical browser Origin',refresh.status_code == 200)
    denied=client.post('/api/v1/auth/refresh',json={},headers={'Origin':'https://untrusted.example','Sec-Fetch-Site':'cross-site'})
    check('Cross-origin cookie refresh rejected',denied.status_code == 403)
    denied=client.post('/api/v1/auth/logout',headers={'Origin':'https://untrusted.example','Sec-Fetch-Site':'cross-site'})
    check('Cross-origin cookie logout rejected',denied.status_code == 403)
    check('Legitimate session remains after rejected CSRF',client.get('/api/v1/auth/me').status_code == 200)
    check('Logout with canonical browser Origin',client.post('/api/v1/auth/logout').status_code == 200)
    check('Post-logout cookie access denied',client.get('/api/v1/auth/me').status_code == 401)
(ROOT/'project_audit/browser_origin_verification.json').write_text(json.dumps({'canonical_browser_url':base,'controlled_account':email,'password_retained':False,'results':results},indent=2))
print('Canonical browser-origin checks:',len(results),'passed; trust configuration unchanged.')
