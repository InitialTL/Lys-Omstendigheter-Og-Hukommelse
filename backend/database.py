"""SQLite persistence. Existing legacy tables from the reading experiment are untouched."""
from __future__ import annotations
import json
import hashlib
import secrets
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from itertools import permutations

DB_PATH = Path(os.environ.get("STUDY_DATABASE", str(Path(__file__).with_name("results.db"))))
PROTOCOL_VERSION = "2.6"
WORDS_PER_ROUND = 8
LANGUAGES = ("nb", "en", "sv", "de", "fr", "es", "it", "pt", "nl", "da", "pl", "ro")
CONDITIONS = ("ORANGE", "BLUE", "NEUTRAL")
SEQUENCES = (
    ("ORANGE", "BLUE", "NEUTRAL"),
    ("BLUE", "NEUTRAL", "ORANGE"),
    ("NEUTRAL", "ORANGE", "BLUE"),
)
LIST_ORDERS = tuple(permutations((0, 1, 2)))
LEARN_SECONDS = 75
DISTRACT_SECONDS = 30
RECALL_SECONDS = 120
ACCLIMATION_SECONDS = 60


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=15000")
    connection.execute("PRAGMA cache_size=-2048")  # Limit per-connection cache to about 2 MiB.
    connection.execute("PRAGMA wal_autocheckpoint=100")
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        # WAL permits a reader to run while results are inserted. One worker is
        # sufficient on a Pi 3; checkpoints bound the write-ahead log size.
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS study_participants (
                id TEXT PRIMARY KEY,
                language TEXT NOT NULL CHECK(language IN ('nb','en','sv','de','fr','es','it','pt','nl','da','pl','ro')),
                age_band TEXT NOT NULL,
                gender TEXT NOT NULL,
                group_name TEXT NOT NULL CHECK(group_name IN ('A','B','C')),
                list_order TEXT NOT NULL,
                consented_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                protocol_version TEXT NOT NULL DEFAULT '2.6',
                token_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS study_rounds (
                participant_id TEXT NOT NULL,
                round_index INTEGER NOT NULL CHECK(round_index BETWEEN 0 AND 2),
                started_at REAL NOT NULL,
                learning_order TEXT,
                recall_order TEXT,
                PRIMARY KEY (participant_id, round_index),
                FOREIGN KEY(participant_id) REFERENCES study_participants(id)
            );
            CREATE TABLE IF NOT EXISTS study_results (
                participant_id TEXT NOT NULL,
                round_index INTEGER NOT NULL CHECK(round_index BETWEEN 0 AND 2),
                condition TEXT NOT NULL,
                list_id INTEGER NOT NULL,
                answers TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                recall_seconds REAL NOT NULL,
                hidden_count INTEGER NOT NULL DEFAULT 0,
                submitted_late INTEGER NOT NULL DEFAULT 0,
                math_attempts INTEGER NOT NULL DEFAULT 0,
                math_correct INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (participant_id, round_index),
                FOREIGN KEY(participant_id) REFERENCES study_participants(id)
            );
            CREATE INDEX IF NOT EXISTS idx_study_results_condition
              ON study_results(condition);
            CREATE TABLE IF NOT EXISTS study_perceptions (
                participant_id TEXT PRIMARY KEY,
                perceived_difference TEXT NOT NULL CHECK(perceived_difference IN
                  ('NONE','SMALL','MODERATE','LARGE','UNSURE','SKIPPED')),
                perceived_easiest TEXT NOT NULL CHECK(perceived_easiest IN
                  ('ORANGE','BLUE','NEUTRAL','SAME','UNSURE','SKIPPED')),
                completed_at TEXT NOT NULL,
                FOREIGN KEY(participant_id) REFERENCES study_participants(id)
            );
        """)
    # Migrate old pilot schemas without modifying or deleting old results.
    # Only V2.6 participants are accepted by public study endpoints.
    with connect() as db:
        existing = {r[1] for r in db.execute('PRAGMA table_info(study_participants)')}
        schema = db.execute("SELECT sql FROM sqlite_master WHERE name='study_participants'").fetchone()[0]
    if "'ro'" not in schema or 'protocol_version' not in existing or 'token_hash' not in existing:
        with sqlite3.connect(DB_PATH, timeout=15) as db:
            db.execute('PRAGMA foreign_keys=OFF')
            db.execute('BEGIN IMMEDIATE')
            db.execute('''CREATE TABLE study_participants_new_v23 (
                id TEXT PRIMARY KEY,
                language TEXT NOT NULL CHECK(language IN ('nb','en','sv','de','fr','es','it','pt','nl','da','pl','ro')),
                age_band TEXT NOT NULL,
                gender TEXT NOT NULL,
                group_name TEXT NOT NULL CHECK(group_name IN ('A','B','C')),
                list_order TEXT NOT NULL,
                consented_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                protocol_version TEXT NOT NULL DEFAULT '2.6',
                token_hash TEXT
            )''')
            protocol_expr = 'protocol_version' if 'protocol_version' in existing else "'2.0'"
            token_expr = 'token_hash' if 'token_hash' in existing else 'NULL'
            db.execute(f'''INSERT INTO study_participants_new_v23
                 SELECT id,language,age_band,gender,group_name,list_order,consented_at,created_at,
                        {protocol_expr},{token_expr} FROM study_participants''')
            db.execute('DROP TABLE study_participants')
            db.execute('ALTER TABLE study_participants_new_v23 RENAME TO study_participants')
            assert db.execute('PRAGMA foreign_key_check').fetchall() == []

    with connect() as db:
        rounds_cols = {r[1] for r in db.execute('PRAGMA table_info(study_rounds)')}
        for name in ('learning_order','recall_order'):
            if name not in rounds_cols:
                db.execute(f'ALTER TABLE study_rounds ADD COLUMN {name} TEXT')
        results_cols = {r[1] for r in db.execute('PRAGMA table_info(study_results)')}
        for name in ('math_attempts','math_correct'):
            if name not in results_cols:
                db.execute(f'ALTER TABLE study_results ADD COLUMN {name} INTEGER NOT NULL DEFAULT 0')


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_participant(language: str, age_band: str, gender: str) -> dict:
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        counts = {group: db.execute(
            "SELECT COUNT(*) FROM study_participants WHERE group_name=? AND protocol_version=?", (group, PROTOCOL_VERSION)
        ).fetchone()[0] for group in "ABC"}
        group = min("ABC", key=lambda group_: counts[group_])
        # Balance all 6 word-list orders within each light-sequence group.
        order = LIST_ORDERS[counts[group] % len(LIST_ORDERS)]
        participant_id = str(uuid.uuid4())
        access_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        db.execute("""INSERT INTO study_participants
          (id, language, age_band, gender, group_name, list_order, consented_at, created_at, protocol_version, token_hash)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (participant_id, language, age_band, gender, group, json.dumps(order), now_iso(), now_iso(), PROTOCOL_VERSION, token_hash))
    return {"participant_id": participant_id, "group": group, "access_token": access_token}


