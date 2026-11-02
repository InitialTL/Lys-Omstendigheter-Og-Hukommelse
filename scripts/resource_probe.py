"""Dependency-free lightweight Pi-oriented storage / enrollment probe.

Runs on a TEMPORARY DB; does not use, read, or overwrite user results.
Not a physical Raspberry Pi benchmark or an HTTP attack/load test.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = '''
from pathlib import Path
import database, os, time
DB=database.DB_PATH
database.init_db()
start=time.perf_counter()
for i in range(300):
    database.create_participant('nb', '18_24', 'prefer_not')
seconds=time.perf_counter()-start
with database.connect() as db:
    participants=db.execute('SELECT COUNT(*) FROM study_participants').fetchone()[0]
    groups=db.execute('SELECT group_name,COUNT(*) FROM study_participants GROUP BY group_name ORDER BY group_name').fetchall()
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
bytes_size=DB.stat().st_size
assert participants == 300
assert [r[1] for r in groups] == [100,100,100]
assert bytes_size < 600_000, f'Unexpected DB growth: {bytes_size}'
print(f'PASS 300 participants; DB={bytes_size:,} bytes; enrollment={seconds:.2f}s')
'''

def main():
    with tempfile.TemporaryDirectory(prefix='lm-resource-') as directory:
        env={**os.environ,'STUDY_DATABASE':str(Path(directory)/'probe.db')}
        result=subprocess.run([sys.executable,'-c',SCRIPT],cwd=ROOT/'backend',env=env,
                               text=True,capture_output=True,timeout=30)
        if result.returncode:
            raise RuntimeError(result.stdout + '\n' + result.stderr)
        print(result.stdout.strip())

if __name__=='__main__': main()
