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


def advance(db_path: Path, participant_id: str, round_index: int, elapsed: int):
    with sqlite3.connect(db_path) as db:
        db.execute('UPDATE study_rounds SET started_at=? WHERE participant_id=? AND round_index=?',
                   (time.time() - elapsed, participant_id, round_index))


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
    participant_id = page.evaluate("localStorage.getItem('lm_v2_participant')")
    assert participant_id
    learned_words = []
    conditions_seen = []
    expected_colors = {'ORANGE': 'rgb(240, 163, 75)', 'BLUE': 'rgb(138, 183, 234)', 'NEUTRAL': 'rgb(179, 179, 179)'}
    for round_index in range(3):
        page.get_by_role('button', name='Start this round').click()
        page.locator('.acclimation-screen').wait_for()
        assert page.locator('.acclimation-screen .study-card').count() == 0
        condition = next(name for name in expected_colors if page.locator('.acclimation-' + name.lower()).count())
        assert condition not in conditions_seen, f'Duplicate condition: {condition}'
        conditions_seen.append(condition)
        rendered = page.locator('.acclimation-screen').evaluate('(node) => getComputedStyle(node).backgroundColor')
        assert rendered == expected_colors[condition], (condition, rendered)
        advance(db_path, participant_id, round_index, 61)
        page.reload(wait_until='networkidle')
        page.locator('.pairs-grid .pair-tile').first.wait_for()
        assert page.locator('.pair-tile').count() == 8
        # Same background in viewport, panel and words: the condition must
        # remain visible during memorization (not just during acclimation).
        def check_color(selectors):
            colors = page.evaluate('''(selectors) => selectors.map(selector =>
                getComputedStyle(document.querySelector(selector)).backgroundColor)''', selectors)
            assert len(set(colors)) == 1, (condition, selectors, colors)
            assert colors[0] == expected_colors[condition], (condition, colors)
        check_color(['.ambient', '.study-card', '.pair-tile'])
        learning = page.locator('.pair-tile b').all_inner_texts()
        learned_words.append(learning)
        advance(db_path, participant_id, round_index, 136)
        page.reload(wait_until='networkidle')
        page.locator('.math-form input').wait_for()
        check_color(['.ambient', '.study-card', '.math-card', '.math-form input'])
        page.locator('.math-form input').fill('41')
        page.get_by_role('button', name='Submit', exact=True).click()
        assert '1' in page.locator('.math-card>small').inner_text()
        advance(db_path, participant_id, round_index, 166)
        page.reload(wait_until='networkidle')
        page.locator('.answers-grid input').first.wait_for()
        assert page.locator('.answers-grid input').count() == 8
        check_color(['.ambient', '.study-card', '.answer-field', '.answer-field input'])
        recall = page.locator('.answer-field b').all_inner_texts()
        assert all(a != b for a,b in zip(learning,recall)), 'Words were not independently shuffled'
        assert not page.locator('.review-item').count(), 'Answer key leaked before completion'
        page.wait_for_timeout(1050)
        assert page.locator('.answers-grid input').count() == 8, 'Recall auto-submitted immediately'
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), f'Horizontal overflow at {width}px'
        page.locator('.answers-grid input').first.fill('test')
        if round_index == 1:
            # Server moves beyond the recall deadline without receiving a POST.
            # Reloading then MUST lock and automatically submit the 8 answers.
            # On one device, simulate the first transmission failing, and ensure
            # the participant can retry without editing answers after expiry.
            if width == 390:
                page.route('**/rounds/1/submit',
                           lambda route: route.fulfill(status=503, content_type='application/json',
                                                       body='{"detail":"Temporary failure"}'), times=1)
            advance(db_path, participant_id, round_index, 287)
            page.reload(wait_until='networkidle')
            if width == 390:
                page.get_by_role('button', name='Retry saving').wait_for(timeout=12000)
                assert page.locator('.answers-grid input').first.is_disabled(), 'Answers remained editable after time expired'
                page.get_by_role('button', name='Retry saving').click()
        else:
            page.get_by_role('button', name='Submit answers').click()
        if round_index < 2:
            page.get_by_role('button', name='Start this round').wait_for(timeout=12000)
        else:
            page.locator('.results-review').wait_for(timeout=12000)
    assert set(conditions_seen) == set(expected_colors), conditions_seen
    with sqlite3.connect(db_path) as db:
        saved = db.execute('SELECT score,math_attempts,math_correct FROM study_results WHERE participant_id=? ORDER BY round_index',
                           (participant_id,)).fetchall()
        assert len(saved) == 3 and all(row[1] == 1 for row in saved), saved
        # The time-up path completed round 2 automatically, not by a click.
        after_timeout = db.execute('SELECT answers FROM study_results WHERE participant_id=? AND round_index=1',
                                   (participant_id,)).fetchone()
        assert after_timeout and 'test' in after_timeout[0], after_timeout
    assert page.locator('.review-round').count() == 3
    page.locator('.review-round summary').first.click()
    assert page.locator('.review-round').first.locator('.review-item').count() == 8
    assert page.locator('.results-overview').is_visible()
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), f'Overflow in results at {width}px'

    assert not errors, f'Browser exceptions at {width}: {errors}'
    print(f'PASS {width}×{height} mobile={mobile}, full 3-round flow, shuffle, arithmetic and review')
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
