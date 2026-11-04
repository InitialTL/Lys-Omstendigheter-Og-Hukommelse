import json
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import database
import server
import words


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'study.db')
    database.init_db()
    server._registration_times.clear()
    fake_clock = {'now': 1_800_000_000.0}
    monkeypatch.setattr(database, 'time', SimpleNamespace(time=lambda: fake_clock['now']))
    return TestClient(server.app), fake_clock



def test_russian_word_pairs_registration_and_unicode_grading(client):
    c, clock = client
    assert words.normalize('  СТУЛ!! ') == 'стул'
    assert words.normalize('Ёж') == 'еж'
    assert words.normalize('máviko _ ') == 'maviko'
    assert words.normalize('ПЕРЧАТКА') == 'перчатка'
    assert words.TARGETS['bicycle']['ru'][0] == 'велосипед'

    created = c.post('/api/participants', json={
        'language': 'ru', 'age_band': '18_24',
        'gender': 'prefer_not', 'consent': True,
    })
    assert created.status_code == 201, created.text
    pid = created.json()['participant_id']
    c.headers['X-Participant-Token'] = created.json()['access_token']
    base = f'/api/participants/{pid}'
    assert c.post(base + '/rounds/start').status_code == 200
    clock['now'] += 60
    learning = c.get(base + '/next').json()
    assert learning['phase'] == 'learning'
    assert len(learning['pairs']) == 8
    assert all(any('а' <= ch.lower() <= 'я' for ch in p['meaning'])
               for p in learning['pairs'])
    clock['now'] += 106
    recall = c.get(base + '/next').json()
    assert recall['phase'] == 'recall'
    correct = {item['word']: item['meaning'].upper() for item in learning['pairs']}
    answers = [correct[word] for word in recall['words']]
    response = c.post(base + '/rounds/0/submit',
                      json={'answers': answers, 'hidden_count': 0})
    assert response.status_code == 200, response.text
    with database.connect() as db:
        row = db.execute(
            'SELECT score, max_score FROM study_results WHERE participant_id=?',
            (pid,),
        ).fetchone()
        assert tuple(row) == (8, 8)


def test_adding_russian_migrates_legacy_constraint_without_erasing_results(client):
    c, clock = client
    created = c.post('/api/participants', json={
        'language': 'nb', 'age_band': '18_24',
        'gender': 'prefer_not', 'consent': True,
    }).json()
    pid = created['participant_id']
    c.headers['X-Participant-Token'] = created['access_token']
    base = f'/api/participants/{pid}'
    c.post(base + '/rounds/start')
    clock['now'] += 166
    assert c.post(base + '/rounds/0/submit',
                  json={'answers': [''] * 8, 'hidden_count': 0}).status_code == 200

    # Recreate the historical participants CHECK constraint only; preserve
    # the real child result, participant credentials and started-round data.
    with sqlite3.connect(database.DB_PATH) as db:
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('BEGIN IMMEDIATE')
        old_sql = db.execute(
            "SELECT sql FROM sqlite_master WHERE name='study_participants'"
        ).fetchone()[0]
        assert "'ru'" in old_sql
        old_sql = old_sql.replace(
            'CREATE TABLE study_participants',
            'CREATE TABLE study_participants_pre_ru',
            1,
        ).replace(",'ru'", '')
        db.execute(old_sql)
        db.execute(
            'INSERT INTO study_participants_pre_ru SELECT * FROM study_participants'
        )
        db.execute('DROP TABLE study_participants')
        db.execute(
            'ALTER TABLE study_participants_pre_ru RENAME TO study_participants'
        )
        assert not db.execute('PRAGMA foreign_key_check').fetchall()

    # Real startup migration must be repeatable, and it must retain results.
    database.init_db()
    database.init_db()
    with database.connect() as db:
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute(
            'SELECT COUNT(*) FROM study_participants WHERE id=?', (pid,)
        ).fetchone()[0] == 1
        assert db.execute(
            'SELECT COUNT(*) FROM study_results WHERE participant_id=?', (pid,)
        ).fetchone()[0] == 1
        assert db.execute(
            'SELECT COUNT(*) FROM study_rounds WHERE participant_id=?', (pid,)
        ).fetchone()[0] == 1
        assert "'ru'" in db.execute(
            "SELECT sql FROM sqlite_master WHERE name='study_participants'"
        ).fetchone()[0]
    assert c.get(base + '/next').status_code == 200
    another = c.post('/api/participants', json={
        'language': 'ru', 'age_band': '25_44',
        'gender': 'prefer_not', 'consent': True,
    })
    assert another.status_code == 201, another.text


def test_balances_groups_and_orders(client):
    c, clock = client
    participants = [c.post('/api/participants', json={
        'language': 'nb', 'age_band': '16_17', 'gender': 'prefer_not', 'consent': True
    }).json() for _ in range(18)]
    assert [p['group'] for p in participants[:6]] == list('ABCABC')
    with database.connect() as db:
        assignments = db.execute('SELECT group_name, list_order FROM study_participants').fetchall()
    assert all(len({row['list_order'] for row in assignments if row['group_name'] == g}) == 6
               for g in 'ABC')


