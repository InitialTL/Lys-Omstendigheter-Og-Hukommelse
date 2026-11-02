"""Consistent, atomic SQLite backups, safe while the study server is running.

Usage: python scripts/backup_sqlite.py /absolute/path/to/backups
The file permissions are restricted where supported; arrange encrypted/off-host
copies yourself. Never copy only a live WAL-mode .db file for backups.
"""
from __future__ import annotations
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = ROOT / 'backend' / 'results.db'


def backup(source: Path, destination_dir: Path) -> Path:
    source = source.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError('Database source is not a file')
    destination_dir = destination_dir.expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = destination_dir / f'hukommelse-{stamp}.db'
    counter = 1
    while target.exists():
        target = destination_dir / f'hukommelse-{stamp}-{counter}.db'
        counter += 1
    staging = destination_dir / f'.{target.name}.{secrets.token_hex(6)}.partial'
    staging.touch(mode=0o600, exist_ok=False)
    try:
        with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src:
            with sqlite3.connect(staging) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise RuntimeError('Backup failed SQLite integrity check')
        if os.name != 'nt':
            os.chmod(staging, 0o600)
        staging.replace(target)
        return target
    finally:
        if staging.exists():
            staging.unlink()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/backup_sqlite.py /path/to/backup-directory')
    db = Path(os.getenv('STUDY_DATABASE', str(DEFAULT_DATABASE)))
    print('Backup created:', backup(db, Path(sys.argv[1])))
