import sqlite3
from pathlib import Path
import json

DATABASE = Path(__file__).resolve().parent / "results.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_id INTEGER NOT NULL,
                answers TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL
            )
        """)

def save_result(text_id, answers, score, max_score):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
                     INSERT INTO results (text_id, answers, score, max_score)
                     VALUES (?, ?, ?, ?)
                """, (
                    text_id,
                    json.dumps(answers),
                    score,
                    max_score
                ))