def test_experiment_flow_and_server_timers(client):
    c, clock = client
    p = c.post('/api/participants', json={
        'language':'nb','age_band':'18_24','gender':'prefer_not','consent':True
    })
    assert p.status_code == 201
    participant_id = p.json()['participant_id']
    c.headers['X-Participant-Token'] = p.json()['access_token']
    base = f'/api/participants/{participant_id}'
    state = c.get(base + '/next').json()
    assert (state['condition'],state['phase'],state['round_index']) == ('ORANGE','setup',0)
    assert 'pairs' not in state
    assert 'words' in state and state['words'] == []
    started = c.post(base + '/rounds/start').json()
    assert started['phase'] == 'acclimation'
    assert 'pairs' not in started
    assert 'words' in started and started['words'] == []
    clock['now'] += 60
    started = c.get(base + '/next').json()
    assert started['phase'] == 'learning'
    assert len(started['pairs']) == 8
    repeat = c.post(base + '/rounds/start').json()
    assert repeat['phase_end_at'] == started['phase_end_at']
    early = c.post(base + '/rounds/0/submit', json={'answers':['']*8,'hidden_count':0})
    assert early.status_code == 409
    clock['now'] += 76
    during = c.get(base + '/next').json()
    assert during['phase'] == 'distraction'
    assert 'pairs' not in during
    clock['now'] += 30
    recall = c.get(base + '/next').json()
    assert recall['phase'] == 'recall'
    assert len(recall['words']) == 8
    assert 'pairs' not in recall
    assert 'review' not in recall
    mapping = {pair['word']:pair['meaning'] for pair in started['pairs']}
    answers = [mapping[word] for word in recall['words']]
    submitted = c.post(base + '/rounds/0/submit', json={'answers': answers, 'hidden_count': 1})
    assert submitted.status_code == 200, submitted.text
    assert submitted.json().get('score') is None  # no premature scoring feedback
    assert c.post(base + '/rounds/0/submit', json={'answers': answers}).status_code == 409
    next_state = c.get(base + '/next').json()
    assert next_state['phase'] == 'setup'
    assert next_state['condition'] == 'BLUE'
    assert next_state['list_id'] != state['list_id']
    assert 'review' not in next_state
    with database.connect() as db:
        row = db.execute('SELECT score,hidden_count,condition FROM study_results').fetchone()
    assert tuple(row) == (8, 1, 'ORANGE')



def test_redeploy_reinitialization_preserves_completed_results_and_rejects_replay(client):
    """Reopen/migrate the exact same SQLite file, not a new in-memory database."""
    c, clock = client
    created = c.post('/api/participants', json={
        'language':'nb','age_band':'16_17','gender':'prefer_not','consent':True
    }).json()
    pid = created['participant_id']
    c.headers['X-Participant-Token'] = created['access_token']
    url = f'/api/participants/{pid}'
    for index in range(3):
        assert c.post(url + '/rounds/start').json()['phase'] == 'acclimation'
        clock['now'] += 166 + index
        saved = c.post(url + f'/rounds/{index}/submit', json={
            'answers': [''] * 8,
            'math_attempts': 2 + index,
            'math_correct': 1,
        })
        assert saved.status_code == 200, saved.text
    before = c.get(url + '/next').json()
    assert before['finished'] and before['results_saved']
    with database.connect() as db:
        original_rows = [
            tuple(row) for row in db.execute(
                'SELECT round_index,condition,score,answers,math_attempts FROM study_results '
                'WHERE participant_id=? ORDER BY round_index', (pid,)
            ).fetchall()
        ]
    assert len(original_rows) == 3
    db_path = database.DB_PATH
    # Multiple startups and schema checks must never overwrite the existing
    # participant, access token, completed rounds or scores.
    database.init_db()
    database.init_db()
    assert database.DB_PATH == db_path
    after = c.get(url + '/next').json()
    assert after['participant_id'] == pid
    assert after['finished'] and after['completed'] == 3
    assert after['perception_deadline_at'] == before['perception_deadline_at']
    assert c.post(url + '/rounds/start').status_code == 409
    assert c.post(url + '/rounds/2/submit', json={'answers':['wrong'] * 8}).status_code == 409
    assert c.post(url + '/rounds/2/draft', json={
        'revision':1, 'answers':['wrong'] * 8
    }).status_code == 409
    with database.connect() as db:
        new_rows = [
            tuple(row) for row in db.execute(
                'SELECT round_index,condition,score,answers,math_attempts FROM study_results '
                'WHERE participant_id=? ORDER BY round_index', (pid,)
            ).fetchall()
        ]
        assert new_rows == original_rows
        assert db.execute('SELECT COUNT(*) FROM study_participants WHERE id=?', (pid,)).fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM study_rounds WHERE participant_id=?', (pid,)).fetchone()[0] == 3
    # Withdrawal is the only in-app operation that clears the old identity.
    assert c.delete(url).status_code == 204
    assert c.get(url + '/next').status_code == 401
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?', (pid,)).fetchone()[0] == 0
    replacement = c.post('/api/participants', json={
        'language':'nb','age_band':'16_17','gender':'prefer_not','consent':True
    })
    assert replacement.status_code == 201
    assert replacement.json()['participant_id'] != pid


def test_cancel_acclimation_returns_to_setup_and_restarts_full_wait(client):
    c, clock = client
    registration = c.post('/api/participants', json={
        'language': 'en', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True
    }).json()
    pid = registration['participant_id']
    c.headers['X-Participant-Token'] = registration['access_token']
    base = f'/api/participants/{pid}'
    first = c.post(base + '/rounds/start').json()
    assert first['phase'] == 'acclimation'
    original_deadline = first['phase_end_at']

    # Missing, invalid and cross-participant sessions must not erase a round.
    cancel_url = base + '/rounds/0/cancel-acclimation'
    assert c.post(cancel_url, json={}).status_code == 422
    assert c.post(cancel_url, json={'expected_phase_end_at': original_deadline},
                  headers={'X-Participant-Token': 'wrong-token'}).status_code == 401
    assert c.post(base + '/rounds/1/cancel-acclimation', json={
        'expected_phase_end_at': original_deadline
    }).status_code == 409
    assert c.post(cancel_url, json={
        'expected_phase_end_at': original_deadline + 10
    }).status_code == 409

    clock['now'] += 15
    cancelled = c.post(cancel_url, json={'expected_phase_end_at': original_deadline})
    assert cancelled.status_code == 200
    assert cancelled.json()['phase'] == 'setup'
    assert cancelled.json()['round_index'] == 0
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_rounds WHERE participant_id=?', (pid,)).fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?', (pid,)).fetchone()[0] == 0

    assert c.post(cancel_url, json={'expected_phase_end_at': original_deadline}).status_code == 409
    clock['now'] += 0.5
    restarted = c.post(base + '/rounds/start').json()
    assert restarted['phase'] == 'acclimation'
    assert restarted['phase_end_at'] == pytest.approx(clock['now'] + 60)
    # An old request from another tab cannot delete the new timer.
    assert c.post(cancel_url, json={'expected_phase_end_at': original_deadline}).status_code == 409
    assert c.get(base + '/next').json()['phase'] == 'acclimation'
    clock['now'] += 60
    assert c.get(base + '/next').json()['phase'] == 'learning'
    assert c.post(cancel_url, json={
        'expected_phase_end_at': restarted['phase_end_at']
    }).status_code == 409
    assert c.get(base + '/next').json()['phase'] == 'learning'


