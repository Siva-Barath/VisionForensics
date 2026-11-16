"""Restore schema only into a NEW test DB and run the complete backend suite.

No historical rows/files are copied or altered. Test DB/files are retained for
review. Requires the verified backup from the project audit and local admin
configuration. Secrets are passed through child environment, never logged.
"""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote
import json
import os
import re
import subprocess
import sys
import uuid

from dotenv import dotenv_values
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
cfg = dotenv_values(ROOT / '.env')
runtime = urlsplit(dotenv_values(ROOT / 'backend/.env')['DATABASE_URL'])
name = 'vf_test_' + uuid.uuid4().hex[:12]
admin = dict(host=runtime.hostname, port=runtime.port, dbname='postgres',
             user=cfg['POSTGRES_USER'], password=cfg['POSTGRES_PASSWORD'], connect_timeout=5)
connection = psycopg2.connect(**admin)
connection.autocommit = True
with connection.cursor() as cursor:
    cursor.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
connection.close()
env = os.environ.copy()
env.update(PGHOST=admin['host'], PGPORT=str(admin['port']), PGDATABASE=name,
           PGUSER=admin['user'], PGPASSWORD=admin['password'])
archive = ROOT / 'project_audit/backups/before_context_snapshot_20261113.dump'
if not archive.is_file():
    raise RuntimeError('Verified pre-migration backup required')
restored = subprocess.run([r'C:\Program Files\PostgreSQL\17\bin\pg_restore.exe',
                          '--schema-only', '--exit-on-error', '--no-password', '-d', name, str(archive)],
                         env=env, capture_output=True, text=True)
if restored.returncode:
    raise RuntimeError('Isolated schema restore failed: ' + restored.stderr)
connection = psycopg2.connect(**dict(admin, dbname=name))
with connection:
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO alembic_version(version_num) VALUES ('146af5c0448f')")
connection.close()
admin_url = 'postgresql://' + quote(admin['user'], safe='') + ':' + quote(admin['password'], safe='') + '@' + runtime.hostname + ':' + str(runtime.port) + '/' + name
env.update(DATABASE_URL=urlunsplit(runtime._replace(path='/' + name)), MIGRATION_DATABASE_URL=admin_url,
           VF_ISOLATED_TEST_DB=name, APP_ENV='development', APP_DEBUG='false',
           ALLOWED_ORIGINS='http://localhost:5173,http://testserver,http://test',
           PYTHONPATH=str(ROOT / 'backend'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
storage = ROOT / 'project_audit' / 'test_runs' / name
for key, directory in [('UPLOAD_DIR', 'uploads'), ('PROCESSED_DIR', 'processed'), ('REPORTS_DIR', 'reports'), ('HEATMAPS_DIR', 'heatmaps')]:
    path = storage / directory
    path.mkdir(parents=True, exist_ok=True)
    env[key] = str(path)
migrated = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT / 'backend',
                         env=env, capture_output=True, text=True)
if migrated.returncode:
    raise RuntimeError('Isolated migration failed')
(ROOT / 'project_audit/test_environment.json').write_text(json.dumps({'database': name, 'storage': str(storage), 'initial_records': 0}, indent=2))
print('Running full backend suite on fresh database:', name, flush=True)
result = subprocess.run([sys.executable, '-m', 'pytest', 'backend/tests', '-p', 'pytest_asyncio.plugin',
                         '-q', '--disable-warnings', '--tb=short', '--continue-on-collection-errors', '--junitxml=project_audit/full_backend_tests.xml'],
                        env=env, capture_output=True, text=True)
output = result.stdout + '\n' + result.stderr
for values in [cfg, dotenv_values(ROOT / 'backend/.env')]:
    for key, value in values.items():
        if value and any(word in key.upper() for word in ['PASSWORD', 'SECRET', 'TOKEN', 'DATABASE_URL']):
            output = output.replace(value, '[REDACTED]')
output = re.sub(r'eyJ[A-Za-z0-9_.-]{30,}', '[REDACTED_JWT]', output)
(ROOT / 'project_audit/full_backend_tests.log').write_text(output, encoding='utf-8')
print('Full suite exit:', result.returncode, flush=True)
print('\n'.join(output.splitlines()[-22:]), flush=True)
sys.exit(result.returncode)
