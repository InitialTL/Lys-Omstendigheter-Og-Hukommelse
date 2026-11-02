import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_online_backup_does_not_copy_inconsistent_wal(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / 'research data.db'
    with sqlite3.connect(source) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('CREATE TABLE test (answer TEXT)')
        conn.execute('INSERT INTO test VALUES (?)', ('saved before backup',))
    # Keep an active WAL-mode writer/reader open while using the backup API.
    with sqlite3.connect(source) as conn:
        conn.execute('PRAGMA wal_autocheckpoint=0')
        conn.execute('INSERT INTO test VALUES (?)', ('visible in backup',))
        conn.commit()  # Uncommitted data must NOT be included in a backup.
        output = tmp_path / 'secure backups'
        run = subprocess.run(
            [sys.executable,str(root/'scripts'/'backup_sqlite.py'),str(output)],
            env={**os.environ,'STUDY_DATABASE':str(source)},
            capture_output=True,text=True,check=True,
        )
        files = list(output.glob('hukommelse-*.db'))
        assert len(files)==1,run.stdout
        with sqlite3.connect(files[0]) as archived:
            assert archived.execute('SELECT answer FROM test ORDER BY rowid').fetchall() == [
                ('saved before backup',),('visible in backup',)
            ]
            assert archived.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    if os.name != 'nt':
        assert files[0].stat().st_mode & 0o077 == 0
