"""Chromium E2E smoke test for real React+FastAPI integration.

CI only. Starts a temporary SQLite-backed server and a browser; no network
analytics, paid API, or existing participant data is used.
"""
from __future__ import annotations
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = 'http://127.0.0.1:18080'


def wait_for_server():
    for _ in range(100):
        try:
            if httpx.get(BASE + '/api/health', timeout=0.5).status_code == 200:
                return
        except (httpx.HTTPError, OSError):
            pass
        time.sleep(0.1)
    raise RuntimeError('FastAPI did not start')


def advance(db_path: Path, participant_id: str, elapsed: int):
    with sqlite3.connect(db_path) as db:
        db.execute('UPDATE study_rounds SET started_at=? WHERE participant_id=? AND round_index=0',
                   (time.time() - elapsed, participant_id))


def one_device(browser, db_path: Path, width: int, height: int, mobile: bool):
    context = browser.new_context(viewport={'width': width, 'height': height},
                                  locale='en-US', is_mobile=mobile, has_touch=mobile)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    page.goto(BASE, wait_until='networkidle')
    page.locator('.consent-control input').check()
    page.get_by_role('button', name='Begin experiment').click()
    try:
        page.locator('.calibration-checklist').wait_for(timeout=10000)
    except Exception as exc:
        raise AssertionError(f'Calibration was not shown at {width}px. Page text: {page.locator("body").inner_text()[:750]}; console: {errors}') from exc
    for tile in page.locator('.check-tile').all():
        tile.click()
    page.get_by_role('button', name='I am ready').click()
    page.get_by_role('button', name='Start this round').click()
    page.locator('.acclimation-screen').wait_for()
    assert page.locator('.acclimation-screen .acclimation-timer').count() == 1
    assert page.locator('.acclimation-screen .study-card').count() == 0
    participant_id = page.evaluate("localStorage.getItem('lm_v2_participant')")
    assert participant_id

    advance(db_path, participant_id, 61)
    page.reload(wait_until='networkidle')
    page.locator('.pairs-grid .pair-tile').first.wait_for()
    assert page.locator('.pair-tile').count() == 10
    advance(db_path, participant_id, 122)
    page.reload(wait_until='networkidle')
    page.locator('.math-form input').wait_for()
    advance(db_path, participant_id, 153)
    page.reload(wait_until='networkidle')
    page.locator('.answers-grid input').first.wait_for()
    assert page.locator('.answers-grid input').count() == 10
    page.wait_for_timeout(1100)
    assert page.locator('.answers-grid input').count() == 10, 'Recall auto-submitted immediately'
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), f'Horizontal overflow at {width}px'
    page.locator('.answers-grid input').first.fill('test')
    page.get_by_role('button', name='Submit answers').click()
    page.get_by_role('button', name='Start this round').wait_for()
    with sqlite3.connect(db_path) as db:
        assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?',
                          (participant_id,)).fetchone()[0] == 1
    assert not errors, f'Browser exceptions at {width}: {errors}'
    print(f'PASS {width}×{height} mobile={mobile}, all stages and recall fields')
    context.close()


def main():
    with tempfile.TemporaryDirectory(prefix='lm-ui-test-') as tmp:
        db_path = Path(tmp) / 'study.db'
        env = {**os.environ, 'STUDY_DATABASE':str(db_path),
               'STUDY_ALLOWED_HOSTS':'localhost,127.0.0.1,testserver'}
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server:app',
                                   '--host', '127.0.0.1', '--port', '18080', '--workers', '1'],
                                  cwd=ROOT/'backend', env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            wait_for_server()
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    for width,height,mobile in [(320,640,True), (390,844,True), (768,1024,True), (1280,850,False)]:
                        one_device(browser, db_path, width, height, mobile)
                finally:
                    browser.close()
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill()


if __name__ == '__main__':
    main()
