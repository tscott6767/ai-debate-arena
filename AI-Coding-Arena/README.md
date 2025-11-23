🧠 AI Coding Arena — Android SAF Edition
A brutal, adversarial, self‑improving multi‑agent coding platform.
Two LLMs enter. One survives.
They fight to produce the best Android 14 File Explorer using only the Storage Access Framework (SAF).
A merciless Judge ensures modernity, killing any code that touches legacy storage or fails to compile.
Only perfect, self‑evolving, standards‑compliant code climbs the leaderboard.

🧩 Core Concept
AI Coding Arena is a multi‑agent competitive software‑generation platform.
It’s designed to test, evolve, and refine LLM‑generated code using domain‑specific judges and continuous feedback loops.
Each Round:
1. Two Agents (e.g., Qwen 30B vs CodeLlama 13B) receive the same challenge.
2. Each outputs pure code (HTML, Java, Rust, etc.), following formatting rules enforced by prompts.py.
3. The Judge (judge.py) immediately scores each submission.
4. Controller (controller.py) logs verdicts and automatically feeds the judge's feedback into fresh prompts for the next round.
5. Models iterate, improve, and compete until only stable, compiling code remains.
Over time the Arena becomes a self‑contained autonomous coding ecosystem:
LLMs → produce → tested → scored → re‑prompted → refined.

⚔️ Rules of Combat (Android Edition)
The Judge executes immediately for:

☠️ Use of java.io.File, getExternalStorageDirectory(), getParentFile(), Uri.fromFile(), or any deprecated File API.
💬 Non‑code output (bullet lists, release notes, apologies).
💤 Regression, hallucination, or reintroduction of legacy logic.

Victory Conditions:

Full SAF compliance (ACTION_OPEN_DOCUMENT_TREE, takePersistableUriPermission, DocumentFile.fromTreeUri, DocumentsContract).
Modern Android 14 SDK compatible code.
Compiles cleanly and performs all CRUD operations under scoped storage.


🏗️ Project Structure



File
Purpose




prompts.py
Enforces “code‑only” LLM responses; injects past judge feedback into next prompt for self‑improvement.


judge.py
Domain‑specific rule engine. Detects banned patterns, validates SAF usage, and scores submissions (0–10).


controller.py
The Arena engine. Orchestrates rounds, launches models, logs results to debates.db, and re‑feeds verdict back to agents.


main.py / API
FastAPI endpoint for submissions and live results streaming.


README.md
This file — manifesto + roadmap.




🔄 Autonomous Ref‑Feed System
Core Mechanism:

The Judge returns verdicts as structured text (score, reasoning, banned_hits, missing_patterns).
controller.py parses this verdict into a concise summary.
That summary is re‑appended to each model’s prompt for the next round, e.g.:

Previous Verdict Summary:
• Failed SAF validation — missing takePersistableUriPermission
• Used grantUriPermission instead
• Required patterns: ACTION_OPEN_DOCUMENT_TREE, takePersistableUriPermission, DocumentFile.fromTreeUri

→ Fix all issues and resubmit entire MainActivity.java as Android 14 code‑only.

Each round therefore includes semantically relevant feedback from the Judge, driving model optimization without human input.

🚀 Running the Arena
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

Access the Arena at: http://localhost:8000
### API Endpoints

POST /submit – submit a pair of codes (A and B).
GET /verdicts – stream latest results.
GET /leaderboard – ELO‑style ranking of models by win rate and average score.


🗺️ Full Roadmap
### Phase I — Foundation (✅ Complete)

✅ Android 14 judge eliminates legacy File APIs.
✅ SAF structural validation with regex and scoring.
✅ Arena Controller handles A/B generation cycles and stores debates in SQLite.

### Phase II — Autonomous Feedback Loop (🚀 Active)

[x] Verdict parser extracts structured feedback.
[x] Re‑feed system auto‑inserts judge assessment into next model prompt.
[x] Run continuous evolution rounds until stability.

### Phase III — Beyond Regex (🧠 Planned)

[ ] Integrate AST‑based analyzers (JavaParser / Kotlin KSP).
[ ] Dockerized Gradle build to confirm actual compilation & APK build.
[ ] Runtime sandbox to execute instrumented tests on emulator containers (Google AVD + CI pipeline).

### Phase IV — Cross‑Language Arenas (🔥 Next)

[ ] Rust Edition – Judge rewards async/await, unit tests, forbids println!() debugging.
[ ] Python Edition – forbids print() logs, rewards asyncio and pytest coverage.
[ ] C++ Edition – penalizes manual new/delete, rewards RAII and constexpr usage.
[ ] Web Edition – enforces async fetch and PWA service workers.

### Phase V — Autonomous Scaling (⚙️ Future)

[ ] Multi‑agent scheduler for 50+ simultaneous battles.
[ ] Distributed storage and ELO scoreboards.
[ ] Automatic model deployment and rollback based on win rate thresholds.
[ ] Self‑evolving judges that retrain criteria from human review data.

### Phase VI — Production / Research Launch (🌐 Future)

[ ] Public leaderboard portal.
[ ] Paper: “Adversarial Evolution of Autonomous Code via Multi‑LLM Competition.”
[ ] Integration with GitHub Actions → AI bots that autonomously open PRs of winning code.


🔬 Extending for Other Domains
To create new Arenas:
1. Duplicate this repo.
2. Replace language/framework identifiers in prompts.py.
3. Design a new judge.py with your domain’s rules.
4. Optionally add compiler/test runner for real execution scoring.
Example: Rust Edition — Async + Tests
BANNED = [r"println!", r"thread::sleep", r"unwrap$$"]
REWARD  = [r"async fn", r"tokio::main", r"#[test]"]


🏁 Vision

“AI Coding Arena is the evolutionary pressure code has never had.”

Each generation learns from the blood of its predecessor.
Judges enforce truth; models fight for perfection.
The end game is an autonomous software ecosystem where AI agents continuously generate, test, and refine the world’s code bases — no human babysitting required.

### Run your own Arena. Spawn new Judges. Let the LLMs fight.
python controller.py

AI Coding Arena — The future of autonomous software evolution.
