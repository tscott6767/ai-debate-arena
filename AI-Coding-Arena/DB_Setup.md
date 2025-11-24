# 🗄 AI Debate Arena Database Setup

This document explains how the AI Debate Arena stores debate transcripts, how to inspect
or back up the `debates.db` SQLite database, and how the application reads previous
sessions to generate continuation prompts.

🗂 Database Setup – debates.db
The application automatically logs every debate session (topic + transcript + judge decision) into a local SQLite database file called debates.db.
This happens transparently inside logger.log_debate() after each successful run.
No manual configuration is required — the file is created on first run in your project directory.

📌 Default location
<project_root>/debates.db

(Depending on your version, it may appear under static/debates.db if you mounted the database path there.)
You can verify its exact location inside logger.py:
DB_PATH = os.path.join(os.path.dirname(__file__), "debates.db")


🧱 Database schema
The log_debate() function initializes a single table named debates:
CREATE TABLE IF NOT EXISTS debates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    session_id TEXT NOT NULL,
    topic TEXT,
    transcript TEXT
);

Each row represents one complete debate run:
- timestamp – time it was recorded
- session_id – short UUID identifier
- topic – the full prompt passed to the models
- transcript – the entire multi‑round dialogue including the judge’s verdict

🧰 Inspecting the database manually
sqlite3 debates.db

Inside the SQLite prompt you can use, for example:
-- List latest debates
SELECT id, timestamp, substr(topic,1,80) AS topic_snippet
FROM debates
ORDER BY id DESC
LIMIT 5;

-- Read a full transcript by ID
SELECT transcript FROM debates WHERE id = 5;
.exit


🧾 Backup & cleanup
To back up or archive debate logs:
cp debates.db backups/debates_$(date +%F).db

To clear all records (start fresh):
sqlite3 debates.db "DELETE FROM debates;"

(Be careful — this cannot be undone.)

🚀 Summary



Item
Default
Purpose




File
debates.db
Stores all debates persistence


Engine
SQLite 3
Lightweight + file‑based


Table
debates
One row per session


Created by
logger.log_debate()
Auto‑runs after every debate



No environment variables or external SQL server are required — the app is plug‑and‑play.

Add this block near your “Usage” or “Architecture” section in README.md, and your project becomes self‑documenting about the SQLite setup.You can drop this straight into your README.md after the installation or usage section:

🗄 Debate Database (debates.db)
Every time a debate finishes, AI Debate Arena automatically logs the full transcript – including the topic, all rounds, and the final judge verdict – into a lightweight SQLite database called debates.db.
You do not need to configure anything; the file is created on first run.
📍 Default location
<project_root>/debates.db

(If you mounted a static directory, it may appear under static/debates.db.)
🧱 Schema
The database contains a single table:
CREATE TABLE IF NOT EXISTS debates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    topic       TEXT,
    transcript  TEXT
);

Each row represents one debate session.



Column
Description




id
Auto‑incremented row ID


timestamp
When the debate ended


session_id
Short unique identifier


topic
Full prompt provided to the models


transcript
Complete dialogue and judge verdict



🧰 Inspecting and managing data
Open the file with the built‑in sqlite3 CLI:
sqlite3 debates.db

Common commands:
-- Show latest five debates
SELECT id, timestamp, substr(topic,1,80) AS snippet
FROM debates ORDER BY id DESC LIMIT 5;

-- Read a full transcript by ID
SELECT transcript FROM debates WHERE id = 5;

-- Remove all old logs (irreversible!)
DELETE FROM debates;
.exit

💾 Backup or archive
cp debates.db backups/debates_$(date +%F).db

⚙️ How it’s used internally
The function logger.log_debate() handles all writes.
On every run it:
1. Creates the table if it doesn’t exist.
2. Inserts (timestamp, session_id, topic, transcript) after the final round.
3. Allows /api/continuation to read the latest entry for the next round.
No additional environment variables or credentials are required — the app is completely self‑contained.

