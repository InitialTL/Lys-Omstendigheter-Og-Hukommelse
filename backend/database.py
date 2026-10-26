import sqlite3
from pathlib import Path
import json
import uuid

DATABASE = Path(__file__).resolve().parent / "results.db"

LIGHTING = {
    "A": ["OFF", "3000K", "10000K"],
    "B": ["3000K", "10000K", "OFF"],
    "C": ["10000K", "OFF", "3000K"]
}

def connect():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                text_id INTEGER NOT NULL,
                lighting TEXT NOT NULL,
                answers TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                UNIQUE(participant_id, text_id),
                FOREIGN KEY(participant_id)
                    REFERENCES participants(id)
            )
        """)

def create_participant():
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        
        counts = {
            group: conn.execute(
                "SELECT COUNT (*) FROM participants WHERE group_name = ?",
                (group,)
            ).fetchone()[0] for group in LIGHTING
        }
        group = min(counts, key=counts.get)
        participant_id = str(uuid.uuid4())
        
        conn.execute(
            "INSERT INTO participants (id, group_name) VALUES (?, ?)",
            (participant_id, group)
        )
    return {
        "participant_id": participant_id,
        "group": group
    }

def get_participant(participant_id):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM participants WHERE id = ?",
            (participant_id,)
        ).fetchone()
        
        return dict(row) if row else None

def get_next_test(participant_id):
    participant = get_participant(participant_id)
    
    if participant is None:
        return None

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT text_id
            FROM experiment_results
            WHERE participant_id = ?
            """,
            (participant_id,)
        ).fetchall()
    
    completed = {row["text_id"] for row in rows}
    next_text = next(
        (i for i in range(3) if not i in completed),
        None
    )
    
    return {
        "group": participant["group_name"],
        "finished": next_text is None,
        "text_id": next_text,
        "lighting": (
            LIGHTING[participant["group_name"]][next_text]
            if next_text is not None
            else None
        )
    }

def save_result(participant_id, text_id, answers, score, max_score):
    with connect() as conn:
        conn.execute(
            """
                INSERT INTO experiment_results
                (participant_id, text_id, lighting, answers, score, max_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                participant_id,
                text_id,
                LIGHTING[get_participant(participant_id)["group_name"]][text_id],
                json.dumps(answers),
                score,
                max_score
            ))
