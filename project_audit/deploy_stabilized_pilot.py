"""Apply additive migration and deploy built images without resetting evidence volumes."""
from pathlib import Path
from urllib.parse import quote
import json
import os
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
def run(args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if result.returncode:
        # Do not include command environment or database URLs in errors.
        safe = re.sub(r'postgres(?:ql)?://[^\s]+', '[REDACTED DATABASE URL]', result.stderr)
        for value in globals().get('config', {}).values():
            if len(value) > 10:
                safe = safe.replace(value, '[REDACTED]')
        raise RuntimeError('Deployment step failed: ' + args[0] + ' ' + args[1] + '\n' + safe[-3500:])
    return result.stdout

backup = ROOT / 'project_audit/backups/pilot_before_stabilization_20261113.dump'
assert backup.is_file() and backup.stat().st_size > 0
container = json.loads(run(['docker', 'inspect', 'visionforensics-pilot-postgres']))[0]
config = dict(item.split('=', 1) for item in container['Config']['Env'] if '=' in item)
env = os.environ.copy()
env['MIGRATION_DATABASE_URL'] = 'postgresql://' + quote(config['POSTGRES_USER'], safe='') + ':' + quote(config['POSTGRES_PASSWORD'], safe='') + '@postgres:5432/' + config['POSTGRES_DB']
base = ['docker', 'compose', '--env-file', '.env.pilot', '-f', 'docker-compose.pilot.yml']
run(['docker', 'run', '--rm', '--network', 'visionforensics_pilot_net', '--env-file', '.env.pilot', '-e', 'MIGRATION_DATABASE_URL', 'forgerydetectionml-backend:latest', 'python', '-m', 'alembic', 'upgrade', 'head'], env=env)
print('Additive pilot migration applied; existing database owner used, runtime grants unchanged.', flush=True)
run(base + ['build', 'frontend'])
print('Frontend production image built.', flush=True)
run(base + ['up', '-d', '--no-deps', 'backend', 'frontend'])
print('Backend and frontend updated; persistent volumes preserved.', flush=True)
(ROOT / 'project_audit/deployment_result.json').write_text(json.dumps({'migration': 'PASS', 'frontend_image': 'PASS', 'backend_frontend_update': 'PASS', 'database_volume_reset': False}, indent=2))
