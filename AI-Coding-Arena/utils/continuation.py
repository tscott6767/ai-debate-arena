# utils/continuation.py
"""
continuation.py – load previous debate transcripts from debates.db
and build a continuation topic for the next AI Debate Arena round.
"""

import sqlite3
import os
from logger import DB_PATH  # uses your existing logger.py database path


def get_last_debate(limit: int = 1):
    """
    Returns the latest debate(s) from debates.db.

    Parameters:
        limit (int): number of recent rows to fetch

    Returns:
        tuple or list:
            Each tuple => (id, ts, session, topic, transcript)
    """
    if not os.path.exists(DB_PATH):
        print("⚠️ debates.db not found at", DB_PATH)
        return None

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, ts, session, topic, transcript
            FROM debates
            ORDER BY id DESC
            LIMIT ?;
            """,
            (limit,),
        ).fetchall()

    # Return a single record if limit == 1
    return rows if limit > 1 else (rows[0] if rows else None)


def build_continuation_prompt(past_transcript: str, new_task: str, round_no: int) -> str:
    """
    Wraps the previous debate transcript and new assignment text
    into one combined prompt for the next round.

    Example:
        topic = build_continuation_prompt(last_text,
                  "Expand last SAF code to full ACTION_OPEN_DOCUMENT_TREE.",
                  13)
    """
    return f"""
Round {round_no} — Continuation of Round {round_no - 1}

Context:
Below is the transcript and code from the previous round.
────────────────────────────
{past_transcript}
────────────────────────────

Task:
{new_task}

Rules:
• Do not restart from scratch — build upon the existing implementation.
• Use modern Android APIs (ActivityResultLauncher / DocumentFile).
• Explain your changes clearly for the judge.
"""