def verify_token(participant_id: str, access_token: str | None) -> bool:
    """Separate 256-bit bearer secret; participant UUID alone is not authentication."""
    if not access_token or len(access_token) > 128:
        return False
    with connect() as db:
        participant = db.execute("SELECT token_hash, protocol_version FROM study_participants WHERE id=?",
                                 (participant_id,)).fetchone()
    if not participant or participant["protocol_version"] != PROTOCOL_VERSION or not participant["token_hash"]:
        return False
    provided = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
    return secrets.compare_digest(provided, participant["token_hash"])


def get_next(participant_id: str) -> dict | None:
    with connect() as db:
        participant = db.execute("SELECT * FROM study_participants WHERE id=?", (participant_id,)).fetchone()
        if participant is None or participant["protocol_version"] != PROTOCOL_VERSION:
            return None
        completed = db.execute("SELECT round_index FROM study_results WHERE participant_id=?",
                               (participant_id,)).fetchall()
        completed_indices = {row["round_index"] for row in completed}
        idx = next((index for index in range(3) if index not in completed_indices), None)
        common = {
            "participant_id": participant_id,
            "group": participant["group_name"],
            "language": participant["language"],
            "completed": len(completed_indices),
            "total": 3,
            "finished": idx is None,
            "server_now": time.time(),
        }
        if idx is None:
            common["perception_done"] = db.execute(
                "SELECT 1 FROM study_perceptions WHERE participant_id=?", (participant_id,)
            ).fetchone() is not None
            return common
        condition = SEQUENCES["ABC".index(participant["group_name"])][idx]
        list_id = json.loads(participant["list_order"])[idx]
        started = db.execute("SELECT started_at,learning_order,recall_order FROM study_rounds WHERE participant_id=? AND round_index=?",
                             (participant_id, idx)).fetchone()
        if not started:
            return {**common, "round_index": idx, "condition": condition,
                    "list_id": list_id, "phase": "setup", "phase_end_at": None}
        elapsed = common["server_now"] - started["started_at"]
        if elapsed < ACCLIMATION_SECONDS:
            phase, phase_end = "acclimation", started["started_at"] + ACCLIMATION_SECONDS
        elif elapsed < ACCLIMATION_SECONDS + LEARN_SECONDS:
            phase, phase_end = "learning", started["started_at"] + ACCLIMATION_SECONDS + LEARN_SECONDS
        elif elapsed < ACCLIMATION_SECONDS + LEARN_SECONDS + DISTRACT_SECONDS:
            phase, phase_end = "distraction", started["started_at"] + ACCLIMATION_SECONDS + LEARN_SECONDS + DISTRACT_SECONDS
        else:
            phase, phase_end = "recall", started["started_at"] + ACCLIMATION_SECONDS + LEARN_SECONDS + DISTRACT_SECONDS + RECALL_SECONDS
        return {**common, "round_index": idx, "condition": condition,
                "list_id": list_id, "phase": phase, "phase_end_at": phase_end,
                "learning_order": json.loads(started["learning_order"]),
                "recall_order": json.loads(started["recall_order"])}


