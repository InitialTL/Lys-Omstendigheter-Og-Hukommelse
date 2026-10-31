import json
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
    assert (state['condition'],state['phase'],state['round_index']) == ('WARM','setup',0)
    assert 'pairs' not in state
    assert 'words' in state and state['words'] == []
    started = c.post(base + '/rounds/start').json()
    assert started['phase'] == 'acclimation'
    assert 'pairs' not in started
    assert 'words' in started and started['words'] == []
    clock['now'] += 60
    started = c.get(base + '/next').json()
    assert started['phase'] == 'learning'
    assert len(started['pairs']) == 10
    repeat = c.post(base + '/rounds/start').json()
    assert repeat['phase_end_at'] == started['phase_end_at']
    early = c.post(base + '/rounds/0/submit', json={'answers':['']*10,'hidden_count':0})
    assert early.status_code == 409
    clock['now'] += 61
    during = c.get(base + '/next').json()
    assert during['phase'] == 'distraction'
    assert 'pairs' not in during
    clock['now'] += 30
    recall = c.get(base + '/next').json()
    assert recall['phase'] == 'recall'
    assert len(recall['words']) == 10
    assert 'pairs' not in recall
    answers = [pair['meaning'] for pair in started['pairs']]
    submitted = c.post(base + '/rounds/0/submit', json={'answers': answers, 'hidden_count': 1})
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()['score'] == 10
    assert c.post(base + '/rounds/0/submit', json={'answers': answers}).status_code == 409
    next_state = c.get(base + '/next').json()
    assert next_state['phase'] == 'setup'
    assert next_state['condition'] == 'COOL'
    assert next_state['list_id'] != state['list_id']
    with database.connect() as db:
        row = db.execute('SELECT score,hidden_count,condition FROM study_results').fetchone()
    assert tuple(row) == (10, 1, 'WARM')


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
        clock['now'] += 95
        submitted = c.post(base + f'/rounds/{round_index}/submit', json={
            'answers':[item['meaning'] for item in started['pairs']], 'hidden_count':0
        })
        assert submitted.status_code == 200
    assert c.get(f'/api/participants/{pid}/next').json()['finished']
    assert c.get('/api/admin/export.csv').status_code == 503
    monkeypatch.setenv('STUDY_ADMIN_TOKEN', 'a-real-secret-used-only-for-tests')
    assert c.get('/api/admin/export.csv').status_code == 403
    export = c.get('/api/admin/export.csv', headers={'X-Admin-Token':'a-real-secret-used-only-for-tests'})
    assert export.status_code == 200
    assert len(export.text.strip().splitlines()) == 4
    assert 'COOL' in export.text and 'DARK' in export.text


def test_score_is_language_specific_and_normalized():
    score, correct = words.grade(0, 'nb', ['  STOL!','NOKKEL','eple','sykkel','lampe','bok','skje','vindu','sko','kopp'])
    assert score == 10 and all(correct)
    score_en, _ = words.grade(0,'en',['stol']*10)
    assert score_en == 0
    for lang in words.LANGUAGES:
        labels = [pair['meaning'] for pair in words.learning_pairs(0, lang)]
        assert words.grade(0, lang, labels)[0] == 10


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
    clock['now'] += 152
    assert c.post(base + '/rounds/0/submit', json={'answers':['']*10}).status_code == 200
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
    assert len(c.get(url + '/next').json()['pairs']) == 10


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
    clock['now'] += 150.01  # acclimation (60) + learning (60) + distraction (30)
    recall = c.get(base + '/next').json()
    assert recall['phase'] == 'recall'
    assert 119 < recall['phase_end_at'] - recall['server_now'] <= 120
    assert len(recall['words']) == 10
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0
    clock['now'] += 0.2
    unchanged = c.get(base + '/next').json()
    assert unchanged['phase'] == 'recall'
    assert unchanged['round_index'] == 0
    assert unchanged['phase_end_at'] > unchanged['server_now'] + 119
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0