def test_cancel_acclimation_boundary_is_server_enforced(client):
    c, clock = client
    p = c.post('/api/participants', json={
        'language':'nb','age_band':'16_17','gender':'prefer_not','consent':True
    }).json()
    pid = p['participant_id']
    c.headers['X-Participant-Token'] = p['access_token']
    base = f'/api/participants/{pid}'
    initial = c.post(base + '/rounds/start').json()
    clock['now'] += 60
    # At the exact 60-second boundary, the server must reject any cancellation.
    result = c.post(base + '/rounds/0/cancel-acclimation', json={
        'expected_phase_end_at': initial['phase_end_at']
    })
    assert result.status_code == 409
    assert c.get(base + '/next').json()['phase'] == 'learning'


def test_complete_three_rounds_and_export(client, monkeypatch):
    c, clock = client
    response = c.post('/api/participants', json={
        'language':'en','age_band':'25_44','gender':'woman','consent':True
    })
    pid = response.json()['participant_id']
    c.headers['X-Participant-Token'] = response.json()['access_token']
    for round_index in range(3):
        base = f'/api/participants/{pid}'
        started = c.post(base + '/rounds/start').json()
        assert started['phase'] == 'acclimation'
        clock['now'] += 60
        started = c.get(base + '/next').json()
        assert started['phase'] == 'learning'
        clock['now'] += 106
        recall = c.get(base + '/next').json()
        mapping = {item['word']:item['meaning'] for item in started['pairs']}
        submitted = c.post(base + f'/rounds/{round_index}/submit', json={
            'answers':[mapping[word] for word in recall['words']],
            'hidden_count':0, 'math_attempts':5, 'math_correct':4
        })
        assert submitted.status_code == 200
    final = c.get(f'/api/participants/{pid}/next').json()
    assert final['finished']
    assert 'review' not in final
    assert c.post(f'/api/participants/{pid}/perception', json={
        'perceived_difference':'SKIPPED','perceived_easiest':'SKIPPED'
    }).status_code == 201
    final = c.get(f'/api/participants/{pid}/next').json()
    assert len(final['review']) == 3
    assert all(x['score']==8 and len(x['items']) == 8 for x in final['review'])
    assert all(x['math_correct']==4 and x['math_attempts']==5 for x in final['review'])
    assert all(item['correct'] for round_ in final['review'] for item in round_['items'])
    assert c.get('/api/admin/export.csv').status_code == 503
    monkeypatch.setenv('STUDY_ADMIN_TOKEN', 'a-real-secret-used-only-for-tests')
    assert c.get('/api/admin/export.csv').status_code == 403
    export = c.get('/api/admin/export.csv', headers={'X-Admin-Token':'a-real-secret-used-only-for-tests'})
    assert export.status_code == 200
    assert len(export.text.strip().splitlines()) == 4
    assert 'BLUE' in export.text and 'NEUTRAL' in export.text


def test_score_is_language_specific_and_normalized():
    score, correct = words.grade(0, 'nb', ['  STOL!','NOKKEL','eple','sykkel','lampe','bok','skje','vindu'])
    assert score == 8 and all(correct)
    score_en, _ = words.grade(0,'en',['stol']*8)
    assert score_en == 0
    for lang in words.LANGUAGES:
        labels = [pair['meaning'] for pair in words.learning_pairs(0, lang)]
        assert words.grade(0, lang, labels)[0] == 8


def test_legacy_data_kept(tmp_path, monkeypatch):
    import sqlite3
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE experiment_results (id INTEGER PRIMARY KEY, score INTEGER)')
        db.execute('INSERT INTO experiment_results(id,score) VALUES (1,7)')
    monkeypatch.setattr(database, 'DB_PATH', path)
    database.init_db()
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT score FROM experiment_results').fetchone()[0] == 7


def test_withdrawal_deletes_study_data(client):
    c, clock = client
    result = c.post('/api/participants', json={
        'language':'nb','age_band':'16_17','gender':'prefer_not','consent':True
    }).json()
    pid = result['participant_id']
    c.headers['X-Participant-Token'] = result['access_token']
    base = f'/api/participants/{pid}'
    c.post(base + '/rounds/start')
    clock['now'] += 167
    assert c.post(base + '/rounds/0/submit', json={'answers':['']*8}).status_code == 200
    assert c.delete(base).status_code == 204
    assert c.get(base + '/next').status_code == 401
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM study_participants').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM study_rounds').fetchone()[0] == 0


def test_supported_languages_register_and_security_headers(client):
    c, clock = client
    for language in words.LANGUAGES:
        r = c.post('/api/participants', json={
            'language': language, 'age_band': '18_24', 'gender':'prefer_not', 'consent':True
        })
        assert r.status_code == 201, r.text
        c.headers['X-Participant-Token'] = r.json()['access_token']
        next_response = c.get(f"/api/participants/{r.json()['participant_id']}/next")
        assert next_response.json()['language'] == language
        assert next_response.headers['Cache-Control'] == 'no-store, private'
        assert next_response.headers['X-Frame-Options'] == 'DENY'
        assert next_response.headers['Referrer-Policy'] == 'no-referrer'
    assert c.post('/api/participants', json={
        'language':'unsupported','age_band':'18_24','gender':'prefer_not','consent':True
    }).status_code == 422
    assert c.post('/api/participants', json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True,
        'admin':True
    }).status_code == 422


