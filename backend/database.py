"""SQLite persistence. Existing legacy tables from the reading experiment are untouched."""
from __future__ import annotations
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from itertools import permutations

DB_PATH = Path(os.environ.get("STUDY_DATABASE", str(Path(__file__).with_name("results.db"))))
CONDITIONS = ("WARM", "COOL", "DARK")
SEQUENCES = (
    ("WARM", "COOL", "DARK"),
    ("COOL", "DARK", "WARM"),
    ("DARK", "WARM", "COOL"),
)
LIST_ORDERS = tuple(permutations((0, 1, 2)))
LEARN_SECONDS = 60
DISTRACT_SECONDS = 30
RECALL_SECONDS = 120
ACCLIMATION_SECONDS = 15


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS study_participants (
                id TEXT PRIMARY KEY,
                language TEXT NOT NULL CHECK(language IN ('nb','en')),
                age_band TEXT NOT NULL,
                gender TEXT NOT NULL,
                group_name TEXT NOT NULL CHECK(group_name IN ('A','B','C')),
                list_order TEXT NOT NULL,
                consented_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS study_rounds (
                participant_id TEXT NOT NULL,
                round_index INTEGER NOT NULL CHECK(round_index BETWEEN 0 AND 2),
                started_at REAL NOT NULL,
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
                completed_at TEXT NOT NULL,
                PRIMARY KEY (participant_id, round_index),
                FOREIGN KEY(participant_id) REFERENCES study_participants(id)
            );
            CREATE INDEX IF NOT EXISTS idx_study_results_condition
              ON study_results(condition);
        """)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_participant(language: str, age_band: str, gender: str) -> dict:
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        counts = {group: db.execute(
            "SELECT COUNT(*) FROM study_participants WHERE group_name=?", (group,)
        ).fetchone()[0] for group in "ABC"}
        group = min("ABC", key=lambda group_: counts[group_])
        # Balance all 6 word-list orders within each light-sequence group.
        order = LIST_ORDERS[counts[group] % len(LIST_ORDERS)]
        participant_id = str(uuid.uuid4())
        db.execute("""INSERT INTO study_participants
          (id, language, age_band, gender, group_name, list_order, consented_at, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
          (participant_id, language, age_band, gender, group, json.dumps(order), now_iso(), now_iso()))
    return {"participant_id": participant_id, "group": group}


def get_next(participant_id: str) -> dict | None:
    with connect() as db:
        participant = db.execute("SELECT * FROM study_participants WHERE id=?", (participant_id,)).fetchone()
        if participant is None:
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
            return common
        condition = SEQUENCES["ABC".index(participant["group_name"])][idx]
        list_id = json.loads(participant["list_order"])[idx]
        started = db.execute("SELECT started_at FROM study_rounds WHERE participant_id=? AND round_index=?",
                             (participant_id, idx)).fetchone()
        if not started:
            return {**common, "round_index": idx, "condition": condition,
                    "list_id": list_id, "phase": "setup", "phase_end_at": None}
        elapsed = common["server_now"] - started["started_at"]
        if elapsed < LEARN_SECONDS:
            phase, phase_end = "learning", started["started_at"] + LEARN_SECONDS
        elif elapsed < LEARN_SECONDS + DISTRACT_SECONDS:
            phase, phase_end = "distraction", started["started_at"] + LEARN_SECONDS + DISTRACT_SECONDS
        else:
            phase, phase_end = "recall", started["started_at"] + LEARN_SECONDS + DISTRACT_SECONDS + RECALL_SECONDS
        return {**common, "round_index": idx, "condition": condition,
                "list_id": list_id, "phase": phase, "phase_end_at": phase_end}


def start_round(participant_id: str) -> dict | None:
    # Inserting with a unique constraint makes repeat clicks idempotent.
    state = get_next(participant_id)
    if state is None or state["finished"]:
        return state
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO study_rounds(participant_id,round_index,started_at) VALUES (?,?,?)",
                   (participant_id, state["round_index"], time.time()))
    return get_next(participant_id)


def save_result(participant_id: str, round_index: int, answers: list[str],
                hidden_count: int, score: int) -> dict:
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        participant = db.execute("SELECT * FROM study_participants WHERE id=?", (participant_id,)).fetchone()
        if not participant:
            raise ValueError("participant")
        existing = db.execute("SELECT 1 FROM study_results WHERE participant_id=? AND round_index=?",
                              (participant_id, round_index)).fetchone()
        if existing:
            raise ValueError("duplicate")
        completed = db.execute("SELECT count(*) FROM study_results WHERE participant_id=?", (participant_id,)).fetchone()[0]
        if completed != round_index:
            raise ValueError("order")
        started = db.execute("SELECT started_at FROM study_rounds WHERE participant_id=? AND round_index=?",
                             (participant_id, round_index)).fetchone()
        if not started:
            raise ValueError("not_started")
        elapsed = time.time() - started["started_at"]
        if elapsed < LEARN_SECONDS + DISTRACT_SECONDS:
            raise ValueError("too_early")
        condition = SEQUENCES["ABC".index(participant["group_name"])][round_index]
        list_id = json.loads(participant["list_order"])[round_index]
        recall_seconds = max(0, elapsed - LEARN_SECONDS - DISTRACT_SECONDS)
        late = int(recall_seconds > RECALL_SECONDS + 5)
        db.execute("""INSERT INTO study_results
          (participant_id,round_index,condition,list_id,answers,score,max_score,recall_seconds,hidden_count,submitted_late,completed_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
          (participant_id, round_index, condition, list_id, json.dumps(answers, ensure_ascii=False),
           score, 10, recall_seconds, hidden_count, late, now_iso()))
    return {"score": score, "max_score": 10, "submitted_late": bool(late)}


def export_rows() -> list[dict]:
    with connect() as db:
        rows = db.execute("""SELECT p.id AS participant_id,p.language,p.age_band,p.gender,
          p.group_name,p.list_order,p.created_at,r.round_index,r.condition,r.list_id,
          r.answers,r.score,r.max_score,r.recall_seconds,r.hidden_count,
          r.submitted_late,r.completed_at
          FROM study_results r JOIN study_participants p ON p.id=r.participant_id
          ORDER BY p.created_at,r.round_index""").fetchall()
        return [dict(row) for row in rows]


def delete_participant(participant_id: str) -> bool:
    """Withdraw consent and delete all new-study data linked to this participant ID."""
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT id FROM study_participants WHERE id=?", (participant_id,)).fetchone()
        if not row:
            return False
        db.execute("DELETE FROM study_results WHERE participant_id=?", (participant_id,))
        db.execute("DELETE FROM study_rounds WHERE participant_id=?", (participant_id,))
        db.execute("DELETE FROM study_participants WHERE id=?", (participant_id,))
    return True
