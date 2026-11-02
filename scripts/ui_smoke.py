"""Chromium E2E smoke test for real React+FastAPI integration.

CI only. Starts a temporary SQLite-backed server and a browser; no network
analytics, paid API, or existing participant data is used.
"""
from __future__ import annotations
import os
import json
import sqlite3
from datetime import datetime, timezone
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
    # Languages default to browser preference; the registration control is prominent.
    assert page.locator('#registration-language').input_value() == 'en'
    assert page.locator('#page-language').input_value() == 'en'
    assert page.locator('#registration-language').is_visible()
    assert page.locator('#study-os').count() == 0
    if width <= 390:
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Intro horizontal overflow'
        assert page.locator('.topbar .language-switch label').is_visible(), 'Mobile language label hidden'
    page.locator('.consent-control input').check()
    page.get_by_role('button', name='Begin experiment').click()
    try:
        page.locator('.calibration-checklist').wait_for(timeout=10000)
    except Exception as exc:
        raise AssertionError(f'Calibration was not shown at {width}px. Page text: {page.locator("body").inner_text()[:750]}; console: {errors}') from exc
    assert page.locator('#study-os').count() == 0, 'Manual OS selector still required'
    assert page.locator('.os-guide').is_visible()
    assert page.locator('.os-guide p').first.inner_text().strip()
    assert page.locator('.external-screen-tip summary').count() == 1
    assert page.get_by_role('heading', name='Can you distinguish the symbols from their backgrounds?').is_visible()
    calibration_text = page.locator('.calibration-visual').inner_text().lower()
    assert 'remain visible at every brightness setting' in calibration_text
    assert 'halfway on your device slider' in calibration_text
    assert 'barely visible' not in page.locator('body').inner_text().lower()
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Calibration overflow'
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
        rendered = page.locator('.experiment-surface').evaluate('(node) => getComputedStyle(node).backgroundColor')
        assert rendered == expected_colors[condition], (condition, rendered)
        assert page.locator('.acclimation-screen').evaluate('(node) => getComputedStyle(node).backgroundColor') == 'rgba(0, 0, 0, 0)'
        assert page.locator('.experiment-surface').evaluate('(node) => getComputedStyle(node).transitionDuration') == '1.85s' 
        advance(db_path, participant_id, round_index, 61)
        page.reload(wait_until='networkidle')
        page.locator('.pairs-grid .pair-tile').first.wait_for()
        assert page.locator('.pair-tile').count() == 8
        # The stimulus is a SINGLE background surface. Cards, words and inputs
        # are transparent, preventing an unintentional white flash.
        def check_color(selectors):
            assert page.locator('.experiment-surface').evaluate('(node) => getComputedStyle(node).backgroundColor') == expected_colors[condition]
            colors = page.evaluate('''(selectors) => selectors.map(selector =>
                getComputedStyle(document.querySelector(selector)).backgroundColor)''', selectors)
            assert all(x == 'rgba(0, 0, 0, 0)' for x in colors), (condition, selectors, colors)
        check_color(['.ambient', '.study-card', '.pair-tile', '.study-header > .brand', '.brand-mark'])
        learning = page.locator('.pair-tile b').all_inner_texts()
        learned_words.append(learning)
        advance(db_path, participant_id, round_index, 136)
        page.reload(wait_until='networkidle')
        page.locator('.math-form input').wait_for()
        check_color(['.ambient', '.study-card', '.math-card', '.math-form input'])
        # The equation's question mark must no longer have a bright accent tint.
        ink,mark = page.locator('.math-expression').evaluate('''el => [getComputedStyle(el).color,
            getComputedStyle(el.querySelector('.math-unknown')).color]''')
        assert mark == ink, (mark, ink)
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
        # The server must have a pre-deadline checkpoint before any final submit.
        page.get_by_text('Answers backed up to the server.').wait_for(timeout=8000)
        with sqlite3.connect(db_path) as db:
            draft = db.execute('SELECT answers,revision FROM study_drafts WHERE participant_id=? AND round_index=?',
                               (participant_id,round_index)).fetchone()
            assert draft and json.loads(draft[0])[0] == 'test' and draft[1] > 0, draft
        if round_index == 0:
            # Simulate a closed tab / browser refresh without final submission.
            # The server checkpoint must restore the answer, not merely localStorage.
            page.evaluate('localStorage.removeItem(`lm_v2_draft_${localStorage.getItem("lm_v2_participant")}_0`)')
            page.reload(wait_until='networkidle')
            page.locator('.answers-grid input').first.wait_for()
            assert page.locator('.answers-grid input').first.input_value() == 'test', 'Server checkpoint was lost on reload'
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
            page.locator('.perception-main').wait_for(timeout=12000)
            assert page.locator('.results-review').count() == 0
            # Objective data must already be committed before the optional form.
            with sqlite3.connect(db_path) as db:
                assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?', (participant_id,)).fetchone()[0] == 3
            clock_text = page.locator('.perception-countdown').inner_text()
            assert clock_text.startswith('01:'), clock_text
            assert '3 of 3 rounds saved' in page.locator('.perception-save-status').inner_text()
            if width == 320:
                # Simulate abandoning the questionnaire without sending a response.
                # Change only the test DB timestamp to avoid a real 90-second wait.
                with sqlite3.connect(db_path) as db:
                    db.execute('UPDATE study_results SET completed_at=? WHERE participant_id=? AND round_index=2',
                               (datetime.fromtimestamp(time.time()-95, timezone.utc).isoformat(timespec='milliseconds'), participant_id))
                page.reload(wait_until='networkidle')
                page.locator('.results-review').wait_for(timeout=12000)
            elif width == 390:
                page.get_by_role('button',name='Skip these questions').click()
                page.locator('.results-review').wait_for(timeout=12000)
            else:
                page.locator('input[name="difference"][value="SMALL"]').check()
                page.locator('input[name="easiest"][value="BLUE"]').check()
                page.get_by_role('button', name='See my results').click()
                page.locator('.results-review').wait_for(timeout=12000)
    assert set(conditions_seen) == set(expected_colors), conditions_seen
    with sqlite3.connect(db_path) as db:
        saved = db.execute('SELECT score,math_attempts,math_correct FROM study_results WHERE participant_id=? ORDER BY round_index',
                           (participant_id,)).fetchall()
        perception = db.execute('SELECT perceived_difference,perceived_easiest FROM study_perceptions WHERE participant_id=?',
                                (participant_id,)).fetchone()
        if width == 320:
            # An uncompleted optional questionnaire is genuinely missing, not SKIPPED.
            assert perception is None
        else:
            assert perception is not None
            assert perception[0] == ('SKIPPED' if width == 390 else 'SMALL'), perception
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
    print(f'PASS {width}×{height} mobile={mobile}, muted question mark, 3 saved rounds and optional feedback timeout')
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
                    mobile_context = browser.new_context(
                        viewport={'width': 375, 'height': 812}, locale='nb-NO',
                        is_mobile=True, has_touch=True,
                        user_agent='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/125.0 Mobile Safari/537.36')
                    mobile_page = mobile_context.new_page()
                    mobile_page.goto(BASE, wait_until='networkidle')
                    assert mobile_page.locator('#registration-language').input_value() == 'nb'
                    mobile_page.locator('.consent-control input').check()
                    mobile_page.get_by_role('button', name='Start forsøket').click()
                    mobile_page.locator('.os-guide').wait_for()
                    assert 'Android' in mobile_page.locator('.os-guide p').first.inner_text()
                    assert mobile_page.locator('#study-os').count() == 0
                    assert not mobile_page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    mobile_context.close()
                    print('PASS mobile Norwegian browser language and automatic Android guidance')
                finally:
                    browser.close()
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill()


if __name__ == '__main__':
    main()
