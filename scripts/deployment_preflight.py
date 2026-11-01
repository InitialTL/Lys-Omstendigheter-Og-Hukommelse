"""Deployment configuration checks without printing secrets or modifying study data.

Run from the repository root after building the frontend. This is not a
vulnerability scanner; it checks common origin/tunnel deployment mistakes.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check():
    errors = []
    warnings = []
    allowed = [x.strip() for x in os.getenv('STUDY_ALLOWED_HOSTS', '').split(',') if x.strip()]
    if not allowed or all(x in ('localhost','127.0.0.1','::1','testserver') for x in allowed):
        warnings.append('Set STUDY_ALLOWED_HOSTS to the actual public study hostname before publishing.')
    if '*' in allowed or any('://' in host for host in allowed):
        errors.append('STUDY_ALLOWED_HOSTS must use explicit hostnames, without protocols or *.')
    if not (ROOT/'frontend'/'dist'/'index.html').exists():
        errors.append('Missing frontend/dist/index.html. Run npm --prefix frontend run build first.')
    admin = os.getenv('STUDY_ADMIN_TOKEN', '')
    if admin and len(admin) < 32:
        errors.append('STUDY_ADMIN_TOKEN must be a high-entropy secret with at least 32 characters, or unset to disable exports.')
    if not admin:
        warnings.append('Admin exports are disabled until STUDY_ADMIN_TOKEN is set (safe default).')
    db = Path(os.getenv('STUDY_DATABASE', str(ROOT/'backend'/'results.db'))).expanduser()
    if not db.parent.exists() or not os.access(db.parent, os.W_OK):
        errors.append('STUDY_DATABASE parent directory is absent or not writable by the service user.')
    if not os.getenv('STUDY_DATABASE'):
        warnings.append('Set STUDY_DATABASE to persistent storage outside the application working tree.')
    if os.getenv('STUDY_TRUST_CLOUDFLARE') == '1':
        warnings.append('STUDY_TRUST_CLOUDFLARE requires an origin inaccessible directly from the internet.')
    print('Hukommelse LM deployment preflight')
    for msg in errors:
        print('ERROR:', msg)
    for msg in warnings:
        print('WARNING:', msg)
    if not errors:
        print('PASS: local configuration checks found no blocking errors.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(check())