def start_round(participant_id: str) -> dict | None:
    # Inserting with a unique constraint makes repeat clicks idempotent.
    state = get_next(participant_id)
    if state is None or state["finished"]:
        return state
    learning_order = list(range(WORDS_PER_ROUND))
    recall_order = list(range(WORDS_PER_ROUND))
    secure_random = secrets.SystemRandom()
    secure_random.shuffle(learning_order)
    # The test never presents words in the same screen positions as learning.
    for _ in range(200):
        secure_random.shuffle(recall_order)
        if all(a != b for a,b in zip(learning_order,recall_order)):
            break
    else:
        raise RuntimeError('Unable to create shuffled recall order')
    with connect() as db:
        db.execute('''INSERT OR IGNORE INTO study_rounds
            (participant_id,round_index,started_at,learning_order,recall_order)
            VALUES (?,?,?,?,?)''',
            (participant_id, state["round_index"], time.time(),
             json.dumps(learning_order), json.dumps(recall_order)))
    return get_next(participant_id)


def save_result(participant_id: str, round_index: int, answers: list[str],
                hidden_count: int, score: int, math_attempts: int = 0, math_correct: int = 0) -> dict:
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        participant = db.execute("SELECT * FROM study_participants WHERE id=?", (participant_id,)).fetchone()
        if not participant or participant["protocol_version"] != PROTOCOL_VERSION:
            raise ValueError("participant")
        existing = db.execute("SELECT 1 FROM study_results WHERE participant_id=? AND round_index=?",
                              (participant_id, round_index)).fetchone()
        if existing:
            raise ValueError("duplicate")
        completed = db.execute("SELECT count(*) FROM study_results WHERE participant_id=?", (participant_id,)).fetchone()[0]
        if completed != round_index:
            raise ValueError("order")
        started = db.execute("SELECT started_at,learning_order,recall_order FROM study_rounds WHERE participant_id=? AND round_index=?",
                             (participant_id, round_index)).fetchone()
        if not started:
            raise ValueError("not_started")
        elapsed = time.time() - started["started_at"]
        if elapsed < ACCLIMATION_SECONDS + LEARN_SECONDS + DISTRACT_SECONDS:
            raise ValueError("too_early")
        condition = SEQUENCES["ABC".index(participant["group_name"])][round_index]
        list_id = json.loads(participant["list_order"])[round_index]
        recall_seconds = max(0, elapsed - ACCLIMATION_SECONDS - LEARN_SECONDS - DISTRACT_SECONDS)
        late = int(recall_seconds > RECALL_SECONDS + 5)
        db.execute("""INSERT INTO study_results
          (participant_id,round_index,condition,list_id,answers,score,max_score,recall_seconds,hidden_count,submitted_late,math_attempts,math_correct,completed_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (participant_id, round_index, condition, list_id, json.dumps(answers, ensure_ascii=False),
           score, WORDS_PER_ROUND, recall_seconds, hidden_count, late, math_attempts, math_correct, now_iso()))
    return {"saved": True}


def export_rows() -> list[dict]:
    with connect() as db:
        rows = db.execute("""SELECT p.id AS participant_id,p.language,p.age_band,p.gender,
          p.protocol_version,p.group_name,p.list_order,p.created_at,r.round_index,r.condition,r.list_id,
          r.answers,r.score,r.max_score,r.recall_seconds,r.hidden_count,
          r.submitted_late,r.math_attempts,r.math_correct,r.completed_at
          FROM study_results r JOIN study_participants p ON p.id=r.participant_id
          ORDER BY p.created_at,r.round_index""").fetchall()
        return [dict(row) for row in rows]


def completed_rounds(participant_id: str) -> list[dict] | None:
    '''Return raw results only for a fully finished V2.5 session.

    The API layer adds translations and grades after this gate, so the
    correct answers are never available while another round remains.
    '''
    with connect() as db:
        protocol = db.execute('SELECT protocol_version FROM study_participants WHERE id=?',
                              (participant_id,)).fetchone()
        if not protocol or protocol['protocol_version'] != PROTOCOL_VERSION:
            return None
        data = db.execute('''SELECT r.*,p.group_name,p.list_order,p.language,
                     q.recall_order FROM study_results r
                     JOIN study_participants p ON p.id=r.participant_id
                     JOIN study_rounds q ON q.participant_id=r.participant_id
                       AND q.round_index=r.round_index
                     WHERE r.participant_id=? ORDER BY r.round_index''',
                     (participant_id,)).fetchall()
        if len(data) != 3 or [x['round_index'] for x in data] != [0,1,2]:
            return None
        return [dict(x) for x in data]


def save_perception(participant_id: str, difference: str, easiest: str) -> bool:
    """Post-study belief, independent of objective accuracy and collected once."""
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        participant = db.execute(
            "SELECT protocol_version FROM study_participants WHERE id=?", (participant_id,)
        ).fetchone()
        if not participant or participant["protocol_version"] != PROTOCOL_VERSION:
            raise ValueError("participant")
        completed = db.execute(
            "SELECT COUNT(*) FROM study_results WHERE participant_id=?", (participant_id,)
        ).fetchone()[0]
        if completed != 3:
            raise ValueError("study_not_complete")
        if db.execute(
            "SELECT 1 FROM study_perceptions WHERE participant_id=?", (participant_id,)
        ).fetchone():
            raise ValueError("already_submitted")
        db.execute("INSERT INTO study_perceptions "
          "(participant_id,perceived_difference,perceived_easiest,completed_at) "
          "VALUES (?,?,?,?)", (participant_id, difference, easiest, now_iso()))
    return True


def export_perceptions() -> list[dict]:
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT v.participant_id,p.protocol_version,p.language,p.group_name, "
          "v.perceived_difference,v.perceived_easiest,v.completed_at "
          "FROM study_perceptions v JOIN study_participants p ON p.id=v.participant_id "
          "ORDER BY v.completed_at").fetchall()]


def delete_participant(participant_id: str) -> bool:
    """Withdraw consent and delete all new-study data linked to this participant ID."""
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT id FROM study_participants WHERE id=?", (participant_id,)).fetchone()
        if not row:
            return False
        db.execute("DELETE FROM study_perceptions WHERE participant_id=?", (participant_id,))
        db.execute("DELETE FROM study_results WHERE participant_id=?", (participant_id,))
        db.execute("DELETE FROM study_rounds WHERE participant_id=?", (participant_id,))
        db.execute("DELETE FROM study_participants WHERE id=?", (participant_id,))
    return True
