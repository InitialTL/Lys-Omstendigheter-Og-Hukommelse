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
    base = f'/api/participants/{participant_id}'
    state = c.get(base + '/next').json()
    assert (state['condition'],state['phase'],state['round_index']) == ('WARM','setup',0)
    assert 'pairs' not in state
    assert 'words' in state and state['words'] == []
    started = c.post(base + '/rounds/start').json()
    assert started['phase'] == 'learning'
    assert len(started['pairs']) == 10
    assert 'words' in started and started['words'] == []
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
    for round_index in range(3):
        base = f'/api/participants/{pid}'
        started = c.post(base + '/rounds/start').json()
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
    base = f'/api/participants/{pid}'
    c.post(base + '/rounds/start')
    clock['now'] += 92
    assert c.post(base + '/rounds/0/submit', json={'answers':['']*10}).status_code == 200
    assert c.delete(base).status_code == 204
    assert c.get(base + '/next').status_code == 404
    with database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM study_results').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM study_participants').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM study_rounds').fetchone()[0] == 0