def test_acclimation_is_server_enforced_and_survives_refresh(client):
    c, clock = client
    p = c.post('/api/participants', json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    c.headers['X-Participant-Token'] = p['access_token']
    p = p['participant_id']
    url = f'/api/participants/{p}'
    first = c.post(url + '/rounds/start').json()
    assert first['phase'] == 'acclimation'
    assert first['words'] == []
    assert 'pairs' not in first
    clock['now'] += 30
    assert c.get(url + '/next').json()['phase'] == 'acclimation'
    assert c.post(url + '/rounds/start').json()['phase_end_at'] == first['phase_end_at']
    clock['now'] += 29
    assert c.get(url + '/next').json()['phase'] == 'acclimation'
    clock['now'] += 1
    assert len(c.get(url + '/next').json()['pairs']) == 8


def test_old_v2_language_migration_preserves_results(client, monkeypatch):
    # Simulate a V2.0 table schema and data with old-language CHECK.
    import sqlite3
    path = database.DB_PATH
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('BEGIN IMMEDIATE')
        db.execute("""CREATE TABLE study_participants_old (
          id TEXT PRIMARY KEY, language TEXT NOT NULL CHECK(language IN ('nb','en')),
          age_band TEXT NOT NULL, gender TEXT NOT NULL,
          group_name TEXT NOT NULL CHECK(group_name IN ('A','B','C')),
          list_order TEXT NOT NULL, consented_at TEXT NOT NULL, created_at TEXT NOT NULL
        )""")
        db.execute('INSERT INTO study_participants_old SELECT id,language,age_band,gender,group_name,list_order,consented_at,created_at FROM study_participants')
        db.execute('DROP TABLE study_participants')
        db.execute('ALTER TABLE study_participants_old RENAME TO study_participants')
    database.init_db()
    with sqlite3.connect(path) as db:
        ddl = db.execute("SELECT sql FROM sqlite_master WHERE name='study_participants'").fetchone()[0]
        assert "'fr'" in ddl
    # Repeated migrations are safe.
    database.init_db()


def test_participant_bearer_token_required(client):
    c, clock = client
    r = c.post('/api/participants', json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    pid, secret = r['participant_id'], r['access_token']
    url = f'/api/participants/{pid}'
    assert len(secret) >= 40
    assert c.get(url + '/next').status_code == 401
    assert c.post(url + '/rounds/start').status_code == 401
    assert c.delete(url).status_code == 401
    assert c.get(url + '/next', headers={'X-Participant-Token':'wrong'}).status_code == 401
    assert c.get(url + '/next', headers={'X-Participant-Token':secret}).status_code == 200
    with database.connect() as db:
        row = db.execute('SELECT token_hash FROM study_participants WHERE id=?', (pid,)).fetchone()
        assert secret not in row['token_hash']


def test_protocol_versions_are_not_mixed(client):
    c, clock = client
    new = c.post('/api/participants', json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    assert new['access_token']
    with database.connect() as db:
        db.execute("UPDATE study_participants SET protocol_version='2.0' WHERE id=?",
                   (new['participant_id'],))
    assert c.get(f"/api/participants/{new['participant_id']}/next",
                 headers={'X-Participant-Token':new['access_token']}).status_code == 401
    # Old pilot participant is retained in the database instead of erased.
    with database.connect() as db:
        row = db.execute('SELECT protocol_version FROM study_participants WHERE id=?',
                         (new['participant_id'],)).fetchone()
    assert row['protocol_version'] == '2.0'


def test_registration_rate_limit(client):
    c, clock = client
    for i in range(30):
        r = c.post('/api/participants', json={
            'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
        })
        assert r.status_code == 201, (i, r.text)
    last = c.post('/api/participants', json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    })
    assert last.status_code == 429


def test_recall_has_full_time_after_distraction_and_is_not_auto_submitted(client):
    """Regression: the transition to recall must not save empty answers."""
    c, clock = client
    response = c.post('/api/participants', json={
        'language': 'en', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True
    }).json()
    pid = response['participant_id']
    c.headers['X-Participant-Token'] = response['access_token']
    base = f'/api/participants/{pid}'
    c.post(base + '/rounds/start')
    clock['now'] += 165.01  # acclimation (60) + learning (75) + distraction (30)
    recall = c.get(base + '/next').json()
    assert recall['phase'] == 'recall'
    assert 119 < recall['phase_end_at'] - recall['server_now'] <= 120
    assert len(recall['words']) == 8
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0
    clock['now'] += 0.2
    unchanged = c.get(base + '/next').json()
    assert unchanged['phase'] == 'recall'
    assert unchanged['round_index'] == 0
    assert unchanged['phase_end_at'] > unchanged['server_now'] + 119
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0


def test_reject_host_spoof_and_cross_site_writes(client):
    c, clock = client
    assert c.get('/api/health', headers={'Host':'attacker.example'}).status_code == 400
    other_site = c.post('/api/participants', headers={'Origin':'https://attacker.example'}, json={
        'language':'en', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
    })
    assert other_site.status_code == 403
    local = c.post('/api/participants', headers={'Origin':'http://localhost:5173'}, json={
        'language':'en', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
    })
    assert local.status_code == 201
    # Same host+port is accepted regardless of a nonstandard local test port.
    same_site = c.post('/api/participants', headers={'Origin':'http://testserver'}, json={
        'language':'en', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
    })
    assert same_site.status_code == 201


def test_api_rejects_oversized_payload_and_preserves_db(client):
    c, clock = client
    oversized = c.post('/api/participants', content='x'*9000, headers={
        'Content-Type':'application/json'
    })
    assert oversized.status_code == 413
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM study_participants').fetchone()[0] == 0


def test_sqlite_wal_and_balanced_registration_under_load(client):
    c, clock = client
    # The built-in abuse limit is 30 registrations per ten minutes per client.
    for index in range(30):
        response = c.post('/api/participants', json={
            'language':'nb', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
        })
        assert response.status_code == 201
    with database.connect() as db:
        counts = [db.execute('SELECT count(*) FROM study_participants WHERE group_name=?',(name,)).fetchone()[0]
                  for name in ('A','B','C')]
        assert counts == [10,10,10]
        assert db.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'


def test_untrusted_cloudflare_header_does_not_bypass_rate_limit(client, monkeypatch):
    c, clock = client
    monkeypatch.delenv('STUDY_TRUST_CLOUDFLARE', raising=False)
    for i in range(30):
        r = c.post('/api/participants', headers={'CF-Connecting-IP':f'192.0.2.{i+1}'}, json={
            'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
        })
        assert r.status_code == 201
    r = c.post('/api/participants', headers={'CF-Connecting-IP':'192.0.2.201'}, json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    })
    assert r.status_code == 429


def test_cloudflare_tunnel_rate_limit_keys_by_validated_ip(client, monkeypatch):
    c, clock = client
    monkeypatch.setenv('STUDY_TRUST_CLOUDFLARE', '1')
    # The test client is not a trusted localhost tunnel and cannot spoof the header.
    for i in range(30):
        assert c.post('/api/participants', headers={'CF-Connecting-IP':f'192.0.2.{i+1}'}, json={
            'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
        }).status_code == 201
    assert c.post('/api/participants', headers={'CF-Connecting-IP':'198.51.100.22'}, json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).status_code == 429


def test_reject_streamed_oversized_body_without_content_length(client):
    c, clock = client
    streamed = (part for part in (b'{"language":"en",', b' '*9000, b'}'))
    response = c.post('/api/participants', content=streamed,
                      headers={'Content-Type':'application/json'})
    assert response.status_code == 413, response.text


def test_independent_randomized_order_and_completed_feedback(client):
    c, clock = client
    p = c.post('/api/participants', json={
        'language':'nb','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    pid = p['participant_id']
    c.headers['X-Participant-Token'] = p['access_token']
    path = f'/api/participants/{pid}'
    assert 'review' not in c.get(path + '/next').json()
    for i in range(3):
        start = c.post(path + '/rounds/start').json()
        assert start['phase'] == 'acclimation'
        assert 'learning_order' not in start and 'recall_order' not in start
        with database.connect() as db:
            row = db.execute('SELECT learning_order,recall_order FROM study_rounds WHERE participant_id=? AND round_index=?',
                             (pid,i)).fetchone()
            learning_order, recall_order = map(json.loads, row)
            assert sorted(learning_order) == sorted(recall_order) == list(range(8))
            assert all(a != b for a,b in zip(learning_order,recall_order))
        clock['now'] += 60
        learning = c.get(path + '/next').json()
        assert len(learning['pairs']) == 8
        assert 'review' not in learning
        assert c.post(path+'/rounds/start').json()['phase_end_at'] == learning['phase_end_at']
        clock['now'] += 106
        recall = c.get(path+'/next').json()
        assert recall['phase'] == 'recall'
        assert 'review' not in recall
        visible = [x['word'] for x in learning['pairs']]
        assert all(a != b for a,b in zip(visible,recall['words']))
        by_word = {x['word']:x['meaning'] for x in learning['pairs']}
        answers = [by_word[word] for word in recall['words']]
        if i == 1: answers[0] = 'incorrect'
        bad = c.post(path+f'/rounds/{i}/submit',json={'answers':answers,'math_attempts':2,'math_correct':3})
        assert bad.status_code == 422
        response = c.post(path+f'/rounds/{i}/submit',json={
            'answers':answers,'math_attempts':5,'math_correct':4,
        })
        assert response.status_code == 200
        assert response.json() == {'saved':True}
        if i != 2:
            assert 'review' not in c.get(path+'/next').json()
    end = c.get(path+'/next').json()
    assert end['finished']
    assert 'review' not in end
    assert c.post(path+'/perception', json={
        'perceived_difference':'NONE', 'perceived_easiest':'SAME'
    }).status_code == 201
    end = c.get(path+'/next').json()
    assert [r['score'] for r in end['review']] == [8,7,8]
    assert all(x['math_attempts']==5 and x['math_correct']==4 for x in end['review'])
    assert end['review'][1]['items'][0]['correct'] is False
    assert end['review'][1]['items'][0]['answer'] == 'incorrect'
    assert end['review'][1]['items'][0]['expected']
    assert c.get(path+'/next',headers={'X-Participant-Token':'invalid'}).status_code == 401


def test_language_grading_and_shuffle_by_language():
    for lang in words.LANGUAGES:
        mapping = list(reversed(range(8)))
        labels = words.learning_pairs(0,lang,mapping)
        assert len(labels) == 8
        assert words.grade(0,lang,[x['meaning'] for x in labels],mapping)[0] == 8
        assert words.recall_words(0,mapping) == [x['word'] for x in labels]
    with pytest.raises(ValueError):
        words.grade(0,'en',['chair'],list(range(8)))
    with pytest.raises(ValueError):
        words.grade(0,'en',['']*8,[0]*8)


def test_legacy_schema_migration_keeps_v22_results(tmp_path, monkeypatch):
    import sqlite3
    path = tmp_path / 'legacy_v22.db'
    monkeypatch.setattr(database, 'DB_PATH', path)
    database.init_db()
    with database.connect() as db:
        db.execute('''INSERT INTO study_participants
            (id,language,age_band,gender,group_name,list_order,consented_at,created_at,protocol_version,token_hash)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            ('old-session','en','18_24','prefer_not','A','[0,1,2]','old','old','2.2','old-hash'))
        db.execute('''INSERT INTO study_rounds (participant_id,round_index,started_at,learning_order,recall_order)
                      VALUES (?,?,?,?,?)''',('old-session',0,100,'[0,1,2,3,4,5,6,7]','[7,6,5,4,3,2,1,0]'))
        db.execute('''INSERT INTO study_results (participant_id,round_index,condition,list_id,answers,score,max_score,
             recall_seconds,hidden_count,submitted_late,completed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            ('old-session',0,'WARM',0,'["stol"]',4,10,100,0,0,'old'))
    # Simulate the pre-v2.3 fixed six-language CHECK constraint.
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('BEGIN IMMEDIATE')
        db.execute('''CREATE TABLE legacy_participants (
              id TEXT PRIMARY KEY,language TEXT NOT NULL CHECK(language IN ('nb','en','sv','de','fr','es')),
              age_band TEXT NOT NULL, gender TEXT NOT NULL, group_name TEXT NOT NULL,
              list_order TEXT NOT NULL, consented_at TEXT NOT NULL, created_at TEXT NOT NULL,
              protocol_version TEXT NOT NULL DEFAULT '2.1', token_hash TEXT)''')
        db.execute('INSERT INTO legacy_participants SELECT * FROM study_participants')
        db.execute('DROP TABLE study_participants')
        db.execute('ALTER TABLE legacy_participants RENAME TO study_participants')
    database.init_db()
    with database.connect() as db:
        assert db.execute("SELECT score,max_score FROM study_results WHERE participant_id='old-session'").fetchone()[:] == (4,10)
        assert db.execute("SELECT protocol_version FROM study_participants WHERE id='old-session'").fetchone()[0] == '2.2'
        assert db.execute("SELECT 1 FROM study_participants").fetchone()
    new = database.create_participant('ro','18_24','prefer_not')
    assert new['group'] == 'A'  # Old sessions excluded from balancing
    database.init_db()  # idempotent


def test_v24_conditions_and_approximate_relative_srgb_luminance(client):
    import math
    c, _ = client
    assert database.PROTOCOL_VERSION == '2.7'
    assert database.CONDITIONS == ('ORANGE', 'BLUE', 'NEUTRAL')
    colors = c.get('/api/config').json()['conditions']
    assert set(colors) == set(database.CONDITIONS)
    assert [colors[name]['hex'] for name in database.CONDITIONS] == ['#F0A34B','#8AB7EA','#B3B3B3']

    def y(hexcode):
        rgb = [int(hexcode[i:i+2],16)/255 for i in (1,3,5)]
        linear = [value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4 for value in rgb]
        return sum(a*b for a,b in zip(linear, (.2126,.7152,.0722)))

    levels = [y(colors[name]['hex']) for name in database.CONDITIONS]
    assert max(levels) - min(levels) < 0.005, levels
    assert all(math.isfinite(value) for value in levels)
    assert 'not physically calibrated' in c.get('/api/config').json()['measurement']


def test_v23_data_are_preserved_and_not_accepted_as_new_sessions(client):
    c, _ = client
    old = c.post('/api/participants', json={
        'language':'nb', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
    }).json()
    with database.connect() as db:
        db.execute("UPDATE study_participants SET protocol_version='2.3' WHERE id=?", (old['participant_id'],))
        db.execute("INSERT INTO study_results (participant_id,round_index,condition,list_id,answers,score,max_score,recall_seconds,completed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                   (old['participant_id'],0,'WARM',0,'[]',5,8,75,'2026-10-31'))
    response = c.get(f"/api/participants/{old['participant_id']}/next",
                     headers={'X-Participant-Token': old['access_token']})
    assert response.status_code == 401
    with database.connect() as db:
        old_count = db.execute("SELECT count(*) FROM study_results WHERE participant_id=? AND condition='WARM'", (old['participant_id'],)).fetchone()[0]
    assert old_count == 1
    new = c.post('/api/participants', json={
        'language':'nb', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
    }).json()
    assert new['group'] == 'A'  # group balance only counts 2.5
    with database.connect() as db:
        assert db.execute("SELECT protocol_version FROM study_participants WHERE id=?", (new['participant_id'],)).fetchone()[0] == '2.7'


def test_v24_same_color_codes_not_mixed_into_new_protocol(client):
    c, _ = client
    previous = c.post('/api/participants', json={
        'language': 'nb', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True
    }).json()
    with database.connect() as db:
        db.execute("UPDATE study_participants SET protocol_version='2.4' WHERE id=?", (previous['participant_id'],))
        db.execute("INSERT INTO study_results (participant_id,round_index,condition,list_id,answers,score,max_score,recall_seconds,completed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                   (previous['participant_id'], 0, 'ORANGE', 0, '[]', 6, 8, 80, '2026-11-01'))
    assert c.get(f"/api/participants/{previous['participant_id']}/next",
                 headers={'X-Participant-Token': previous['access_token']}).status_code == 401
    new = c.post('/api/participants', json={
        'language': 'nb', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True
    }).json()
    assert new['group'] == 'A'  # Older cohorts are not counted in balancing.
    with database.connect() as db:
        assert db.execute("SELECT score FROM study_results WHERE participant_id=?", (previous['participant_id'],)).fetchone()[0] == 6
        assert db.execute("SELECT protocol_version FROM study_participants WHERE id=?", (new['participant_id'],)).fetchone()[0] == database.PROTOCOL_VERSION


def test_perception_is_optional_post_study_private_and_single_submission(client, monkeypatch):
    c, clock = client
    response = c.post('/api/participants', json={
        'language':'nb', 'age_band':'18_24', 'gender':'prefer_not', 'consent':True
    })
    pid = response.json()['participant_id']
    token = response.json()['access_token']
    path = f'/api/participants/{pid}/perception'
    payload = {'perceived_difference': 'SMALL', 'perceived_easiest': 'BLUE'}
    assert c.post(path, json=payload).status_code == 401
    c.headers['X-Participant-Token'] = token
    assert c.get(f'/api/participants/{pid}/next').json()['finished'] is False
    assert c.post(path, json=payload).status_code == 409
    assert c.post(path, json={**payload, 'extra':'unexpected'}).status_code == 422
    assert c.post(path, json={**payload, 'perceived_easiest':'BAD'}).status_code == 422
    assert c.post(path, json={'perceived_difference':'SKIPPED', 'perceived_easiest':'BLUE'}).status_code == 422
    for idx in range(3):
        c.post(f'/api/participants/{pid}/rounds/start')
        clock['now'] += 170
        result = c.post(f'/api/participants/{pid}/rounds/{idx}/submit',json={'answers':['']*8})
        assert result.status_code == 200, result.text
    before = c.get(f'/api/participants/{pid}/next').json()
    assert before['finished'] and before['perception_done'] is False
    assert 'review' not in before
    submitted = c.post(path,json=payload)
    assert submitted.status_code == 201, submitted.text
    again = c.post(path,json=payload)
    assert again.status_code == 409
    after = c.get(f'/api/participants/{pid}/next').json()
    assert after['perception_done'] is True
    assert len(after['review']) == 3
    with database.connect() as db:
        saved = db.execute('SELECT perceived_difference,perceived_easiest FROM study_perceptions WHERE participant_id=?', (pid,)).fetchone()
        assert tuple(saved) == ('SMALL','BLUE')
    assert c.get('/api/admin/perceptions.csv').status_code == 503
    monkeypatch.setenv('STUDY_ADMIN_TOKEN','long-secret-for-test-only')
    assert c.get('/api/admin/perceptions.csv').status_code == 403
    exported = c.get('/api/admin/perceptions.csv',headers={'X-Admin-Token':'long-secret-for-test-only'})
    assert exported.status_code == 200 and 'SMALL' in exported.text and 'BLUE' in exported.text
    assert c.delete(f'/api/participants/{pid}').status_code == 204
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_perceptions WHERE participant_id=?',(pid,)).fetchone()[0] == 0


def test_skipping_perception_allows_review_and_creates_no_score(client):
    c, clock = client
    registered = c.post('/api/participants',json={
        'language':'en','age_band':'25_44','gender':'prefer_not','consent':True
    }).json()
    pid = registered['participant_id']
    c.headers['X-Participant-Token'] = registered['access_token']
    for idx in range(3):
        c.post(f'/api/participants/{pid}/rounds/start')
        clock['now'] += 170
        assert c.post(f'/api/participants/{pid}/rounds/{idx}/submit',json={'answers':['']*8}).status_code == 200
    assert c.post(f'/api/participants/{pid}/perception',json={
        'perceived_difference':'SKIPPED', 'perceived_easiest':'SKIPPED'
    }).status_code == 201
    next_state=c.get(f'/api/participants/{pid}/next').json()
    assert next_state['finished'] and next_state['perception_done']
    assert len(next_state['review']) == 3
    with database.connect() as db:
        row = db.execute('SELECT perceived_difference,perceived_easiest FROM study_perceptions WHERE participant_id=?',(pid,)).fetchone()
        assert tuple(row) == ('SKIPPED','SKIPPED')
        assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?',(pid,)).fetchone()[0] == 3


def test_v25_is_retained_but_cannot_reenter_v26(client):
    c, _ = client
    p=c.post('/api/participants',json={'language':'en','age_band':'18_24','gender':'prefer_not','consent':True}).json()
    with database.connect() as db:
        db.execute("UPDATE study_participants SET protocol_version='2.5' WHERE id=?",(p['participant_id'],))
    assert c.get(f"/api/participants/{p['participant_id']}/next",headers={'X-Participant-Token':p['access_token']}).status_code == 401
    with database.connect() as db:
        assert db.execute('SELECT protocol_version FROM study_participants WHERE id=?',(p['participant_id'],)).fetchone()[0]=='2.5'


def test_feedback_timeout_keeps_all_three_results_and_unanswered_is_not_skipped(client, monkeypatch):
    """Closing the browser at the optional questions must never lose recall scores."""
    c, clock = client
    p = c.post('/api/participants', json={
        'language': 'en', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True,
    }).json()
    pid = p['participant_id']
    c.headers['X-Participant-Token'] = p['access_token']
    for index in range(3):
        c.post(f'/api/participants/{pid}/rounds/start')
        clock['now'] += 167
        answer = c.post(f'/api/participants/{pid}/rounds/{index}/submit', json={
            'answers': [''] * 8, 'math_attempts': 2, 'math_correct': 1
        })
        assert answer.status_code == 200, answer.text
        with database.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?', (pid,)).fetchone()[0] == index + 1
    # The entire objective study is persisted before the subjective form is shown.
    before = c.get(f'/api/participants/{pid}/next').json()
    assert before['finished'] and before['results_saved']
    assert not before['perception_done']
    assert 'review' not in before
    deadline = before['perception_deadline_at']
    assert 89 <= deadline - clock['now'] <= database.PERCEPTION_SECONDS
    assert c.get('/api/config').json()['perception_seconds'] == 90

    clock['now'] = deadline - .01
    assert not c.get(f'/api/participants/{pid}/next').json()['perception_done']
    # Simulate closing the browser instead of ever submitting the form.
    clock['now'] = deadline + .01
    after = c.get(f'/api/participants/{pid}/next').json()
    assert after['perception_done'] and after['perception_timed_out']
    assert len(after['review']) == 3
    assert all(r['score'] == 0 and r['max_score'] == 8 for r in after['review'])
    assert c.post(f'/api/participants/{pid}/perception', json={
        'perceived_difference': 'NONE', 'perceived_easiest': 'SAME'
    }).status_code == 409
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results WHERE participant_id=?', (pid,)).fetchone()[0] == 3
        assert db.execute('SELECT COUNT(*) FROM study_perceptions WHERE participant_id=?', (pid,)).fetchone()[0] == 0
    monkeypatch.setenv('STUDY_ADMIN_TOKEN', 'sample-admin-token')
    rows = c.get('/api/admin/export.csv', headers={'X-Admin-Token':'sample-admin-token'})
    assert rows.status_code == 200
    assert len(rows.text.splitlines()) == 4


def test_feedback_deadline_persists_and_timely_choice_is_saved(client):
    c, clock = client
    p = c.post('/api/participants', json={
        'language': 'nb', 'age_band': '16_17', 'gender': 'prefer_not', 'consent': True,
    }).json()
    pid = p['participant_id']
    c.headers['X-Participant-Token'] = p['access_token']
    for i in range(3):
        c.post(f'/api/participants/{pid}/rounds/start')
        clock['now'] += 166
        assert c.post(f'/api/participants/{pid}/rounds/{i}/submit', json={'answers':[''] * 8}).status_code == 200
    url = f'/api/participants/{pid}'
    deadline = c.get(url + '/next').json()['perception_deadline_at']
    database.init_db()  # restart-like migration / DB reopening
    assert c.get(url + '/next').json()['perception_deadline_at'] == deadline
    clock['now'] = deadline - 2
    saved = c.post(url + '/perception', json={
        'perceived_difference': 'SMALL', 'perceived_easiest': 'BLUE'
    })
    assert saved.status_code == 201
    clock['now'] = deadline + 120
    after = c.get(url + '/next').json()
    assert after['perception_done'] and not after['perception_timed_out']
    with database.connect() as db:
        assert tuple(db.execute('SELECT perceived_difference, perceived_easiest FROM study_perceptions WHERE participant_id=?', (pid,)).fetchone()) == ('SMALL','BLUE')


def test_v26_data_remain_saved_but_not_reused_in_v27(client):
    c, _ = client
    p = c.post('/api/participants', json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    with database.connect() as db:
        db.execute('UPDATE study_participants SET protocol_version=? WHERE id=?', ('2.6', p['participant_id']))
    assert c.get(f"/api/participants/{p['participant_id']}/next",
                 headers={'X-Participant-Token':p['access_token']}).status_code == 401
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_participants WHERE id=?',(p['participant_id'],)).fetchone()[0] == 1

# Recovery and deadline checks for the deployment-readiness patch.
def test_recall_checkpoint_survives_disconnect_and_restart(client, monkeypatch):
    c, clock = client
    participant = c.post('/api/participants', json={
        'language': 'en', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True,
    }).json()
    pid = participant['participant_id']
    url = f'/api/participants/{pid}'
    c.headers['X-Participant-Token'] = participant['access_token']
    assert c.post(url + '/rounds/0/draft', json={'revision': 1, 'answers': ['a'] * 8}).status_code == 409
    assert c.post(url + '/rounds/start').status_code == 200
    clock['now'] += database.ACCLIMATION_SECONDS + database.LEARN_SECONDS + database.DISTRACT_SECONDS
    saved = c.post(url + '/rounds/0/draft', json={'revision': 1, 'answers': ['chair'] + [''] * 7})
    assert saved.status_code == 200 and saved.json() == {'saved': True, 'revision': 1}
    # Simulate worker restart and a new browser retrieving the same server state.
    database.init_db()
    next_state = c.get(url + '/next').json()
    assert next_state['draft_revision'] == 1
    assert next_state['draft_answers'] == ['chair'] + [''] * 7
    # The authenticated admin can export unfinished checkpoints but they are
    # never silently treated as study_results / finished participant data.
    assert database.export_drafts()[0]['revision'] == 1
    assert c.get('/api/admin/drafts.csv').status_code == 503
    monkeypatch.setenv('STUDY_ADMIN_TOKEN', 'only-for-tests')
    assert c.get('/api/admin/drafts.csv').status_code == 403
    export = c.get('/api/admin/drafts.csv', headers={'X-Admin-Token': 'only-for-tests'})
    assert export.status_code == 200 and pid in export.text
    assert c.get(url + '/next').json()['finished'] is False
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0


def test_checkpoint_revision_order_auth_and_expired_replay(client):
    c, clock = client
    p = c.post('/api/participants', json={
        'language': 'en', 'age_band': '18_24', 'gender': 'prefer_not', 'consent': True,
    }).json()
    url = f"/api/participants/{p['participant_id']}"
    assert c.post(url+'/rounds/0/draft',json={'revision':1,'answers':['x']*8}).status_code == 401
    c.headers['X-Participant-Token'] = p['access_token']
    c.post(url+'/rounds/start')
    clock['now'] += 165
    good = ['one'] + [''] * 7
    newer = ['two'] + [''] * 7
    assert c.post(url+'/rounds/0/draft',json={'revision':2,'answers':newer}).json()['saved']
    stale = c.post(url+'/rounds/0/draft',json={'revision':1,'answers':good})
    assert stale.status_code == 200 and stale.json() == {'saved':False,'revision':2}
    assert c.get(url+'/next').json()['draft_answers'] == newer
    assert c.post(url+'/rounds/0/draft',json={'revision':3,'answers':['a'*81]+['']*7}).status_code == 422
    assert c.post(url+'/rounds/0/draft',json={'revision':3,'answers':['']*7}).status_code == 422
    clock['now'] += database.RECALL_SECONDS + 1
    assert c.post(url+'/rounds/0/draft',json={'revision':3,'answers':['changed']*8}).status_code == 409
    # Client sends forged correct answers after the cutoff, which MUST NOT be
    # considered in scoring. Only the pre-deadline checkpoint is eligible.
    state = c.get(url+'/next').json()
    forged = ['apple'] * 8
    completed = c.post(url+'/rounds/0/submit',json={'answers':forged})
    assert completed.status_code == 200
    with database.connect() as db:
        row = db.execute('SELECT answers,score,submitted_late FROM study_results').fetchone()
        assert json.loads(row['answers']) == newer
        assert row['submitted_late'] == 1
        assert row['score'] <= 1
        assert db.execute('SELECT COUNT(*) FROM study_drafts').fetchone()[0] == 0


def test_early_submission_uses_latest_answers_and_cleans_checkpoint(client):
    c,clock = client
    p=c.post('/api/participants',json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    c.headers['X-Participant-Token']=p['access_token']
    url=f"/api/participants/{p['participant_id']}"
    c.post(url+'/rounds/start')
    clock['now']+=165
    c.post(url+'/rounds/0/draft',json={'revision':1,'answers':['']*8})
    state=c.get(url+'/next').json()
    expected={pair['word']:pair['meaning'] for pair in __import__('words').learning_pairs(state['list_id'],'en')}
    answers=[expected[word] for word in state['words']]
    assert c.post(url+'/rounds/0/submit',json={'answers':answers}).status_code==200
    with database.connect() as db:
        result=db.execute('SELECT score,submitted_late,answers FROM study_results').fetchone()
        assert result['score']==8 and result['submitted_late']==0
        assert json.loads(result['answers'])==answers
        assert db.execute('SELECT COUNT(*) FROM study_drafts').fetchone()[0]==0
    assert c.post(url+'/rounds/0/draft',json={'revision':4,'answers':answers}).status_code==409


def test_withdrawal_also_removes_unfinished_checkpoint(client):
    c,clock=client
    p=c.post('/api/participants',json={
        'language':'nb','age_band':'16_17','gender':'prefer_not','consent':True
    }).json()
    c.headers['X-Participant-Token']=p['access_token']
    url=f"/api/participants/{p['participant_id']}"
    c.post(url+'/rounds/start')
    clock['now']+=165
    assert c.post(url+'/rounds/0/draft',json={'revision':1,'answers':['stol']+['']*7}).status_code==200
    assert c.delete(url).status_code==204
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_drafts').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM study_participants').fetchone()[0]==0


def test_late_post_without_checkpoint_scores_no_unsaved_answers(client):
    c,clock=client
    p=c.post('/api/participants',json={
        'language':'en','age_band':'18_24','gender':'prefer_not','consent':True
    }).json()
    c.headers['X-Participant-Token']=p['access_token']
    url=f"/api/participants/{p['participant_id']}"
    c.post(url+'/rounds/start')
    clock['now']+=165+database.RECALL_SECONDS+20
    assert c.post(url+'/rounds/0/submit',json={'answers':['apple']*8}).status_code==200
    with database.connect() as db:
        row=db.execute('SELECT score,answers,submitted_late FROM study_results').fetchone()
        assert row['score']==0 and json.loads(row['answers'])==['']*8
        assert row['submitted_late']==1
