"""Lightweight CI contracts for hosted SQLite deployment; no network needed.

Detailed behavioral testing still happens in Docker and the backend tests.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check():
    fly = tomllib.loads((ROOT / 'fly.toml').read_text(encoding='utf-8'))
    assert fly['env']['STUDY_DATABASE'] == '/data/results.db'
    assert fly['env']['STUDY_REQUIRE_PERSISTENT_VOLUME'] == '1'
    assert fly['http_service']['auto_stop_machines'] == 'off'
    assert fly['http_service']['internal_port'] == int(fly['env']['PORT'])
    assert fly['http_service']['checks'][0]['headers']['Host'] == 'localhost'
    assert len(fly['mounts']) == 1 and fly['mounts'][0] == {'source': 'study_data', 'destination': '/data'}
    assert len(fly['vm']) == 1 and fly['vm'][0]['cpu_kind'] == 'shared'
    assert fly['vm'][0]['memory'] == '512mb'
    assert (ROOT / 'scripts' / 'start_hosted.sh').exists()
    assert subprocess.run(['sh', '-n', str(ROOT / 'scripts' / 'start_hosted.sh')], check=False).returncode == 0
    docker = (ROOT / 'Dockerfile').read_text(encoding='utf-8')
    assert 'gosu study uvicorn' in (ROOT / 'scripts' / 'start_hosted.sh').read_text()
    assert 'ENTRYPOINT ["/usr/local/bin/start-hosted"]' in docker
    assert '\nVOLUME ' not in docker, 'Anonymous volumes hide missing persistent storage'
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, STUDY_DATABASE=str(Path(tmp) / 'test.db'),
                   RAILWAY_PUBLIC_DOMAIN='quiet-forest.up.railway.app',
                   RAILWAY_SERVICE_ID='a-real-railway-service-id',
                   FLY_APP_NAME='memory-research')
        code = '''from fastapi.testclient import TestClient
from server import app, allowed_hosts
assert 'quiet-forest.up.railway.app' in allowed_hosts()
assert 'memory-research.fly.dev' in allowed_hosts()
assert 'healthcheck.railway.app' in allowed_hosts()
client=TestClient(app)
for domain in ['quiet-forest.up.railway.app', 'memory-research.fly.dev', 'healthcheck.railway.app']:
 response=client.get('/api/health', headers={'host':domain})
 assert response.status_code == 200, response.text
 assert response.json()['status'] == 'ok'
response=client.get('/api/health', headers={'host':'attacker.example'})
assert response.status_code == 400, response.text
'''
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT/'backend',
                                env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + '\n' + result.stderr
    print('PASS: Fly config, Docker security, hostnames, health endpoint and mount policy')


if __name__ == '__main__':
    check()
