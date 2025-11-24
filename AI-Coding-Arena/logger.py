# logger.py
"""
logger.py – Thin SQLite wrapper for storing debate transcripts locally.
"""

import sqlite3
from contextlib import closing
import os

# Allow override through environment variable
#DB_PATH = os.getenv("DEBATE_DB_PATH", "debates.db")
DB_PATH = os.getenv("DEBATE_DB_PATH") or os.path.join(os.path.dirname(__file__), "static/debates.db")
# ─── Initialize database table if needed ────────────────────────────────────
with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS debates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            session TEXT,
            topic TEXT,
            transcript TEXT
        );
        """
    )
    conn.commit()


# ─── Function to log a debate ───────────────────────────────────────────────
def log_debate(session: str, topic: str, transcript: str):
    """Append a debate transcript to the local SQLite database."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO debates (session, topic, transcript) VALUES (?, ?, ?)",
            (session, topic, transcript),
        )
        conn.commit()

